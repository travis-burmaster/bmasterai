import os
from bmasterai import Agent, MultiAgent

class StatefulAgent(Agent):
    """Extended Agent class with basic state management capabilities"""

    def __init__(self, name, role, instructions, api_key=None, user_id=None):
        super().__init__(name, role, instructions, api_key)
        self.user_id = user_id
        self.state = {}  # Simple state storage
        self.memory = []  # Basic memory storage

    def set_state(self, key, value):
        """Set a state value"""
        self.state[key] = value
        print(f"[{self.name}] State set: {key} = {value}")

    def get_state(self, key, default=None):
        """Get a state value"""
        return self.state.get(key, default)

    def has_state(self, key):
        """Check if state key exists"""
        return key in self.state

    def increment_state(self, key, increment=1, default=0):
        """Increment a numeric state value"""
        current = self.get_state(key, default)
        new_value = current + increment
        self.set_state(key, new_value)
        return new_value

    def append_to_state(self, key, value, max_length=None):
        """Append to a list state value"""
        current = self.get_state(key, [])
        if not isinstance(current, list):
            current = [current]
        current.append(value)
        if max_length and len(current) > max_length:
            current = current[-max_length:]
        self.set_state(key, current)

    def add_memory(self, content, memory_type="short"):
        """Add content to memory"""
        memory_entry = {
            "content": content,
            "type": memory_type,
            "timestamp": __import__('time').time(),
            "agent": self.name
        }
        self.memory.append(memory_entry)
        print(f"[{self.name}] Memory added: {content[:50]}...")

    def search_memory(self, query, memory_type=None):
        """Simple memory search"""
        results = []
        for entry in self.memory:
            if memory_type and entry["type"] != memory_type:
                continue
            if query.lower() in entry["content"].lower():
                results.append(entry)
        return results

    def perform_task_with_state(self, input_data):
        """Enhanced task performance with state tracking"""
        # Track task count
        self.increment_state("tasks_completed")

        # Add to memory
        self.add_memory(f"Processing task: {input_data}", "short")

        # Get previous context from memory
        context = ""
        recent_memories = self.memory[-3:] if len(self.memory) > 3 else self.memory
        if recent_memories:
            context = "Previous context: " + "; ".join([m["content"] for m in recent_memories])

        # Enhanced prompt with context and state
        task_count = self.get_state("tasks_completed", 0)
        prompt = f"""As {self.role}, {self.instructions}

Context: {context}
Current task #{task_count}: {input_data}
User ID: {self.user_id}

Please provide a response that builds on previous context."""

        # Simulate LLM call (replace with actual OpenAI call in production)
        response = f"[{self.name}] Processed task #{task_count}: {input_data}"

        # Store result in memory
        self.add_memory(f"Completed: {response}", "long")

        return response

class StatefulMultiAgent(MultiAgent):
    """Enhanced MultiAgent with shared state management"""

    def __init__(self, agents, user_id=None):
        super().__init__(agents)
        self.user_id = user_id
        self.shared_state = {}

    def set_shared_state(self, key, value):
        """Set shared state across all agents"""
        self.shared_state[key] = value
        print(f"[SHARED] State set: {key} = {value}")

    def get_shared_state(self, key, default=None):
        """Get shared state value"""
        return self.shared_state.get(key, default)

    def collaborate_with_state(self, initial_task):
        """Enhanced collaboration with state management"""
        self.set_shared_state("workflow_started", True)
        self.set_shared_state("current_phase", "initialization")

        current_output = initial_task
        results = {}

        for i, agent in enumerate(self.agents):
            phase_name = f"phase_{i+1}_{agent.name.lower()}"
            self.set_shared_state("current_phase", phase_name)

            print(f"\n=== {agent} is working on {phase_name} ===")

            # Pass shared state to agent
            if hasattr(agent, 'set_state'):
                agent.set_state("shared_workflow_phase", phase_name)
                agent.set_state("workflow_progress", f"{i+1}/{len(self.agents)}")

            # Process with stateful method if available
            if hasattr(agent, 'perform_task_with_state'):
                current_output = agent.perform_task_with_state(current_output)
            else:
                current_output = agent.perform_task(current_output)

            results[agent.name] = current_output

            # Update shared progress
            progress = ((i + 1) / len(self.agents)) * 100
            self.set_shared_state("progress_percentage", progress)

        self.set_shared_state("workflow_completed", True)
        self.set_shared_state("current_phase", "completed")

        return results

def main():
    """Demonstrate basic state management with bmasterai"""

    # Set your OpenAI key (in production, use environment variables)
    os.environ["OPENAI_API_KEY"] = "your-openai-key-here"

    print("=== bmasterai Stateful Agents Demo ===\n")

    # Create stateful agents with user context
    researcher = StatefulAgent(
        name="Researcher", 
        role="AI Research Specialist",
        instructions="Research topics thoroughly and maintain context across tasks",
        user_id="demo_user_123"
    )

    analyzer = StatefulAgent(
        name="Analyzer",
        role="Data Analysis Expert", 
        instructions="Analyze research findings and build on previous work",
        user_id="demo_user_123"
    )

    writer = StatefulAgent(
        name="Writer",
        role="Technical Writer",
        instructions="Create comprehensive reports based on research and analysis",
        user_id="demo_user_123"
    )

    # Initialize some state
    researcher.set_state("research_domain", "AI Safety")
    researcher.set_state("expertise_level", "expert")

    analyzer.set_state("analysis_method", "quantitative")
    analyzer.set_state("confidence_threshold", 0.8)

    writer.set_state("writing_style", "technical")
    writer.set_state("target_audience", "researchers")

    # Create stateful multi-agent system
    team = StatefulMultiAgent([researcher, analyzer, writer], user_id="demo_user_123")

    # Set shared project state
    team.set_shared_state("project_name", "AI Safety Research Report")
    team.set_shared_state("deadline", "2024-12-31")
    team.set_shared_state("quality_standard", "peer_review_ready")

    # Run collaborative workflow with state management
    initial_task = "Research the latest developments in AI safety and alignment"

    print("Starting collaborative workflow...\n")
    results = team.collaborate_with_state(initial_task)

    # Display results and final state
    print("\n=== WORKFLOW RESULTS ===")
    for agent_name, output in results.items():
        print(f"\n{agent_name}: {output}")

    print("\n=== FINAL SHARED STATE ===")
    for key, value in team.shared_state.items():
        print(f"{key}: {value}")

    print("\n=== INDIVIDUAL AGENT STATES ===")
    for agent in team.agents:
        if hasattr(agent, 'state'):
            print(f"\n{agent.name} state:")
            for key, value in agent.state.items():
                print(f"  {key}: {value}")

            print(f"  Memory entries: {len(agent.memory)}")
            if agent.memory:
                print(f"  Latest memory: {agent.memory[-1]['content'][:100]}...")

if __name__ == "__main__":
    main()
