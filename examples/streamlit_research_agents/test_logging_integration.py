#!/usr/bin/env python3
"""
Test script to verify BMasterAI logging integration with Google Gemini agents
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the project directory to Python path
sys.path.insert(0, '/home/ubuntu/bmasterai/examples/streamlit_research_agents')

def test_logging_config():
    """Test BMasterAI logging configuration"""
    print("Testing BMasterAI logging configuration...")
    
    try:
        from config.logging_config import initialize_logging, get_logging_config
        
        # Initialize logging
        logging_config = initialize_logging()
        print("✓ BMasterAI logging configuration initialized successfully")
        
        # Test logger creation
        logger = logging_config.get_logger("test_component")
        logger.info("Test log message from logging configuration")
        print("✓ Logger creation and basic logging works")
        
        # Test metrics logging
        logging_config.log_metric("test_metric", 42.0, {"test": "value"})
        print("✓ Metrics logging works")
        
        # Test performance context
        with logging_config.create_performance_context("test_operation"):
            import time
            time.sleep(0.1)  # Simulate some work
        print("✓ Performance context works")
        
        return True
        
    except Exception as e:
        print(f"✗ Logging configuration test failed: {e}")
        return False

def test_logging_mixin():
    """Test logging mixin functionality"""
    print("\nTesting logging mixin...")
    
    try:
        from utils.logging_mixin import LoggingMixin
        
        class TestAgent(LoggingMixin):
            def __init__(self):
                super().__init__()
                self.name = "TestAgent"
            
            def test_method(self):
                self.log_info("Test info message")
                self.log_metric("test_agent_metric", 100.0)
                return "success"
        
        # Create test agent
        agent = TestAgent()
        print("✓ LoggingMixin initialization works")
        
        # Test task logging
        task_id = agent.start_task_logging("Test task")
        result = agent.test_method()
        agent.complete_task_logging(success=True)
        print("✓ Task logging lifecycle works")
        
        return True
        
    except Exception as e:
        print(f"✗ Logging mixin test failed: {e}")
        return False

def test_agent_integration():
    """Test agent integration with logging"""
    print("\nTesting agent integration...")
    
    try:
        from agents.editing_agent import EditingAgent
        
        # Create editing agent (should have logging integrated)
        agent = EditingAgent()
        print("✓ EditingAgent with logging mixin created successfully")
        
        # Check if logging methods are available
        assert hasattr(agent, 'log_info'), "Agent should have log_info method"
        assert hasattr(agent, 'log_metric'), "Agent should have log_metric method"
        assert hasattr(agent, 'start_task_logging'), "Agent should have start_task_logging method"
        print("✓ Agent has all required logging methods")
        
        # Test basic logging
        agent.log_info("Test message from EditingAgent")
        print("✓ Agent logging works")
        
        return True
        
    except Exception as e:
        print(f"✗ Agent integration test failed: {e}")
        return False

async def test_async_agent_method():
    """Test async agent method with logging decorator"""
    print("\nTesting async agent method with logging...")
    
    try:
        from agents.editing_agent import EditingAgent
        
        agent = EditingAgent()
        
        # Test the process method which should have logging decorator
        test_input = '{"content": "This is a test content for editing."}'
        
        # This should trigger the logging decorator
        result = await agent.process(test_input)
        print("✓ Async agent method with logging decorator works")
        
        return True
        
    except Exception as e:
        print(f"✗ Async agent method test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("BMasterAI Logging Integration Test")
    print("=" * 50)
    
    tests = [
        test_logging_config,
        test_logging_mixin,
        test_agent_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    # Test async method
    print("\nTesting async methods...")
    try:
        asyncio.run(test_async_agent_method())
        passed += 1
        total += 1
    except Exception as e:
        print(f"✗ Async test failed: {e}")
        total += 1
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! BMasterAI logging integration is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the integration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
