#!/usr/bin/env python3
"""
Test script to debug the quick actions issue
"""

import os
from dotenv import load_dotenv

def test_quick_action_processing():
    """Test how quick actions process their input"""
    load_dotenv()
    
    # Simulate the quick action questions
    example_questions = [
        "What are the main topics in the documents?",
        "Summarize the key findings",
        "What are the recommendations?"
    ]
    
    print("🧪 Testing quick action lambda functions...")
    
    # Test the problematic lambda approach
    print("\n❌ Problematic approach (all will show the last question):")
    handlers = []
    for question in example_questions:
        handler = lambda q=question: q
        handlers.append(handler)
    
    for i, handler in enumerate(handlers):
        result = handler()
        print(f"   Handler {i}: '{result}'")
    
    # Test the correct approach
    print("\n✅ Correct approach (each shows its own question):")
    def create_handler(question_text):
        return lambda: question_text
    
    correct_handlers = []
    for question in example_questions:
        handler = create_handler(question)
        correct_handlers.append(handler)
    
    for i, handler in enumerate(correct_handlers):
        result = handler()
        print(f"   Handler {i}: '{result}'")

if __name__ == "__main__":
    test_quick_action_processing()