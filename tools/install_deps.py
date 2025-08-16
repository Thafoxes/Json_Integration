#!/usr/bin/env python3
"""
Install dependencies for the Genshin Impact translation project.
"""

import subprocess
import sys

def install_package(package):
    """Install a Python package using pip."""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        print(f"✓ Successfully installed {package}")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install {package}: {e}")

def main():
    """Install all required packages."""
    print("Installing dependencies for Genshin Impact Translation Project...")
    
    # Core dependencies
    core_packages = [
        'PyYAML',        # For configuration files
        'requests',      # For API calls (if using cloud translation)
    ]
    
    # Optional ML dependencies (for offline translation)
    ml_packages = [
        'torch',         # PyTorch (CPU version)
        'transformers',  # Hugging Face transformers
        'sentencepiece', # For tokenization
    ]
    
    # Install core packages
    print("\nInstalling core dependencies...")
    for package in core_packages:
        install_package(package)
    
    # Ask user if they want ML packages
    print("\nOptional: Install machine learning packages for offline translation?")
    print("This will allow the system to work without internet connection but requires ~2GB download.")
    install_ml = input("Install ML packages? (y/N): ").lower().strip()
    
    if install_ml in ['y', 'yes']:
        print("\nInstalling machine learning dependencies...")
        for package in ml_packages:
            install_package(package)
    else:
        print("Skipping ML packages. You can install them later with:")
        print("pip install torch transformers sentencepiece")
    
    print("\n✓ Installation complete!")
    print("\nNext steps:")
    print("1. Configure your translation provider in config/translator.yaml")
    print("2. For DeepL/Google: Set up API keys in environment variables")
    print("3. Run translation: python3 tools/translator.py --max-files 100")

if __name__ == "__main__":
    main()
