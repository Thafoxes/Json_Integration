#!/usr/bin/env python3
"""
Debug script to understand the translate.txt format
"""

import re

def debug_parse():
    with open('translate.txt', 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 10:  # Just look at first 10 lines
                break
            
            line = line.strip()
            if not line or '|' not in line:
                continue
            
            print(f"Line {i+1}: {repr(line)}")
            
            # Split on first |
            parts = line.split('|', 1)
            if len(parts) == 2:
                number, translation = parts
                print(f"  Number: {repr(number.strip())}")
                print(f"  Translation: {repr(translation.strip())}")
                
                # Try to find the boundary between Chinese and English
                translation = translation.strip()
                
                # Look for the first English character after Chinese
                chinese_end = 0
                for j, char in enumerate(translation):
                    if re.match(r'[a-zA-Z]', char):
                        chinese_end = j
                        break
                
                if chinese_end > 0:
                    chinese_part = translation[:chinese_end].strip()
                    english_part = translation[chinese_end:].strip()
                    print(f"  Chinese: {repr(chinese_part)}")
                    print(f"  English: {repr(english_part)}")
                
                print()

if __name__ == "__main__":
    debug_parse()
