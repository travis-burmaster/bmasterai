class MultiAgent:
    def __init__(self, agents):
        self.agents = agents

    def collaborate(self, initial_task):
        """Agents collaborate: Each processes output from the previous one."""
        current_output = initial_task
        results = {}
        for agent in self.agents:
            print(f"{agent} is working...")
            current_output = agent.perform_task(current_output)
            results[agent.name] = current_output
        return results
