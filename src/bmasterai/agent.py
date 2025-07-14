import openai

class Agent:
    def __init__(self, name, role, instructions, api_key=None):
        self.name = name
        self.role = role
        self.instructions = instructions
        openai.api_key = api_key or "your-default-key"  # Set via env in production

    def perform_task(self, input_data):
        """Calls LLM to perform the agent's task."""
        prompt = f"As {self.role}, {self.instructions}. Input: {input_data}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Or use gpt-4, etc.
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    def __str__(self):
        return f"Agent: {self.name} ({self.role})"
