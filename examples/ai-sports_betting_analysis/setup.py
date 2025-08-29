#!/usr/bin/env python3
"""
Setup script for Sports Betting Analysis Multi-Agent AI System

This script automates the installation and configuration process.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_banner():
    """Print installation banner"""
    print("=" * 70)
    print("🏈 Sports Betting Analysis - Multi-Agent AI System")
    print("=" * 70)
    print("Setting up your sports betting analysis environment...")
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 11):
        print("❌ Error: Python 3.11 or higher is required")
        print(f"   Current version: {sys.version}")
        print("   Please upgrade Python and try again")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    print()

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Error installing dependencies")
        print("   Please check your internet connection and try again")
        sys.exit(1)
    
    print()

def setup_environment():
    """Set up environment configuration"""
    print("⚙️ Setting up environment configuration...")
    
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("   Please edit .env with your actual API keys")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  Warning: No .env.example file found")
    
    print()

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "logs",
        "cache",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created {directory}/ directory")
    
    print()

def check_api_keys():
    """Check if API keys are configured"""
    print("🔑 Checking API key configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("   Please create .env file with your API keys")
        return
    
    required_keys = [
        "GOOGLE_API_KEY"
    ]
    
    optional_keys = [
        "TAVILY_API_KEY",
        "THE_ODDS_API_KEY",
        "FIRECRAWL_API_KEY"
    ]
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    missing_required = []
    missing_optional = []
    
    for key in required_keys:
        if f"{key}=test_key" in env_content or f"{key}=" in env_content:
            missing_required.append(key)
    
    for key in optional_keys:
        if f"{key}=test_key" in env_content or f"{key}=" in env_content:
            missing_optional.append(key)
    
    if missing_required:
        print("❌ Missing required API keys:")
        for key in missing_required:
            print(f"   - {key}")
        print("   Please add these keys to your .env file")
    else:
        print("✅ Required API keys configured")
    
    if missing_optional:
        print("⚠️  Optional API keys not configured:")
        for key in missing_optional:
            print(f"   - {key}")
        print("   The system will use mock data for these services")
    
    print()

def test_installation():
    """Test if the installation works"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        import streamlit
        import agno
        import pandas
        import plotly
        print("✅ Core packages imported successfully")
        
        # Test agent imports
        from base_agent import BaseAgent, CoordinationAgent
        from data_collection_agent import DataCollectionAgent
        from statistical_analysis_agent import StatisticalAnalysisAgent
        from probability_calculation_agent import ProbabilityCalculationAgent
        print("✅ Agent modules imported successfully")
        
        print("✅ Installation test passed")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please check the installation and try again")
        sys.exit(1)
    
    print()

def print_next_steps():
    """Print next steps for the user"""
    print("🎉 Installation completed successfully!")
    print()
    print("Next steps:")
    print("1. Edit .env file with your actual API keys")
    print("2. Run the application:")
    print("   streamlit run sports_betting_streamlit_app.py")
    print()
    print("3. Open your browser to http://localhost:8501")
    print()
    print("For help and documentation:")
    print("- README.md: Complete documentation")
    print("- .env.example: API key configuration guide")
    print()
    print("⚠️  Remember: This tool is for educational purposes only!")
    print("   Always gamble responsibly and follow local laws.")
    print()

def main():
    """Main setup function"""
    print_banner()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run setup steps
    check_python_version()
    install_dependencies()
    setup_environment()
    create_directories()
    check_api_keys()
    test_installation()
    print_next_steps()

if __name__ == "__main__":
    main()

