#!/usr/bin/env python3
"""
DeepL API setup guide and test for Genshin Impact translation project.
"""

import os
import sys
import subprocess

def print_setup_guide():
    """Print step-by-step setup guide for DeepL API."""
    print("🔧 DeepL API Setup Guide")
    print("=" * 50)
    print()
    print("1. 📝 Sign up for DeepL API:")
    print("   https://www.deepl.com/pro-api")
    print()
    print("2. 💳 Choose your plan:")
    print("   • DeepL API Free: 500,000 characters/month (FREE)")
    print("   • DeepL API Pro: Unlimited usage ($5.99+/month)")
    print()
    print("3. 🔑 Get your API key:")
    print("   • Go to your DeepL account settings")
    print("   • Find 'Authentication Key for DeepL API'")
    print("   • Copy the key (format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx)")
    print()
    print("4. 🌍 Set environment variable:")
    print("   For macOS/Linux:")
    print("   export DEEPL_API_KEY='your-api-key-here'")
    print()
    print("   For Windows:")
    print("   set DEEPL_API_KEY=your-api-key-here")
    print()
    print("5. ✅ Test the setup:")
    print("   python3 tools/setup_deepl.py --test")
    print()

def test_deepl_setup():
    """Test DeepL API setup."""
    print("🧪 Testing DeepL API Setup...")
    print("-" * 30)
    
    # Check if API key is set
    api_key = os.getenv('DEEPL_API_KEY')
    if not api_key:
        print("❌ DEEPL_API_KEY environment variable is not set!")
        print()
        print("Please set your API key:")
        print("export DEEPL_API_KEY='your-api-key-here'")
        return False
    
    print("✅ DEEPL_API_KEY environment variable is set")
    
    # Test the actual API
    try:
        sys.path.append('.')
        from tools.deepl_translator import test_deepl_integration
        
        success = test_deepl_integration()
        if success:
            print()
            print("🎉 DeepL API setup successful!")
            print("You can now run the full translation with:")
            print("python3 tools/translator.py")
            return True
        else:
            print()
            print("❌ DeepL API test failed")
            return False
            
    except ImportError as e:
        print(f"❌ Error importing DeepL module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing DeepL API: {e}")
        return False

def interactive_setup():
    """Interactive setup process."""
    print("🚀 DeepL API Interactive Setup")
    print("=" * 50)
    
    # Check if already configured
    if os.getenv('DEEPL_API_KEY'):
        print("✅ DEEPL_API_KEY is already set!")
        test = input("Would you like to test it? (y/N): ").lower().strip()
        if test in ['y', 'yes']:
            return test_deepl_setup()
        return True
    
    print()
    print_setup_guide()
    
    # Ask user to set up API key
    print("Once you have your DeepL API key, please set it as an environment variable.")
    print()
    
    # Option to set it temporarily
    api_key = input("Enter your DeepL API key (or press Enter to skip): ").strip()
    
    if api_key:
        # Set temporarily for this session
        os.environ['DEEPL_API_KEY'] = api_key
        print("✅ API key set for this session")
        
        # Test it
        if test_deepl_setup():
            print()
            print("💡 To make this permanent, add this to your shell profile:")
            print(f"export DEEPL_API_KEY='{api_key}'")
            return True
    
    print()
    print("⚠️  No API key provided. The system will use offline placeholder mode.")
    print("You can still run the translation, but it won't produce real translations.")
    
    return False

def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DeepL API setup for Genshin Impact translation")
    parser.add_argument('--test', action='store_true', help='Test existing DeepL API setup')
    parser.add_argument('--guide', action='store_true', help='Show setup guide only')
    
    args = parser.parse_args()
    
    if args.test:
        success = test_deepl_setup()
        sys.exit(0 if success else 1)
    elif args.guide:
        print_setup_guide()
    else:
        interactive_setup()

if __name__ == "__main__":
    main()
