#!/usr/bin/env python3
"""
Compatibility fixes for Python 3.13+ CGI module deprecation
"""

import sys
import warnings

def check_cgi_compatibility():
    """Check for CGI module compatibility issues"""
    try:
        import cgi
        return True
    except ImportError:
        print("⚠️  CGI module not available (Python 3.13+ deprecation)")
        return False

def setup_cgi_fallback():
    """Set up fallback for CGI functionality if needed"""
    if sys.version_info >= (3, 13):
        print("🔧 Setting up CGI fallback for Python 3.13+")
        
        # Suppress deprecation warnings during testing
        warnings.filterwarnings("ignore", category=DeprecationWarning, module="cgi")
        
        try:
            # Try to import and use email.message for multipart parsing
            from email.message import EmailMessage
            import urllib.parse
            
            class CGIFallback:
                """Minimal CGI functionality replacement"""
                
                @staticmethod
                def parse_qs(query_string):
                    """Parse query string"""
                    return urllib.parse.parse_qs(query_string)
                
                @staticmethod
                def escape(s):
                    """HTML escape"""
                    return (s.replace("&", "&amp;")
                             .replace("<", "&lt;")
                             .replace(">", "&gt;")
                             .replace('"', "&quot;")
                             .replace("'", "&#x27;"))
            
            # Make fallback available
            sys.modules['cgi_fallback'] = CGIFallback()
            print("✅ CGI fallback initialized")
            
        except ImportError as e:
            print(f"❌ Failed to set up CGI fallback: {e}")
            return False
    
    return True

def fix_dependencies():
    """Fix dependencies that might use deprecated CGI module"""
    problematic_packages = [
        'django-bootstrap-form',  # Old package that might use cgi
    ]
    
    replacements = {
        'django-bootstrap-form': 'django-bootstrap-v5',
    }
    
    print("🔍 Checking for problematic dependencies...")
    
    for package in problematic_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"⚠️  Found potentially problematic package: {package}")
            if package in replacements:
                print(f"   Recommended replacement: {replacements[package]}")
        except ImportError:
            # Package not installed, which is good
            pass

def main():
    """Main compatibility check and setup"""
    print("🔧 Python 3.13+ Compatibility Check")
    print("=" * 40)
    
    print(f"Python version: {sys.version}")
    
    if sys.version_info >= (3, 13):
        print("🔍 Python 3.13+ detected - checking CGI compatibility...")
        
        if not check_cgi_compatibility():
            print("❌ CGI module not available")
            print("📝 Recommendations:")
            print("   1. Use Python 3.11 or 3.12 for full compatibility")
            print("   2. Update all dependencies to latest versions")
            print("   3. Use Django 4.0+ which doesn't rely on CGI module")
        
        setup_cgi_fallback()
        fix_dependencies()
        
    else:
        print("✅ Python version compatible with CGI module")
    
    print("\n📋 Next steps:")
    print("1. If you encounter CGI-related errors:")
    print("   - Use Python 3.11 or 3.12")
    print("   - Update to Django 4.0+")
    print("   - Run: pip install -r requirements.txt --upgrade")
    print("\n2. For production, consider:")
    print("   - Python 3.11 LTS (recommended)")
    print("   - Virtual environment isolation")
    print("   - Regular dependency updates")

if __name__ == '__main__':
    main()