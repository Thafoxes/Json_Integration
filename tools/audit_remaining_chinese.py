#!/usr/bin/env python3
"""
Quick auditing script to check for remaining Chinese content after translation
"""
import os
import json
import re
from pathlib import Path

def contains_chinese(text):
    """Check if text contains Chinese characters"""
    if not text:
        return False
    return bool(re.search(r'[\u4e00-\u9fff]', str(text)))

def scan_file(filepath):
    """Scan a file for Chinese content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            if filepath.suffix.lower() == '.json':
                data = json.load(f)
                return scan_json_recursive(data, filepath)
            else:
                content = f.read()
                if contains_chinese(content):
                    return [(filepath, "text content", content[:100])]
        return []
    except Exception as e:
        return [(filepath, "error", str(e))]

def scan_json_recursive(obj, filepath, path=""):
    """Recursively scan JSON object for Chinese text"""
    issues = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            if contains_chinese(str(key)):
                issues.append((filepath, f"key: {current_path}", str(key)))
            issues.extend(scan_json_recursive(value, filepath, current_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            current_path = f"{path}[{i}]"
            issues.extend(scan_json_recursive(item, filepath, current_path))
    elif isinstance(obj, str) and contains_chinese(obj):
        issues.append((filepath, f"value: {path}", obj))
    
    return issues

def main():
    """Main function to audit Chinese content"""
    print("🔍 Auditing remaining Chinese content...")
    
    # Define directories to scan
    scan_dirs = [
        "BinOutput",
        "Lua", 
        "TextMap",
        "ExcelConfigData",
        "Subtitle"
    ]
    
    # Only scan existing directories
    existing_dirs = [d for d in scan_dirs if os.path.exists(d)]
    
    if not existing_dirs:
        print("❌ No expected directories found. Scanning entire repository...")
        existing_dirs = ["."]
    
    total_files = 0
    files_with_chinese = 0
    chinese_instances = []
    
    for directory in existing_dirs:
        print(f"📂 Scanning {directory}...")
        
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and git
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                # Only scan text-based files
                if not any(file.lower().endswith(ext) for ext in ['.json', '.txt', '.lua', '.csv', '.xml']):
                    continue
                
                filepath = Path(root) / file
                total_files += 1
                
                issues = scan_file(filepath)
                if issues:
                    files_with_chinese += 1
                    chinese_instances.extend(issues)
                
                if total_files % 1000 == 0:
                    print(f"   Processed {total_files} files...")
    
    # Print summary
    print(f"\n📊 Audit Results:")
    print(f"   Total files scanned: {total_files}")
    print(f"   Files with Chinese: {files_with_chinese}")
    print(f"   Total Chinese instances: {len(chinese_instances)}")
    
    if chinese_instances:
        print(f"\n🔍 Sample Chinese content found:")
        for filepath, location, content in chinese_instances[:20]:
            print(f"   {filepath} | {location}: {content[:50]}...")
        
        if len(chinese_instances) > 20:
            print(f"   ... and {len(chinese_instances) - 20} more instances")
    else:
        print("✅ No Chinese content found!")

if __name__ == "__main__":
    main()
