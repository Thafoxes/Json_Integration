#!/usr/bin/env python3
"""
Genshin Impact Translation Pipeline
Comprehensive automated translation system with glossary enforcement and progress tracking.
"""

import json
import re
import os
import sys
import time
import argparse
import logging
import hashlib
import sqlite3
import yaml
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from collections import defaultdict
import shutil

# Try to import translation libraries
try:
    from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

try:
    from deepl_translator import DeepLTranslator
    HAS_DEEPL = True
except ImportError:
    HAS_DEEPL = False

class GenshinTranslator:
    def __init__(self, config_path: str = "config/translator.yaml"):
        """Initialize the translator with configuration."""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.load_glossary()
        self.init_database()
        self.translation_engine = None
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_changed': 0,
            'translations_made': 0,
            'glossary_applications': 0,
            'errors': 0
        }
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self.get_default_config()
    
    def get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config file is missing."""
        return {
            'provider': 'offline',
            'processing': {
                'chinese_detection_regex': r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]'
            },
            'performance': {
                'worker_pool_size': 1,
                'checkpoint_frequency': 100
            },
            'logging': {
                'level': 'INFO'
            }
        }
    
    def setup_logging(self):
        """Set up logging configuration."""
        log_level = getattr(logging, self.config.get('logging', {}).get('level', 'INFO'))
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(f'logs/translator_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_glossary(self):
        """Load the glossary for translation enforcement."""
        try:
            with open('glossary/glossary.json', 'r', encoding='utf-8') as f:
                self.glossary = json.load(f)
            
            with open('glossary/normalized_index.json', 'r', encoding='utf-8') as f:
                self.normalized_glossary = json.load(f)
            
            # Create reverse lookup for placeholder protection
            self.zh_to_placeholder = {}
            for i, zh_term in enumerate(sorted(self.glossary.keys(), key=len, reverse=True)):
                self.zh_to_placeholder[zh_term] = f"[[TERM_{i+1}]]"
            
            self.logger.info(f"Loaded glossary with {len(self.glossary)} terms")
            
        except Exception as e:
            self.logger.error(f"Failed to load glossary: {e}")
            self.glossary = {}
            self.normalized_glossary = {}
            self.zh_to_placeholder = {}
    
    def init_database(self):
        """Initialize progress tracking database."""
        os.makedirs('progress', exist_ok=True)
        self.db_path = 'progress/progress.sqlite'
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS files (
                path TEXT PRIMARY KEY,
                checksum_before TEXT,
                checksum_after TEXT,
                status TEXT DEFAULT 'pending',
                changed INTEGER DEFAULT 0,
                last_processed_at TEXT,
                error_message TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        self.conn.commit()
        self.logger.info("Database initialized")
    
    def get_file_checksum(self, filepath: str) -> str:
        """Calculate SHA-256 checksum of a file."""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def needs_chinese_translation(self, text: str) -> bool:
        """Check if text contains Chinese characters that need translation."""
        chinese_regex = self.config.get('processing', {}).get(
            'chinese_detection_regex', 
            r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]'
        )
        return bool(re.search(chinese_regex, text))
    
    def protect_known_terms(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Replace known Chinese terms with placeholders to protect them."""
        protected_text = text
        replacements = {}
        
        for zh_term, placeholder in self.zh_to_placeholder.items():
            if zh_term in protected_text:
                protected_text = protected_text.replace(zh_term, placeholder)
                replacements[placeholder] = self.glossary[zh_term]
                self.stats['glossary_applications'] += 1
        
        return protected_text, replacements
    
    def restore_protected_terms(self, text: str, replacements: Dict[str, str]) -> str:
        """Restore placeholders with official English terms."""
        for placeholder, english_term in replacements.items():
            text = text.replace(placeholder, english_term)
        return text
    
    def translate_text(self, text: str) -> str:
        """Translate a single piece of text."""
        if not self.needs_chinese_translation(text):
            return text
        
        # Protect known terms
        protected_text, replacements = self.protect_known_terms(text)
        
        # If everything was protected, no translation needed
        if not self.needs_chinese_translation(protected_text):
            return self.restore_protected_terms(protected_text, replacements)
        
        # Initialize translation engine if not done yet
        if self.translation_engine is None:
            self.init_translation_engine()
        
        # Use translation engine
        translated = self.translate_with_engine(protected_text)
        
        # Restore protected terms
        final_text = self.restore_protected_terms(translated, replacements)
        
        self.stats['translations_made'] += 1
        return final_text
    
    def init_translation_engine(self):
        """Initialize the appropriate translation engine based on configuration."""
        provider = self.config.get('provider', 'offline')
        
        if provider == 'deepl' and HAS_DEEPL:
            api_key = os.getenv('DEEPL_API_KEY')
            if api_key:
                try:
                    self.translation_engine = DeepLTranslator(api_key, self.glossary)
                    if self.translation_engine.check_api_key():
                        self.logger.info("✅ DeepL API initialized successfully")
                        return
                    else:
                        self.logger.error("❌ DeepL API key validation failed")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize DeepL: {e}")
            else:
                self.logger.warning("⚠️ DEEPL_API_KEY not set, falling back to offline mode")
        
        # Fallback to simple translation
        self.logger.info("Using simple placeholder translation (offline mode)")
        self.translation_engine = "simple"
    
    def translate_with_engine(self, text: str) -> str:
        """Translate text using the configured translation engine."""
        if not text.strip():
            return text
        
        if isinstance(self.translation_engine, DeepLTranslator):
            # Use DeepL API
            result = self.translation_engine.translate_text(text)
            if result is not None:
                return result
            else:
                # Fallback to simple translation if API fails
                self.logger.warning(f"DeepL translation failed for: {text[:50]}...")
                return self.simple_translate(text)
        else:
            # Use simple placeholder translation
            return self.simple_translate(text)
    
    def simple_translate(self, text: str) -> str:
        """Simple translation placeholder - replace with actual MT later."""
        # This is a placeholder - in production, this would call:
        # - DeepL API
        # - Google Translate API  
        # - Or local transformer model
        
        # For now, just return original text with a marker
        if self.needs_chinese_translation(text):
            return f"[TRANSLATED: {text}]"
        return text
    
    def translate_json_file(self, filepath: str) -> bool:
        """Translate a JSON file, preserving structure."""
        try:
            # Read original file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in {filepath}: {e}")
                return False
            
            # Translate recursively
            changed = False
            translated_data = self.translate_json_recursive(data, changed)
            
            if changed:
                # Create backup
                backup_path = f"{filepath}.backup"
                shutil.copy2(filepath, backup_path)
                
                # Write translated file
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(translated_data, f, ensure_ascii=False, indent=2)
                
                # Verify the file is still valid JSON
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        json.load(f)
                    
                    # Remove backup if verification passed
                    os.remove(backup_path)
                    return True
                    
                except Exception as e:
                    # Restore from backup if verification failed
                    shutil.move(backup_path, filepath)
                    self.logger.error(f"Translation corrupted JSON in {filepath}, restored from backup: {e}")
                    return False
            
            return False  # No changes made
            
        except Exception as e:
            self.logger.error(f"Error translating {filepath}: {e}")
            return False
    
    def translate_json_recursive(self, obj: Any, changed: bool) -> Tuple[Any, bool]:
        """Recursively translate JSON object."""
        if isinstance(obj, dict):
            new_obj = {}
            for key, value in obj.items():
                new_value, value_changed = self.translate_json_recursive(value, False)
                new_obj[key] = new_value
                if value_changed:
                    changed = True
            return new_obj, changed
            
        elif isinstance(obj, list):
            new_obj = []
            for item in obj:
                new_item, item_changed = self.translate_json_recursive(item, False)
                new_obj.append(new_item)
                if item_changed:
                    changed = True
            return new_obj, changed
            
        elif isinstance(obj, str):
            if self.needs_chinese_translation(obj):
                translated = self.translate_text(obj)
                if translated != obj:
                    return translated, True
            return obj, False
            
        else:
            # Numbers, booleans, null - return as is
            return obj, changed
    
    def translate_text_file(self, filepath: str) -> bool:
        """Translate a text file line by line."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            changed = False
            new_lines = []
            
            for line in lines:
                if self.needs_chinese_translation(line):
                    translated_line = self.translate_text(line.rstrip('\n\r')) + '\n'
                    if translated_line != line:
                        new_lines.append(translated_line)
                        changed = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            if changed:
                # Create backup
                backup_path = f"{filepath}.backup"
                shutil.copy2(filepath, backup_path)
                
                # Write translated file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
                
                # Remove backup
                os.remove(backup_path)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error translating text file {filepath}: {e}")
            return False
    
    def process_file(self, filepath: str) -> bool:
        """Process a single file."""
        try:
            # Calculate checksum before
            checksum_before = self.get_file_checksum(filepath)
            
            # Determine file type and translate accordingly
            changed = False
            if filepath.endswith('.json'):
                changed = self.translate_json_file(filepath)
            elif filepath.endswith(('.txt', '.md')):
                changed = self.translate_text_file(filepath)
            else:
                self.logger.warning(f"Unknown file type: {filepath}")
                return False
            
            # Calculate checksum after
            checksum_after = self.get_file_checksum(filepath) if changed else checksum_before
            
            # Update database
            self.conn.execute("""
                INSERT OR REPLACE INTO files 
                (path, checksum_before, checksum_after, status, changed, last_processed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (filepath, checksum_before, checksum_after, 'done', 1 if changed else 0, 
                  datetime.now().isoformat()))
            
            self.stats['files_processed'] += 1
            if changed:
                self.stats['files_changed'] += 1
            
            # Commit periodically
            if self.stats['files_processed'] % self.config.get('performance', {}).get('checkpoint_frequency', 100) == 0:
                self.conn.commit()
                self.logger.info(f"Processed {self.stats['files_processed']} files, {self.stats['files_changed']} changed")
            
            return changed
            
        except Exception as e:
            self.stats['errors'] += 1
            self.logger.error(f"Error processing {filepath}: {e}")
            
            # Record error in database
            self.conn.execute("""
                INSERT OR REPLACE INTO files 
                (path, status, error_message, last_processed_at)
                VALUES (?, ?, ?, ?)
            """, (filepath, 'error', str(e), datetime.now().isoformat()))
            
            return False
    
    def get_progress_percentage(self) -> float:
        """Calculate current progress percentage."""
        try:
            with open('progress/state.json', 'r') as f:
                state = json.load(f)
            
            total_files = state.get('total_files', 0)
            if total_files == 0:
                return 0.0
                
            processed_count = self.conn.execute(
                "SELECT COUNT(*) FROM files WHERE status IN ('done', 'skipped')"
            ).fetchone()[0]
            
            return (processed_count / total_files) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating progress: {e}")
            return 0.0
    
    def should_commit_progress(self, current_percentage: float) -> bool:
        """Check if we should commit progress at this percentage."""
        try:
            with open('progress/state.json', 'r') as f:
                state = json.load(f)
            
            next_threshold = state.get('next_commit_threshold_percent', 10)
            return current_percentage >= next_threshold
            
        except Exception:
            return False
    
    def commit_progress(self, percentage: float):
        """Commit and push current progress."""
        try:
            # Update state file
            with open('progress/state.json', 'r') as f:
                state = json.load(f)
            
            state['processed_files'] = self.stats['files_processed']
            state['last_audit_time'] = datetime.now().isoformat()
            
            # Calculate next threshold (round up to next 10%)
            next_threshold = ((int(percentage) // 10) + 1) * 10
            state['next_commit_threshold_percent'] = min(next_threshold, 100)
            
            with open('progress/state.json', 'w') as f:
                json.dump(state, f, indent=2)
            
            # Commit to git
            import subprocess
            
            subprocess.run(['git', 'add', '-A'], check=True)
            commit_message = f"Translation Progress: {int(percentage)}% - Processed {self.stats['files_processed']} files, {self.stats['files_changed']} changed, enforcing official Genshin terminology"
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
            subprocess.run(['git', 'push', 'origin', 'upstream/eng-translate'], check=True)
            
            self.logger.info(f"Progress committed: {percentage:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Failed to commit progress: {e}")
    
    def run_translation_loop(self, start_from: int = 0, max_files: Optional[int] = None):
        """Main translation loop."""
        self.logger.info("Starting translation loop...")
        
        try:
            # Load file manifest
            with open('progress/file_manifest.txt', 'r') as f:
                all_files = [line.strip() for line in f if line.strip()]
            
            self.logger.info(f"Total files to process: {len(all_files)}")
            
            # Determine files to process
            files_to_process = all_files[start_from:]
            if max_files:
                files_to_process = files_to_process[:max_files]
            
            self.logger.info(f"Processing {len(files_to_process)} files starting from index {start_from}")
            
            # Process files
            for i, filepath in enumerate(files_to_process, start_from):
                if not os.path.exists(filepath):
                    self.logger.warning(f"File not found: {filepath}")
                    continue
                
                self.process_file(filepath)
                
                # Check if we should commit progress
                current_percentage = self.get_progress_percentage()
                if self.should_commit_progress(current_percentage):
                    self.commit_progress(current_percentage)
                
                # Progress reporting
                if (i + 1) % 1000 == 0:
                    self.logger.info(f"Processed {i + 1} files ({current_percentage:.2f}% complete)")
            
            # Final commit
            final_percentage = self.get_progress_percentage()
            if final_percentage >= 100:
                self.commit_progress(100)
                self.logger.info("Translation completed!")
            
        except KeyboardInterrupt:
            self.logger.info("Translation interrupted by user")
        except Exception as e:
            self.logger.error(f"Error in translation loop: {e}")
            self.logger.error(traceback.format_exc())
        finally:
            self.conn.commit()
            self.conn.close()
            
            # Print final statistics
            self.logger.info("Final Statistics:")
            self.logger.info(f"Files processed: {self.stats['files_processed']}")
            self.logger.info(f"Files changed: {self.stats['files_changed']}")
            self.logger.info(f"Translations made: {self.stats['translations_made']}")
            self.logger.info(f"Glossary applications: {self.stats['glossary_applications']}")
            self.logger.info(f"Errors encountered: {self.stats['errors']}")

def main():
    parser = argparse.ArgumentParser(description="Genshin Impact Translation Pipeline")
    parser.add_argument('--start-from', type=int, default=0, help='File index to start from')
    parser.add_argument('--max-files', type=int, help='Maximum number of files to process')
    parser.add_argument('--continue', action='store_true', help='Continue from last checkpoint')
    parser.add_argument('--config', default='config/translator.yaml', help='Configuration file path')
    
    args = parser.parse_args()
    
    translator = GenshinTranslator(args.config)
    
    if args.__dict__.get('continue', False):
        # TODO: Implement continue logic
        print("Continue functionality not yet implemented")
        return
    
    translator.run_translation_loop(args.start_from, args.max_files)

if __name__ == "__main__":
    main()
