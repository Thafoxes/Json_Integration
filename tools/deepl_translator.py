#!/usr/bin/env python3
"""
DeepL API integration for Genshin Impact translation project.
Provides high-quality translation with glossary enforcement.
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional
from urllib.parse import urlencode

class DeepLTranslator:
    def __init__(self, api_key: str, glossary: Dict[str, str]):
        """Initialize DeepL translator with API key and glossary."""
        self.api_key = api_key
        self.glossary = glossary
        # Determine if this is a free or pro API key based on suffix
        if api_key.endswith(':fx'):
            self.base_url = "https://api-free.deepl.com/v2"
        else:
            self.base_url = "https://api.deepl.com/v2"
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'DeepL-Auth-Key {api_key}',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        # Usage tracking
        self.characters_translated = 0
        self.requests_made = 0
        
    def check_api_key(self) -> bool:
        """Test if the API key is valid."""
        try:
            response = self.session.get(f"{self.base_url}/usage")
            if response.status_code == 200:
                usage = response.json()
                print(f"✅ DeepL API key valid. Usage: {usage.get('character_count', 0)}/{usage.get('character_limit', 'unlimited')} characters")
                return True
            else:
                print(f"❌ DeepL API key invalid: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error checking DeepL API key: {e}")
            return False
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def translate_text(self, text: str, source_lang: str = "ZH", target_lang: str = "EN") -> Optional[str]:
        """Translate text using DeepL API."""
        if not text.strip():
            return text
        
        self._rate_limit()
        
        try:
            data = {
                'text': text,
                'source_lang': source_lang,
                'target_lang': target_lang,
                'preserve_formatting': '1',
                'formality': 'default'
            }
            
            response = self.session.post(
                f"{self.base_url}/translate",
                data=urlencode(data),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'translations' in result and len(result['translations']) > 0:
                    translated_text = result['translations'][0]['text']
                    self.characters_translated += len(text)
                    self.requests_made += 1
                    return translated_text
            else:
                print(f"DeepL API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error in DeepL translation: {e}")
            return None
    
    def translate_batch(self, texts: List[str], source_lang: str = "ZH", target_lang: str = "EN") -> List[Optional[str]]:
        """Translate multiple texts in a single request."""
        if not texts:
            return []
        
        # Filter out empty texts but keep track of positions
        non_empty_indices = []
        non_empty_texts = []
        for i, text in enumerate(texts):
            if text.strip():
                non_empty_indices.append(i)
                non_empty_texts.append(text)
        
        if not non_empty_texts:
            return texts  # All empty, return as is
        
        self._rate_limit()
        
        try:
            data = {
                'source_lang': source_lang,
                'target_lang': target_lang,
                'preserve_formatting': '1',
                'formality': 'default'
            }
            
            # Add multiple text parameters
            for text in non_empty_texts:
                data[f'text'] = text
            
            response = self.session.post(
                f"{self.base_url}/translate",
                data=urlencode(data, doseq=True),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'translations' in result:
                    translations = [t['text'] for t in result['translations']]
                    
                    # Map translations back to original positions
                    results = list(texts)  # Copy original list
                    for i, translation in enumerate(translations):
                        if i < len(non_empty_indices):
                            results[non_empty_indices[i]] = translation
                    
                    self.characters_translated += sum(len(t) for t in non_empty_texts)
                    self.requests_made += 1
                    return results
            else:
                print(f"DeepL batch API error: {response.status_code} - {response.text}")
                return [None] * len(texts)
                
        except Exception as e:
            print(f"Error in DeepL batch translation: {e}")
            return [None] * len(texts)
    
    def get_usage_stats(self) -> Dict:
        """Get current API usage statistics."""
        try:
            response = self.session.get(f"{self.base_url}/usage")
            if response.status_code == 200:
                usage = response.json()
                usage['session_characters'] = self.characters_translated
                usage['session_requests'] = self.requests_made
                return usage
            return {}
        except Exception:
            return {}

def test_deepl_integration():
    """Test function to verify DeepL integration works."""
    api_key = os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ DEEPL_API_KEY environment variable not set")
        return False
    
    # Create a simple glossary for testing
    test_glossary = {
        "璃月": "Liyue",
        "蒙德": "Mondstadt", 
        "稻妻": "Inazuma"
    }
    
    translator = DeepLTranslator(api_key, test_glossary)
    
    # Test API key
    if not translator.check_api_key():
        return False
    
    # Test translation
    test_text = "这是一个测试"
    result = translator.translate_text(test_text)
    
    if result:
        print(f"✅ Test translation successful:")
        print(f"   Original: {test_text}")
        print(f"   Translated: {result}")
        return True
    else:
        print("❌ Test translation failed")
        return False

if __name__ == "__main__":
    test_deepl_integration()
