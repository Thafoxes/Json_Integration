#!/usr/bin/env python3
"""
Build glossary from translate.txt for Genshin Impact translation project.
Handles format: "Chinese text English text" (no pipe separator)
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
            if not line:
                continue
            
            # Find the transition point between Chinese and English
            # Look for the first space followed by an English character
            chinese_part = ""
            english_part = ""
            
            # Method 1: Find first English letter
            for i, char in enumerate(line):
                if char.isascii() and char.isalpha():
                    # Found first English letter, everything before is Chinese
                    chinese_part = line[:i].strip()
                    english_part = line[i:].strip()
                    break
            
            # Method 2: If method 1 failed, try splitting on first space before English word
            if not chinese_part or not english_part:
                words = line.split()
                chinese_words = []
                english_words = []
                transition_found = False
                
                for word in words:
                    if re.search(r'[\u4e00-\u9fff]', word) and not transition_found:
                        chinese_words.append(word)
                    else:
                        transition_found = True
                        english_words.append(word)
                
                chinese_part = ' '.join(chinese_words).strip()
                english_part = ' '.join(english_words).strip()
            
            if chinese_part and english_part:
                if chinese_part in translations:
                    if translations[chinese_part] != english_part:
                        duplicates[chinese_part].append((translations[chinese_part], english_part))
                        print(f"Duplicate found: {chinese_part} -> {translations[chinese_part]} vs {english_part}")
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
    
    # Show a few examples
    print("\nFirst 10 translations:")
    for i, (zh, en) in enumerate(translations.items()):
        if i >= 10:
            break
        print(f"  {zh} -> {en}")
    
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
        if normalized_key in normalized_index and normalized_index[normalized_key] != en:
            print(f"Normalized collision: {normalized_key} -> {normalized_index[normalized_key]} vs {en}")
        normalized_index[normalized_key] = en
    
    with open('glossary/normalized_index.json', 'w', encoding='utf-8') as f:
        json.dump(normalized_index, f, ensure_ascii=False, indent=2)
    
    # Create empty custom overrides file
    if not os.path.exists('glossary/custom_overrides.tsv'):
        with open('glossary/custom_overrides.tsv', 'w', encoding='utf-8') as f:
            f.write("Chinese\tEnglish\tSource\tNotes\n")
    
    print("\nGlossary files created:")
    print("- glossary/glossary.json")
    print("- glossary/glossary.tsv")  
    print("- glossary/phrases_regex.txt")
    print("- glossary/normalized_index.json")
    print("- glossary/custom_overrides.tsv")

if __name__ == "__main__":
    build_glossary()
