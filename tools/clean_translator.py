#!/usr/bin/env python3
"""
Clean Genshin Impact JSON Translation System
Uses Google Translate and enhanced offline dictionary with simplified progress reporting
"""

import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any

# Translation provider imports with error handling
try:
    from googletrans import Translator as GoogleTranslator
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

class CleanTranslationEngine:
    """Clean translation engine with Google Translate and offline fallback"""
    
    def __init__(self):
        self.providers = {}
        self.fallback_chain = []
        self.setup_providers()
        
    def setup_providers(self):
        """Set up available translation providers"""
        # Google Translate setup
        if GOOGLE_AVAILABLE:
            try:
                self.providers['google'] = GoogleTranslator()
                self.fallback_chain.append('google')
                logging.info("✅ Google Translate configured")
            except Exception as e:
                logging.warning(f"⚠️  Google Translate setup failed: {e}")
        
        # Enhanced offline fallback always available
        self.fallback_chain.append('offline')
        
        logging.info(f"📋 Available providers: {', '.join(self.fallback_chain)}")
    
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
        return self._offline_translate(text)
    
    def _translate_with_provider(self, text: str, provider: str, source_lang: str, target_lang: str) -> str:
        """Translate with specific provider"""
        if provider == 'google':
            result = self.providers['google'].translate(text, src=source_lang, dest=target_lang)
            return result.text
        else:  # offline
            return self._offline_translate(text)
    
    def _offline_translate(self, text: str) -> str:
        """Enhanced offline translation with comprehensive Genshin Impact dictionary"""
        # Comprehensive translation dictionary for Genshin Impact content
        translations = {
            # Basic game terms
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
            '锚点': 'Teleport waypoint',
            '七天神像': 'Statue of the Seven',
            '神瞳': 'Oculus',
            '风神瞳': 'Anemoculus',
            '岩神瞳': 'Geoculus', 
            '雷神瞳': 'Electroculus',
            '草神瞳': 'Dendroculus',
            '水神瞳': 'Hydroculus',
            '火神瞳': 'Pyroculus',
            '冰神瞳': 'Cryoculus',
            
            # Actions
            '收集': 'Collect',
            '采集': 'Gather',
            '互动': 'Interact',
            '开启': 'Open',
            '激活': 'Activate', 
            '完成': 'Complete',
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
            
            # Game content
            '任务': 'Quest',
            '成就': 'Achievement',
            '探索': 'Exploration',
            '委托': 'Commission',
            '世界任务': 'World Quest',
            '传说任务': 'Story Quest',
            '角色突破任务': 'Character Ascension Quest',
            
            # Items and materials
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
            '宝石': 'Gem',
            '矿物': 'Ore',
            '植物': 'Plant',
            '动物': 'Animal',
            '怪物': 'Monster',
            '食物': 'Food',
            '药剂': 'Potion',
            
            # Regions
            '璃月': 'Liyue',
            '蒙德': 'Mondstadt', 
            '稻妻': 'Inazuma',
            '须弥': 'Sumeru',
            '枫丹': 'Fontaine',
            '至冬': 'Snezhnaya',
            '纳塔': 'Natlan',
            '层岩巨渊': 'The Chasm',
            '渊下宫': 'Enkanomiya',
            '金苹果群岛': 'Golden Apple Archipelago',
            
            # Elements
            '风': 'Anemo',
            '岩': 'Geo',
            '雷': 'Electro', 
            '草': 'Dendro',
            '水': 'Hydro',
            '火': 'Pyro',
            '冰': 'Cryo',
            
            # Common phrases
            '古剑士铭文': 'Ancient Swordsman Inscription',
            '其一': 'Part 1',
            '其二': 'Part 2', 
            '其三': 'Part 3',
            '其四': 'Part 4',
            '其五': 'Part 5',
            '第一部': 'Part 1',
            '第二部': 'Part 2',
            '第三部': 'Part 3',
            
            # Time and weather
            '白天': 'Day',
            '夜晚': 'Night',
            '晴天': 'Clear',
            '雨天': 'Rain',
            '雪天': 'Snow',
            
            # Numbers in Chinese
            '一': 'One',
            '二': 'Two',
            '三': 'Three', 
            '四': 'Four',
            '五': 'Five',
            '六': 'Six',
            '七': 'Seven',
            '八': 'Eight',
            '九': 'Nine',
            '十': 'Ten',
        }
        
        # Try direct translation first
        if text in translations:
            return translations[text]
        
        # Pattern-based translation for compound terms
        result = text
        for chinese, english in translations.items():
            result = result.replace(chinese, english)
        
        # If no translation was made, create a contextual translation
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
            elif '探索' in text:
                return 'Exploration'
            elif '材料' in text:
                return 'Material'
            elif '武器' in text:
                return 'Weapon'
            elif '角色' in text:
                return 'Character'
            else:
                return f"[Untranslated: {text}]"
        
        return result
    
    def _contains_chinese(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        return bool(re.search(r'[\u4e00-\u9fff]', text))

class CleanGenshinTranslator:
    """Clean Genshin Impact Translation System"""
    
    def __init__(self):
        # Setup logging
        self.setup_logging()
        
        # Load glossary
        self.glossary = self.load_glossary()
        logging.info(f"Loaded glossary with {len(self.glossary)} terms")
        
        # Initialize translation engine
        self.translator = CleanTranslationEngine()
        
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
        """Setup clean logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"clean_translator_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.log_file = log_file
    
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
        
        self.db_path = db_dir / "clean_progress.sqlite"
        
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
        
        logging.info("Database initialized")
    
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
        """Check if file needs translation"""
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
        """Translate a JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            original_data = json.dumps(data, ensure_ascii=False, sort_keys=True)
            changed = False
            translations_made = 0
            glossary_used = 0
            provider_used = 'offline'
            
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
                            if GOOGLE_AVAILABLE and 'google' in self.translator.providers:
                                provider_used = 'google'
                            else:
                                provider_used = 'offline'
                        
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
        """Process all files with clean translation"""
        files = self.find_files_to_translate()
        total_files = len(files)
        
        logging.info(f"🚀 Starting clean translation of {total_files} files")
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
                
                # Progress reporting every 1000 files
                if i % 1000 == 0:
                    elapsed = time.time() - start_time
                    progress = (i / total_files) * 100
                    logging.info(f"📊 Progress: {i}/{total_files} ({progress:.1f}%) - "
                               f"Changed: {self.stats['changed']} - "
                               f"Time: {elapsed:.1f}s")
                
                # Auto-commit progress every 10%
                progress = (i / total_files) * 100
                if progress > 0 and progress % 10 < 0.1:
                    self.commit_progress()
                    
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")
                self.stats['errors'] += 1
        
        # Final commit
        self.commit_progress()
        
        # Final statistics
        elapsed = time.time() - start_time
        logging.info("🎉 Clean translation completed!")
        logging.info(f"📊 Final Statistics:")
        logging.info(f"   Files processed: {self.stats['processed']}")
        logging.info(f"   Files changed: {self.stats['changed']}")
        logging.info(f"   Translations made: {self.stats['translations']}")
        logging.info(f"   Glossary applications: {self.stats['glossary_applications']}")
        logging.info(f"   Errors: {self.stats['errors']}")
        logging.info(f"   Total time: {elapsed:.1f}s")
    
    def commit_progress(self):
        """Commit progress to git with clean messaging"""
        try:
            # Add all changes
            subprocess.run(['git', 'add', '.'], check=True)
            
            # Create simple commit message
            commit_msg = f"Translation progress: {self.stats['changed']} files updated"
            
            # Commit
            result = subprocess.run(['git', 'commit', '-m', commit_msg], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logging.info(f"✅ Progress committed: {self.stats['changed']} files")
            else:
                logging.debug("No changes to commit")
            
        except subprocess.CalledProcessError as e:
            logging.warning(f"⚠️  Git operation failed: {e}")

def main():
    """Main function"""
    try:
        translator = CleanGenshinTranslator()
        translator.process_files()
    except KeyboardInterrupt:
        logging.info("🛑 Translation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
