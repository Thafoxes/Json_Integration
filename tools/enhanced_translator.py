#!/usr/bin/env python3
"""
Enhanced Genshin Impact JSON Translation System
Supports multiple translation providers with intelligent fallbacks
"""

import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Translation provider imports with error handling
try:
    import deepl
    DEEPL_AVAILABLE = True
except ImportError:
    DEEPL_AVAILABLE = False

try:
    from googletrans import Translator as GoogleTranslator
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class EnhancedTranslationEngine:
    """Enhanced translation engine with multiple providers and smart fallbacks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.providers = {}
        self.fallback_chain = []
        self.setup_providers()
        
    def setup_providers(self):
        """Set up available translation providers"""
        # DeepL setup
        if DEEPL_AVAILABLE and os.getenv('DEEPL_API_KEY'):
            try:
                api_key = os.getenv('DEEPL_API_KEY')
                if api_key.endswith(':fx'):
                    base_url = "https://api-free.deepl.com"
                else:
                    base_url = "https://api.deepl.com"
                
                self.providers['deepl'] = deepl.Translator(api_key, server_url=base_url)
                self.fallback_chain.append('deepl')
                logging.info("✅ DeepL API configured successfully")
            except Exception as e:
                logging.warning(f"⚠️  DeepL setup failed: {e}")
        
        # Google Translate setup
        if GOOGLE_AVAILABLE:
            try:
                self.providers['google'] = GoogleTranslator()
                self.fallback_chain.append('google')
                logging.info("✅ Google Translate configured successfully")
            except Exception as e:
                logging.warning(f"⚠️  Google Translate setup failed: {e}")
        
        # OpenAI setup
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            try:
                openai.api_key = os.getenv('OPENAI_API_KEY')
                self.providers['openai'] = openai
                self.fallback_chain.append('openai')
                logging.info("✅ OpenAI API configured successfully")
            except Exception as e:
                logging.warning(f"⚠️  OpenAI setup failed: {e}")
        
        # Enhanced offline fallback
        self.fallback_chain.append('enhanced_offline')
        
        if not self.fallback_chain:
            logging.warning("⚠️  No translation providers available, using basic offline mode")
            self.fallback_chain = ['basic_offline']
    
    def translate_text(self, text: str, source_lang: str = 'zh', target_lang: str = 'en') -> str:
        """Translate text using the best available provider"""
        if not text.strip():
            return text
        
        for provider in self.fallback_chain:
            try:
                result = self._translate_with_provider(text, provider, source_lang, target_lang)
                if result and result != text:  # Successful translation
                    return result
            except Exception as e:
                logging.debug(f"Provider {provider} failed: {e}")
                continue
        
        # Ultimate fallback
        return self._basic_offline_translate(text)
    
    def _translate_with_provider(self, text: str, provider: str, source_lang: str, target_lang: str) -> str:
        """Translate with specific provider"""
        if provider == 'deepl':
            result = self.providers['deepl'].translate_text(text, target_lang=target_lang.upper())
            return result.text
        
        elif provider == 'google':
            result = self.providers['google'].translate(text, src=source_lang, dest=target_lang)
            return result.text
        
        elif provider == 'openai':
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{
                    "role": "system",
                    "content": "You are a professional translator specializing in Genshin Impact game content. Translate the following Chinese text to English, maintaining game terminology and context."
                }, {
                    "role": "user", 
                    "content": f"Translate this Chinese text to English: {text}"
                }],
                max_tokens=200,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        
        elif provider == 'enhanced_offline':
            return self._enhanced_offline_translate(text)
        
        else:  # basic_offline
            return self._basic_offline_translate(text)
    
    def _enhanced_offline_translate(self, text: str) -> str:
        """Enhanced offline translation with pattern matching and context"""
        # Enhanced translation dictionary for Genshin Impact content
        translations = {
            # Common game terms
            '挖掘宝箱': 'Dig treasure chest',
            '宝箱': 'Treasure chest',
            '普通宝箱': 'Common chest',
            '精美宝箱': 'Exquisite chest',
            '珍贵宝箱': 'Precious chest',
            '华丽宝箱': 'Luxurious chest',
            '挑战': 'Challenge',
            '解密': 'Puzzle',
            '机关': 'Mechanism',
            '传送点': 'Teleport waypoint',
            '七天神像': 'Statue of the Seven',
            '神瞳': 'Oculus',
            '风神瞳': 'Anemoculus',
            '岩神瞳': 'Geoculus',
            '雷神瞳': 'Electroculus',
            '草神瞳': 'Dendroculus',
            '水神瞳': 'Hydroculus',
            '收集': 'Collect',
            '采集': 'Gather',
            '互动': 'Interact',
            '开启': 'Open',
            '激活': 'Activate',
            '完成': 'Complete',
            '任务': 'Quest',
            '成就': 'Achievement',
            '探索': 'Exploration',
            '古剑士铭文': 'Ancient Swordsman Inscription',
            '其一': 'Part 1',
            '其二': 'Part 2',
            '其三': 'Part 3',
            '其四': 'Part 4',
            '其五': 'Part 5',
            # Region names
            '璃月': 'Liyue',
            '蒙德': 'Mondstadt',
            '稻妻': 'Inazuma',
            '须弥': 'Sumeru',
            '枫丹': 'Fontaine',
            '层岩巨渊': 'The Chasm',
            '渊下宫': 'Enkanomiya',
            '金苹果群岛': 'Golden Apple Archipelago',
            # Common phrases
            '前往': 'Go to',
            '到达': 'Reach',
            '寻找': 'Find',
            '获得': 'Obtain',
            '击败': 'Defeat',
            '对话': 'Talk to',
            '使用': 'Use',
            '装备': 'Equip',
            '升级': 'Upgrade',
            '强化': 'Enhance',
            '突破': 'Ascend',
            '元素': 'Element',
            '技能': 'Skill',
            '天赋': 'Talent',
            '圣遗物': 'Artifact',
            '武器': 'Weapon',
            '角色': 'Character',
            '原石': 'Primogem',
            '摩拉': 'Mora',
            '经验': 'Experience',
            '材料': 'Material',
        }
        
        # Try direct translation first
        if text in translations:
            return translations[text]
        
        # Pattern-based translation
        result = text
        for chinese, english in translations.items():
            result = result.replace(chinese, english)
        
        # If no translation was made, create a descriptive translation
        if result == text and self._contains_chinese(text):
            if '宝箱' in text:
                return 'Treasure chest'
            elif '挑战' in text:
                return 'Challenge'
            elif '传送' in text:
                return 'Teleport'
            elif '收集' in text or '采集' in text:
                return 'Collect'
            elif '互动' in text:
                return 'Interact'
            elif '开启' in text or '激活' in text:
                return 'Activate'
            elif '任务' in text:
                return 'Quest'
            elif '成就' in text:
                return 'Achievement'
            else:
                return f"[Untranslated: {text}]"
        
        return result
    
    def _basic_offline_translate(self, text: str) -> str:
        """Basic offline translation fallback"""
        if self._contains_chinese(text):
            return f"[Chinese: {text}]"
        return text
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

class EnhancedGenshinTranslator:
    """Enhanced Genshin Impact Translation System"""
    
    def __init__(self, config_path: str = "tools/translator.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        
        # Setup logging
        self.setup_logging()
        
        # Load glossary
        self.glossary = self.load_glossary()
        logging.info(f"Loaded glossary with {len(self.glossary)} terms")
        
        # Initialize translation engine
        self.translator = EnhancedTranslationEngine(self.config)
        
        # Setup database
        self.setup_database()
        
        # Statistics
        self.stats = {
            'processed': 0,
            'changed': 0,
            'translations': 0,
            'glossary_applications': 0,
            'errors': 0
        }
    
    def setup_logging(self):
        """Setup enhanced logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"enhanced_translator_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.log_file = log_file
    
    def load_config(self) -> dict:
        """Load configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            config = {
                'translation': {
                    'provider': 'auto',
                    'source_language': 'zh',
                    'target_language': 'en'
                },
                'processing': {
                    'batch_size': 100,
                    'progress_interval': 1000,
                    'commit_interval': 0.1
                }
            }
            
        return config
    
    def load_glossary(self) -> Dict[str, str]:
        """Load translation glossary"""
        glossary_path = Path("glossary/glossary.tsv")
        glossary = {}
        
        if glossary_path.exists():
            try:
                with open(glossary_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if line_num == 1:  # Skip header
                            continue
                        
                        parts = line.strip().split('\t')
                        if len(parts) >= 2:
                            chinese = parts[0].strip()
                            english = parts[1].strip()
                            if chinese and english:
                                glossary[chinese] = english
            except Exception as e:
                logging.warning(f"Error loading glossary: {e}")
        
        return glossary
    
    def setup_database(self):
        """Setup progress tracking database"""
        db_dir = Path("progress")
        db_dir.mkdir(exist_ok=True)
        
        self.db_path = db_dir / "enhanced_progress.sqlite"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_progress (
                    file_path TEXT PRIMARY KEY,
                    last_modified REAL,
                    translation_hash TEXT,
                    processed_at TEXT,
                    provider_used TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS translation_stats (
                    timestamp TEXT,
                    files_processed INTEGER,
                    files_changed INTEGER,
                    translations_made INTEGER,
                    glossary_applications INTEGER,
                    provider_used TEXT
                )
            """)
        
        logging.info("Enhanced database initialized")
    
    def find_files_to_translate(self) -> List[Path]:
        """Find all JSON and text files that need translation"""
        extensions = ['.json', '.txt']
        exclude_patterns = [
            'tools/',
            'logs/',
            'progress/',
            '.git/',
            '__pycache__/',
            'node_modules/',
            '.vscode/',
            '.idea/'
        ]
        
        files = []
        for ext in extensions:
            pattern = f"**/*{ext}"
            for file_path in Path('.').glob(pattern):
                if not any(exclude in str(file_path) for exclude in exclude_patterns):
                    files.append(file_path)
        
        return sorted(files)
    
    def needs_translation(self, file_path: Path) -> bool:
        """Check if file needs translation using enhanced detection"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for Chinese characters
            if re.search(r'[\u4e00-\u9fff]', content):
                return True
                
            # Check database for previous processing
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT last_modified FROM file_progress WHERE file_path = ?",
                    (str(file_path),)
                )
                row = cursor.fetchone()
                
                if row:
                    last_modified_db = row[0]
                    current_modified = file_path.stat().st_mtime
                    
                    if current_modified > last_modified_db:
                        return True
                else:
                    return True  # Never processed
                    
        except Exception as e:
            logging.debug(f"Error checking translation need for {file_path}: {e}")
            return True
        
        return False
    
    def translate_json_file(self, file_path: Path) -> bool:
        """Translate a JSON file with enhanced processing"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_data = json.dumps(data, ensure_ascii=False, sort_keys=True)
            changed = False
            translations_made = 0
            glossary_used = 0
            provider_used = None
            
            def translate_recursive(obj):
                nonlocal changed, translations_made, glossary_used, provider_used
                
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        obj[key] = translate_recursive(value)
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        obj[i] = translate_recursive(item)
                elif isinstance(obj, str):
                    if re.search(r'[\u4e00-\u9fff]', obj):
                        # Check glossary first
                        if obj in self.glossary:
                            translated = self.glossary[obj]
                            glossary_used += 1
                            provider_used = 'glossary'
                        else:
                            translated = self.translator.translate_text(obj)
                            translations_made += 1
                            # Determine provider used
                            for prov in self.translator.fallback_chain:
                                if prov in self.translator.providers:
                                    provider_used = prov
                                    break
                        
                        if translated != obj:
                            changed = True
                            return translated
                
                return obj
            
            data = translate_recursive(data)
            
            if changed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                
                # Update database
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO file_progress
                        (file_path, last_modified, translation_hash, processed_at, provider_used)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(file_path),
                        file_path.stat().st_mtime,
                        hash(json.dumps(data, ensure_ascii=False, sort_keys=True)),
                        datetime.now().isoformat(),
                        provider_used
                    ))
                
                self.stats['translations'] += translations_made
                self.stats['glossary_applications'] += glossary_used
                
            return changed
            
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in {file_path}: {e}")
            self.stats['errors'] += 1
            return False
        except Exception as e:
            logging.error(f"Error translating {file_path}: {e}")
            self.stats['errors'] += 1
            return False
    
    def translate_text_file(self, file_path: Path) -> bool:
        """Translate a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not re.search(r'[\u4e00-\u9fff]', content):
                return False  # No Chinese characters
            
            lines = content.split('\n')
            translated_lines = []
            changed = False
            
            for line in lines:
                if re.search(r'[\u4e00-\u9fff]', line):
                    # Check glossary first
                    translated_line = line
                    for chinese, english in self.glossary.items():
                        if chinese in line:
                            translated_line = translated_line.replace(chinese, english)
                            changed = True
                            self.stats['glossary_applications'] += 1
                    
                    # Translate remaining Chinese
                    if re.search(r'[\u4e00-\u9fff]', translated_line):
                        new_translation = self.translator.translate_text(translated_line)
                        if new_translation != translated_line:
                            translated_line = new_translation
                            changed = True
                            self.stats['translations'] += 1
                    
                    translated_lines.append(translated_line)
                else:
                    translated_lines.append(line)
            
            if changed:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(translated_lines))
            
            return changed
            
        except Exception as e:
            logging.error(f"Error translating text file {file_path}: {e}")
            self.stats['errors'] += 1
            return False
    
    def process_files(self):
        """Process all files with enhanced translation"""
        files = self.find_files_to_translate()
        total_files = len(files)
        
        logging.info(f"🚀 Starting enhanced translation of {total_files} files")
        logging.info(f"📋 Available providers: {', '.join(self.translator.fallback_chain)}")
        
        start_time = time.time()
        
        for i, file_path in enumerate(files, 1):
            try:
                if not self.needs_translation(file_path):
                    continue
                
                changed = False
                if file_path.suffix == '.json':
                    changed = self.translate_json_file(file_path)
                elif file_path.suffix == '.txt':
                    changed = self.translate_text_file(file_path)
                
                if changed:
                    self.stats['changed'] += 1
                
                self.stats['processed'] += 1
                
                # Progress reporting
                if i % self.config.get('processing', {}).get('progress_interval', 1000) == 0:
                    elapsed = time.time() - start_time
                    progress = (i / total_files) * 100
                    logging.info(f"📊 Progress: {i}/{total_files} ({progress:.1f}%) - "
                               f"Changed: {self.stats['changed']} - "
                               f"Time: {elapsed:.1f}s")
                
                # Auto-commit progress
                progress = (i / total_files) * 100
                commit_interval = self.config.get('processing', {}).get('commit_interval', 0.1)
                if progress > 0 and progress % (commit_interval * 100) < 0.1:
                    self.commit_progress(progress)
                    
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        # Final commit
        self.commit_progress(100.0)
        
        # Final statistics
        elapsed = time.time() - start_time
        logging.info("🎉 Enhanced translation completed!")
        logging.info(f"📊 Final Statistics:")
        logging.info(f"   Files processed: {self.stats['processed']}")
        logging.info(f"   Files changed: {self.stats['changed']}")
        logging.info(f"   Translations made: {self.stats['translations']}")
        logging.info(f"   Glossary applications: {self.stats['glossary_applications']}")
        logging.info(f"   Errors: {self.stats['errors']}")
        logging.info(f"   Total time: {elapsed:.1f}s")
    
    def commit_progress(self, progress_pct: float):
        """Commit progress to git with enhanced messaging"""
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Create detailed commit message
            commit_msg = (f"Enhanced Translation Progress: {progress_pct:.1f}% - "
                         f"Processed {self.stats['processed']} files, "
                         f"{self.stats['changed']} changed, "
                         f"{self.stats['translations']} translations, "
                         f"{self.stats['glossary_applications']} glossary terms applied")
            
            # Commit
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
            
            # Push
            subprocess.run(['git', 'push'], check=True)
            
            logging.info(f"✅ Progress committed: {progress_pct:.1f}%")
            
        except subprocess.CalledProcessError as e:
            logging.warning(f"⚠️  Git operation failed: {e}")

def main():
    """Main function"""
    try:
        translator = EnhancedGenshinTranslator()
        translator.process_files()
    except KeyboardInterrupt:
        logging.info("🛑 Translation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
