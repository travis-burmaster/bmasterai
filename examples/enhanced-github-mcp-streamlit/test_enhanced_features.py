#!/usr/bin/env python3
"""
Test script for Enhanced MCP GitHub Analyzer
Tests the new feature implementation capabilities
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.feature_agent import get_feature_agent
from agents.coordinator import get_workflow_coordinator
from utils.feature_pr_worker import get_feature_pr_worker

def test_feature_pr_worker():
    """Test the feature PR worker utilities"""
    print("🧪 Testing Feature PR Worker...")
    
    worker = get_feature_pr_worker()
    
    # Test branch name generation
    test_prompts = [
        "Add a login system with JWT authentication",
        "Fix the bug in user profile update",
        "Add dark mode toggle to the UI"
    ]
    
    for prompt in test_prompts:
        branch_name = worker.generate_branch_name(prompt)
        print(f"  Prompt: '{prompt}'")
        print(f"  Branch: {branch_name}")
        print(f"  Valid: {worker.validate_branch_name(branch_name)}")
        print()
    
    # Test repo URL parsing
    test_urls = [
        "https://github.com/owner/repo",
        "https://github.com/owner/repo.git",
        "git@github.com:owner/repo.git"
    ]
    
    for url in test_urls:
        try:
            repo_info = worker.extract_repo_info(url)
            print(f"  URL: {url}")
            print(f"  Parsed: {repo_info}")
        except Exception as e:
            print(f"  URL: {url} - Error: {e}")
        print()

def test_feature_agent_initialization():
    """Test feature agent initialization"""
    print("🤖 Testing Feature Agent Initialization...")
    
    try:
        agent = get_feature_agent()
        print(f"  Agent ID: {agent.agent_id}")
        print(f"  Agent Name: {agent.agent_name}")
        print("  ✅ Feature Agent initialized successfully")
    except Exception as e:
        print(f"  ❌ Feature Agent initialization failed: {e}")
    print()

def test_coordinator_enhancement():
    """Test workflow coordinator with feature implementation"""
    print("🎯 Testing Enhanced Workflow Coordinator...")
    
    try:
        coordinator = get_workflow_coordinator()
        print(f"  Coordinator ID: {coordinator.agent_id}")
        print(f"  Has Feature Agent: {hasattr(coordinator, 'feature_agent')}")
        print(f"  Has Feature Implementation Method: {hasattr(coordinator, 'execute_feature_implementation')}")
        print("  ✅ Enhanced Coordinator initialized successfully")
    except Exception as e:
        print(f"  ❌ Enhanced Coordinator initialization failed: {e}")
    print()

async def test_feature_plan_generation():
    """Test feature plan generation (mock test)"""
    print("📋 Testing Feature Plan Generation...")
    
    try:
        agent = get_feature_agent()
        
        # Mock repository structure
        mock_repo_structure = {
            "project_type": {
                "type": "python",
                "framework": "flask",
                "package_manager": "pip"
            },
            "file_structure": {
                "files": ["app.py", "requirements.txt", "README.md"],
                "directories": ["templates", "static"],
                "important_files": {
                    "python_deps": "requirements.txt",
                    "readme": "README.md"
                },
                "source_files": ["app.py"]
            },
            "main_language": "Python"
        }
        
        mock_repo_info = {
            "owner": "test-owner",
            "repo": "test-repo",
            "full_name": "test-owner/test-repo"
        }
        
        # This would normally call the LLM, but we'll just test the structure
        print("  Mock repository structure created")
        print(f"  Project type: {mock_repo_structure['project_type']['type']}")
        print(f"  Framework: {mock_repo_structure['project_type']['framework']}")
        print(f"  Source files: {len(mock_repo_structure['file_structure']['source_files'])}")
        print("  ✅ Feature plan generation structure ready")
        
    except Exception as e:
        print(f"  ❌ Feature plan generation test failed: {e}")
    print()

def test_file_categorization():
    """Test file categorization functionality"""
    print("📁 Testing File Categorization...")
    
    worker = get_feature_pr_worker()
    
    test_files = [
        "app.py",
        "main.js",
        "config.json",
        "README.md",
        "test_app.py",
        "style.css",
        "image.png",
        "Dockerfile"
    ]
    
    categories = worker.categorize_files_by_type(test_files)
    
    for category, files in categories.items():
        if files:
            print(f"  {category.title()}: {files}")
    
    print("  ✅ File categorization completed")
    print()

def test_implementation_time_estimation():
    """Test implementation time estimation"""
    print("⏱️ Testing Implementation Time Estimation...")
    
    worker = get_feature_pr_worker()
    
    test_plans = [
        {
            "feature_analysis": {"complexity": "low"},
            "files_to_modify": [{"path": "app.py"}],
            "dependencies": []
        },
        {
            "feature_analysis": {"complexity": "medium"},
            "files_to_modify": [{"path": "app.py"}, {"path": "config.py"}],
            "dependencies": [{"name": "flask-login"}]
        },
        {
            "feature_analysis": {"complexity": "high"},
            "files_to_modify": [{"path": f"file{i}.py" for i in range(5)}],
            "dependencies": [{"name": "dep1"}, {"name": "dep2"}]
        }
    ]
    
    for i, plan in enumerate(test_plans, 1):
        estimate = worker.estimate_implementation_time(plan)
        complexity = plan["feature_analysis"]["complexity"]
        print(f"  Plan {i} ({complexity} complexity):")
        print(f"    Estimated time: {estimate['estimated_hours']} hours")
        print(f"    Confidence: {estimate['confidence']}")
    
    print("  ✅ Implementation time estimation completed")
    print()

def main():
    """Run all tests"""
    print("🚀 Enhanced MCP GitHub Analyzer - Feature Tests")
    print("=" * 50)
    print()
    
    # Run synchronous tests
    test_feature_pr_worker()
    test_feature_agent_initialization()
    test_coordinator_enhancement()
    test_file_categorization()
    test_implementation_time_estimation()
    
    # Run async tests
    print("Running async tests...")
    asyncio.run(test_feature_plan_generation())
    
    print("🎉 All tests completed!")
    print()
    print("Next steps:")
    print("1. Set up your GitHub token: export GITHUB_TOKEN='your_token'")
    print("2. Set up your AI API key: export ANTHROPIC_API_KEY='your_key'")
    print("3. Run the application: streamlit run app.py")
    print("4. Try the Feature Addition mode with a real repository!")

if __name__ == "__main__":
    main()
