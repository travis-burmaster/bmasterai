#!/usr/bin/env python3
"""
BMasterAI Example Runner

Run this script to see all the enhanced examples in action.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    """Run all examples"""
    print("🚀 BMasterAI Enhanced Examples Runner")
    print("=" * 50)

    try:
        # Import and run examples
        from examples.enhanced_examples import (
            example_stateful_agent_with_logging,
            example_multi_agent_coordination_with_logging,
            example_advanced_monitoring_and_alerts
        )

        print("\n1️⃣ Running Stateful Agent Example...")
        example_stateful_agent_with_logging()

        print("\n2️⃣ Running Multi-Agent Coordination Example...")
        example_multi_agent_coordination_with_logging()

        print("\n3️⃣ Running Advanced Monitoring Example...")
        example_advanced_monitoring_and_alerts()

        print("\n🎉 All examples completed successfully!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure to install BMasterAI first: pip install -e .")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
