import os
from bmasterai import Agent, MultiAgent

# Set your OpenAI key
os.environ["OPENAI_API_KEY"] = "your-openai-key"

researcher = Agent("Researcher", "AI Expert", "Research the latest on multi-agent systems.")
summarizer = Agent("Summarizer", "Content Condenser", "Summarize the research findings concisely.")
reviewer = Agent("Reviewer", "Quality Checker", "Review the summary for accuracy and suggest improvements.")

multi = MultiAgent([researcher, summarizer, reviewer])
results = multi.collaborate("Latest trends in AI agent collaboration")

for agent, output in results.items():
    print(f"{agent}: {output}")
