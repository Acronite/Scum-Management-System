#!/usr/bin/env python3
"""
Game Server Control Panel - Project Packaging Script

This script creates a complete zip archive of the project for distribution.
"""

import os
import sys
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

def get_project_files():
    """Get list of files to include in the package"""
    
    # Files to always include
    essential_files = [
        'manage.py',
        'requirements.txt',
        'setup.py',
        'compatibility_fixes.py',
        'README.md',
        'PYTHON_CGI_FIX.md',
        'GAMESERVER_CONTROL_PANEL_SUMMARY.md',
        '.gitignore',
        'package_project.py'
    ]
    
    # Directories to include recursively
    include_dirs = [
        'home/',
        'servercontrol/',
        'templates/',
        'static/',
        'accounts/',
        'front/',
        'players/',
        'settings/'
    ]
    
    # Files/directories to exclude
    exclude_patterns = [
        '__pycache__',
        '.pyc',
        '.git',
        'db.sqlite3',
        'venv',
        'env',
        'gameserver_env',
        '.env',
        'logs/',
        'backups/',
        'media/',
        'staticfiles/',
        '.DS_Store',
        'Thumbs.db',
        '*.log'
    ]
    
    files_to_package = []
    base_path = Path('.')
    
    # Add essential files
    for file in essential_files:
        if os.path.exists(file):
            files_to_package.append(file)
            print(f"✓ Added: {file}")
    
    # Add directories recursively
    for dir_name in include_dirs:
        if os.path.exists(dir_name):
            for root, dirs, files in os.walk(dir_name):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check if file should be excluded
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in file_path or file_path.endswith(pattern.replace('*', '')):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        files_to_package.append(file_path)
                        print(f"✓ Added: {file_path}")
    
    return files_to_package

def create_package():
    """Create the project package"""
    
    # Generate package name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    package_name = f"gameserver_control_panel_{timestamp}.zip"
    
    print("🎮 Game Server Control Panel - Project Packager")
    print("=" * 50)
    print(f"Creating package: {package_name}")
    print()
    
    # Get files to package
    print("📁 Collecting project files...")
    files_to_package = get_project_files()
    
    if not files_to_package:
        print("❌ No files found to package!")
        return False
    
    print(f"\n📦 Packaging {len(files_to_package)} files...")
    
    try:
        with zipfile.ZipFile(package_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_package:
                if os.path.exists(file_path):
                    # Add file to zip with relative path
                    arcname = file_path
                    zipf.write(file_path, arcname)
                    print(f"  📄 {file_path}")
        
        # Get package size
        package_size = os.path.getsize(package_name)
        size_mb = package_size / (1024 * 1024)
        
        print(f"\n✅ Package created successfully!")
        print(f"📦 File: {package_name}")
        print(f"📏 Size: {size_mb:.2f} MB ({package_size:,} bytes)")
        print(f"📁 Files: {len(files_to_package)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        return False

def create_installation_guide():
    """Create a quick installation guide"""
    
    guide_content = """# Game Server Control Panel - Quick Installation

## 📦 Package Contents
This zip file contains a complete Django-based game server control panel.

## 🚀 Quick Setup

### 1. Extract the Package
```bash
unzip gameserver_control_panel_*.zip
cd gameserver_control_panel/
```

### 2. Install Dependencies
```bash
# Recommended: Use Python 3.11 or 3.12
python3.11 -m venv gameserver_env
source gameserver_env/bin/activate  # Linux/Mac
# or
gameserver_env\\Scripts\\activate   # Windows

pip install -r requirements.txt
```

### 3. Run Setup
```bash
# Check compatibility (Python 3.13+)
python compatibility_fixes.py

# Run automated setup
python setup.py
```

### 4. Start the Server
```bash
python manage.py runserver
```

### 5. Access the Control Panel
- **Control Panel**: http://localhost:8000/control/
- **Admin Interface**: http://localhost:8000/admin/

## 📚 Documentation
- **README.md** - Complete documentation
- **PYTHON_CGI_FIX.md** - Python 3.13+ compatibility
- **GAMESERVER_CONTROL_PANEL_SUMMARY.md** - Feature overview

## 🎮 Features
✅ Server start/stop/restart controls
✅ Real-time monitoring and metrics
✅ Performance charts and graphs
✅ RCON console integration
✅ Centralized logging system
✅ Configuration management
✅ Backup and recovery tools
✅ Mobile-responsive interface

## 🆘 Support
If you encounter issues:
1. Check PYTHON_CGI_FIX.md for Python 3.13+ problems
2. Use Python 3.11 or 3.12 for best compatibility
3. Run `python compatibility_fixes.py` for diagnostics

---
**Game Server Control Panel** - Professional server management made easy!
"""
    
    with open('INSTALLATION_GUIDE.txt', 'w') as f:
        f.write(guide_content)
    
    print("📋 Created: INSTALLATION_GUIDE.txt")
    return 'INSTALLATION_GUIDE.txt'

def main():
    """Main packaging function"""
    
    # Check if we're in the right directory
    if not os.path.exists('manage.py'):
        print("❌ Error: manage.py not found!")
        print("Please run this script from the project root directory.")
        sys.exit(1)
    
    # Create installation guide
    guide_file = create_installation_guide()
    
    # Create the package
    success = create_package()
    
    if success:
        print("\n🎉 Packaging Complete!")
        print("\n📋 Next Steps:")
        print("1. Share the .zip file")
        print("2. Recipients should extract and follow INSTALLATION_GUIDE.txt")
        print("3. The package includes everything needed to run the control panel")
        print("\n💡 Tip: The package is ready for GitHub, email, or file sharing!")
    else:
        print("\n❌ Packaging failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()