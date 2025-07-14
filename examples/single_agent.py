import os
from bmasterai import Agent

os.environ["OPENAI_API_KEY"] = "your-openai-key"

agent = Agent("Helper", "AI Assistant", "Answer questions helpfully.")
print(agent.perform_task("What's the weather like?"))  # Example task
