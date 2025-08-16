#!/usr/bin/env python3
"""
Build glossary from translate.txt for Genshin Impact translation project.
Generates JSON, TSV, and helper files for automated translation.
"""

import json
import re
import os
from collections import defaultdict

def parse_translate_file(filepath):
    """Parse translate.txt and extract Chinese -> English mappings."""
    translations = {}
    duplicates = defaultdict(list)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or '|' not in line:
                continue
            
            # Split on first | to separate number and translation
            parts = line.split('|', 1)
            if len(parts) != 2:
                continue
            
            number, translation = parts
            number = number.strip()
            translation = translation.strip()
            
            # The format is: Chinese text followed by English text
            # Split by finding where Chinese characters end and English begins
            chinese_chars = []
            english_chars = []
            in_english = False
            
            i = 0
            while i < len(translation):
                char = translation[i]
                
                # Check if this is a Chinese character
                if re.match(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', char):
                    if not in_english:
                        chinese_chars.append(char)
                    else:
                        # This shouldn't happen in well-formed data
                        chinese_chars.append(char)
                elif char.isascii() and (char.isalpha() or char.isspace()):
                    # This is likely English
                    in_english = True
                    english_chars.append(char)
                else:
                    # Punctuation or other characters - add to current section
                    if in_english:
                        english_chars.append(char)
                    else:
                        chinese_chars.append(char)
                
                i += 1
            
            chinese_part = ''.join(chinese_chars).strip()
            english_part = ''.join(english_chars).strip()
            
            # Alternative approach: split on first space before an English word
            if not chinese_part or not english_part:
                # Find the transition point more carefully
                words = translation.split()
                chinese_words = []
                english_words = []
                found_english = False
                
                for word in words:
                    if re.search(r'[\u4e00-\u9fff]', word) and not found_english:
                        chinese_words.append(word)
                    else:
                        found_english = True
                        english_words.append(word)
                
                chinese_part = ' '.join(chinese_words).strip()
                english_part = ' '.join(english_words).strip()
            
            if chinese_part and english_part:
                if chinese_part in translations:
                    if translations[chinese_part] != english_part:
                        duplicates[chinese_part].append((translations[chinese_part], english_part))
                else:
                    translations[chinese_part] = english_part
    
    return translations, duplicates

def normalize_for_matching(text):
    """Normalize text for case-insensitive matching."""
    return re.sub(r'[^\w\s]', '', text.lower().strip())

def build_glossary():
    """Build complete glossary with all helper files."""
    print("Building glossary from translate.txt...")
    
    # Parse translations
    translations, duplicates = parse_translate_file('translate.txt')
    print(f"Found {len(translations)} unique translations")
    
    if duplicates:
        print(f"Found {len(duplicates)} duplicates - using first occurrence")
    
    # Sort by length (longest first) for proper replacement
    sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)
    
    # Create glossary.json
    with open('glossary/glossary.json', 'w', encoding='utf-8') as f:
        json.dump(dict(sorted_translations), f, ensure_ascii=False, indent=2)
    
    # Create glossary.tsv for human review
    with open('glossary/glossary.tsv', 'w', encoding='utf-8') as f:
        f.write("Chinese\tEnglish\n")
        for zh, en in sorted_translations:
            f.write(f"{zh}\t{en}\n")
    
    # Create phrases_regex.txt for longest-match first
    with open('glossary/phrases_regex.txt', 'w', encoding='utf-8') as f:
        for zh, _ in sorted_translations:
            # Escape special regex characters
            escaped = re.escape(zh)
            f.write(f"{escaped}\n")
    
    # Create normalized index for post-translation enforcement
    normalized_index = {}
    for zh, en in translations.items():
        normalized_key = normalize_for_matching(en)
        normalized_index[normalized_key] = en
    
    with open('glossary/normalized_index.json', 'w', encoding='utf-8') as f:
        json.dump(normalized_index, f, ensure_ascii=False, indent=2)
    
    # Create empty custom overrides file
    if not os.path.exists('glossary/custom_overrides.tsv'):
        with open('glossary/custom_overrides.tsv', 'w', encoding='utf-8') as f:
            f.write("Chinese\tEnglish\tSource\tNotes\n")
    
    print("Glossary files created:")
    print("- glossary/glossary.json")
    print("- glossary/glossary.tsv")  
    print("- glossary/phrases_regex.txt")
    print("- glossary/normalized_index.json")
    print("- glossary/custom_overrides.tsv")

if __name__ == "__main__":
    build_glossary()
