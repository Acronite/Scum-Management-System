#!/usr/bin/env python3
"""
Game Server Control Panel Setup Script

This script helps set up the game server control panel by:
1. Checking dependencies
2. Creating migrations
3. Installing required packages
4. Providing setup instructions
"""

import os
import sys
import subprocess
import importlib

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    elif sys.version_info >= (3, 13):
        print("⚠️  Python 3.13+ detected. Some dependencies may need updates.")
        print("   Consider using Python 3.11 or 3.12 for best compatibility.")
    print("✅ Python version:", sys.version.split()[0])
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'django',
        'psutil',
        'django_filters',
        'bootstrapform'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_migrations():
    """Create Django migrations"""
    print("\n🔄 Creating migrations...")
    try:
        subprocess.check_call([sys.executable, 'manage.py', 'makemigrations', 'servercontrol'])
        print("✅ Migrations created successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to create migrations")
        return False

def run_migrations():
    """Run Django migrations"""
    print("\n🔄 Running migrations...")
    try:
        subprocess.check_call([sys.executable, 'manage.py', 'migrate'])
        print("✅ Migrations completed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to run migrations")
        return False

def collect_static_files():
    """Collect static files"""
    print("\n📁 Collecting static files...")
    try:
        subprocess.check_call([sys.executable, 'manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to collect static files")
        return False

def create_superuser():
    """Prompt to create superuser"""
    print("\n👤 Creating superuser account...")
    print("You'll need a superuser account to access the admin interface.")
    response = input("Create superuser now? (y/n): ").lower().strip()
    
    if response == 'y':
        try:
            subprocess.check_call([sys.executable, 'manage.py', 'createsuperuser'])
            print("✅ Superuser created successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to create superuser")
            return False
    else:
        print("ℹ️ You can create a superuser later with: python manage.py createsuperuser")
        return True

def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Start the development server:")
    print("   python manage.py runserver")
    print("\n2. Access the control panel:")
    print("   http://localhost:8000/control/")
    print("\n3. Access the admin interface:")
    print("   http://localhost:8000/admin/")
    print("\n4. Add your first game server:")
    print("   - Go to Admin > Server control > Game servers")
    print("   - Click 'Add Game Server'")
    print("   - Fill in your server details")
    print("\n5. Start monitoring (optional):")
    print("   python manage.py monitor_servers")
    print("\n📖 For detailed documentation, see README.md")

def main():
    """Main setup function"""
    print("🎮 Game Server Control Panel Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check for Python 3.13+ compatibility issues
    if sys.version_info >= (3, 13):
        print("\n🔧 Running compatibility check...")
        try:
            subprocess.check_call([sys.executable, 'compatibility_fixes.py'])
        except subprocess.CalledProcessError:
            print("⚠️  Compatibility check completed with warnings")
        except FileNotFoundError:
            print("ℹ️  Compatibility check script not found (optional)")
    
    # Check current directory
    if not os.path.exists('manage.py'):
        print("❌ manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check dependencies
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        install = input("Install missing packages? (y/n): ").lower().strip()
        
        if install == 'y':
            if not install_dependencies():
                sys.exit(1)
        else:
            print("❌ Please install required packages manually:")
            print("pip install -r requirements.txt")
            sys.exit(1)
    
    # Django setup steps
    steps = [
        ("Creating migrations", create_migrations),
        ("Running migrations", run_migrations),
        ("Collecting static files", collect_static_files),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("Please check the error messages above and try again.")
            sys.exit(1)
    
    # Optional superuser creation
    create_superuser()
    
    # Print next steps
    print_next_steps()

if __name__ == '__main__':
    main()