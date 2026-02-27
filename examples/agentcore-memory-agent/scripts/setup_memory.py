"""
One-time setup: Create the AgentCore Memory store.
Run this before deploying the agent.

Usage:
    python scripts/setup_memory.py
"""

import json
import sys

import boto3

REGION = "us-east-1"
MEMORY_NAME = "TelegramAgentMemory"


def create_memory_store():
    control = boto3.client("bedrock-agentcore-control", region_name=REGION)

    print(f"Creating memory store '{MEMORY_NAME}'...")

    try:
        response = control.create_memory(
            name=MEMORY_NAME,
            description="Persistent memory for the Telegram assistant agent. "
                        "Stores session summaries, user preferences, and semantic facts.",
            eventExpiryDuration=180,  # 180 days
            memoryStrategies=[
                {
                    "summaryMemoryStrategy": {
                        "name": "SessionSummarizer",
                        "description": "Generates concise summaries when sessions end.",
                        "namespaces": ["/summaries/{actorId}/{sessionId}/"],
                    }
                },
                {
                    "userPreferenceMemoryStrategy": {
                        "name": "PreferenceLearner",
                        "description": "Extracts user preferences from conversations "
                                       "(communication style, interests, settings).",
                        "namespaces": ["/preferences/{actorId}/"],
                    }
                },
                {
                    "semanticMemoryStrategy": {
                        "name": "FactExtractor",
                        "description": "Extracts and stores factual knowledge mentioned "
                                       "in conversations for future reference.",
                        "namespaces": ["/facts/{actorId}/"],
                    }
                },
            ],
        )

        memory_id = response["memory"]["id"]
        print(f"\nMemory store created successfully!")
        print(f"  Memory ID: {memory_id}")
        print(f"  Name:      {MEMORY_NAME}")
        print(f"\nAdd this to your environment:")
        print(f"  export MEMORY_ID={memory_id}")
        print(f"\nOr add to your .env file:")
        print(f"  MEMORY_ID={memory_id}")

        return memory_id

    except control.exceptions.ConflictException:
        print(f"Memory store '{MEMORY_NAME}' already exists.")
        # List and find the existing one
        memories = control.list_memories()
        for mem in memories.get("memories", []):
            if mem["name"] == MEMORY_NAME:
                print(f"  Existing Memory ID: {mem['id']}")
                return mem["id"]
        print("  Could not find existing memory ID. Check the console.")
        return None

    except Exception as e:
        print(f"Error creating memory store: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    create_memory_store()
