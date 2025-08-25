"""
BMasterAI Reasoning Logger

This module provides utilities for capturing and logging LLM thinking processes,
reasoning chains, and decision points in a structured way.
"""

import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

from .logging import get_logger, LogLevel, EventType
from .monitoring import get_monitor


@dataclass
class ReasoningStep:
    """Represents a single step in the reasoning process"""
    step_number: int
    content: str
    timestamp: datetime
    step_type: str = "thinking"  # thinking, decision, conclusion
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ReasoningSession:
    """
    Context manager for capturing a complete LLM reasoning session
    
    Usage:
        with ReasoningSession("agent-001", "Analyze user request", "gpt-4") as session:
            session.think("First, I need to understand what the user wants...")
            session.decide("Approach selection", ["option1", "option2"], "option1", 
                          "Option 1 is better because...")
            session.conclude("Based on my analysis, the answer is...")
    """
    
    def __init__(self, agent_id: str, task_description: str, model: str, 
                 metadata: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.task_description = task_description
        self.model = model
        self.metadata = metadata or {}
        
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        self.session_id = ""
        self.steps: List[ReasoningStep] = []
        self.start_time = None
        self.decision_count = 0
        
    def __enter__(self):
        self.start_time = time.time()
        self.session_id = self.logger.log_llm_reasoning_start(
            self.agent_id, self.task_description, self.model, self.metadata
        )
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:  # No exception occurred
            duration_ms = (time.time() - self.start_time) * 1000
            
            # Log the complete reasoning chain
            thinking_chain = [step.content for step in self.steps]
            final_conclusion = thinking_chain[-1] if thinking_chain else "No conclusion reached"
            
            self.logger.log_reasoning_chain(
                self.agent_id, thinking_chain, final_conclusion, 
                self.session_id, self.metadata
            )
            
            # Track metrics
            self.monitor.track_reasoning_session(
                self.agent_id, self.session_id, len(self.steps),
                duration_ms, self.decision_count
            )
    
    def think(self, content: str, confidence: Optional[float] = None,
              metadata: Optional[Dict[str, Any]] = None) -> 'ReasoningSession':
        """Log a thinking step"""
        step_number = len(self.steps) + 1
        step = ReasoningStep(
            step_number=step_number,
            content=content,
            timestamp=datetime.now(),
            step_type="thinking",
            confidence=confidence,
            metadata=metadata
        )
        self.steps.append(step)
        
        self.logger.log_thinking_step(
            self.agent_id, step_number, content, 
            self.session_id, metadata
        )
        return self
    
    def decide(self, decision_description: str, options: List[str], 
              chosen_option: str, reasoning: str,
              confidence: Optional[float] = None,
              metadata: Optional[Dict[str, Any]] = None) -> 'ReasoningSession':
        """Log a decision point"""
        step_number = len(self.steps) + 1
        self.decision_count += 1
        
        decision_content = f"Decision: {decision_description} -> {chosen_option}. Reasoning: {reasoning}"
        step = ReasoningStep(
            step_number=step_number,
            content=decision_content,
            timestamp=datetime.now(),
            step_type="decision",
            confidence=confidence,
            metadata=metadata
        )
        self.steps.append(step)
        
        self.logger.log_decision_point(
            self.agent_id, decision_description, options, chosen_option,
            reasoning, self.session_id, step_number, metadata
        )
        return self
    
    def conclude(self, conclusion: str, confidence: Optional[float] = None,
                metadata: Optional[Dict[str, Any]] = None) -> 'ReasoningSession':
        """Log the final conclusion"""
        step_number = len(self.steps) + 1
        step = ReasoningStep(
            step_number=step_number,
            content=conclusion,
            timestamp=datetime.now(),
            step_type="conclusion",
            confidence=confidence,
            metadata=metadata
        )
        self.steps.append(step)
        
        self.logger.log_thinking_step(
            self.agent_id, step_number, f"Conclusion: {conclusion}",
            self.session_id, metadata
        )
        return self


def with_reasoning_logging(task_description: str, model: str = "unknown"):
    """
    Decorator for automatically logging LLM reasoning in functions
    
    Usage:
        @with_reasoning_logging("Process user query", "gpt-4")
        def my_llm_function(agent_id: str, query: str):
            # Your LLM logic here
            # The decorator will automatically create a reasoning session
            pass
    """
    def decorator(func: Callable):
        def wrapper(agent_id: str, *args, **kwargs):
            with ReasoningSession(agent_id, task_description, model) as session:
                # Store session in kwargs for function access
                kwargs['reasoning_session'] = session
                return func(agent_id, *args, **kwargs)
        return wrapper
    return decorator


class ChainOfThought:
    """
    Utility class for implementing chain-of-thought reasoning with automatic logging
    
    Usage:
        cot = ChainOfThought("agent-001", "Solve math problem", "gpt-4")
        cot.step("First, I identify the problem type...")
        cot.step("Next, I apply the relevant formula...")
        result = cot.conclude("Therefore, the answer is 42")
    """
    
    def __init__(self, agent_id: str, task_description: str, model: str,
                 auto_log: bool = True):
        self.agent_id = agent_id
        self.task_description = task_description
        self.model = model
        self.auto_log = auto_log
        
        self.steps: List[str] = []
        self.session: Optional[ReasoningSession] = None
        
        if auto_log:
            self.session = ReasoningSession(agent_id, task_description, model)
            self.session.__enter__()
    
    def step(self, thought: str, confidence: Optional[float] = None) -> 'ChainOfThought':
        """Add a thinking step to the chain"""
        self.steps.append(thought)
        
        if self.session:
            self.session.think(thought, confidence)
        
        return self
    
    def decide(self, description: str, options: List[str], choice: str,
              reasoning: str, confidence: Optional[float] = None) -> 'ChainOfThought':
        """Add a decision step to the chain"""
        decision_text = f"Decision: {description} -> {choice}"
        self.steps.append(decision_text)
        
        if self.session:
            self.session.decide(description, options, choice, reasoning, confidence)
        
        return self
    
    def conclude(self, conclusion: str, confidence: Optional[float] = None) -> str:
        """Finalize the chain of thought and return the conclusion"""
        self.steps.append(f"Conclusion: {conclusion}")
        
        if self.session:
            self.session.conclude(conclusion, confidence)
            self.session.__exit__(None, None, None)
        
        return conclusion
    
    def get_full_chain(self) -> List[str]:
        """Get the complete chain of thought"""
        return self.steps.copy()
    
    def get_formatted_chain(self) -> str:
        """Get the chain formatted as a readable string"""
        formatted = f"# Chain of Thought: {self.task_description}\n\n"
        for i, step in enumerate(self.steps, 1):
            formatted += f"**Step {i}:** {step}\n\n"
        return formatted


# Convenience function for quick reasoning logging
def log_reasoning(agent_id: str, task_description: str, thinking_steps: List[str],
                 final_conclusion: str, model: str = "unknown",
                 metadata: Optional[Dict[str, Any]] = None):
    """
    Quickly log a complete reasoning chain
    
    Usage:
        log_reasoning(
            "agent-001",
            "Analyze sentiment",
            ["First, I examine the word choice...", "The tone appears positive..."],
            "This text has positive sentiment",
            "gpt-4"
        )
    """
    logger = get_logger()
    monitor = get_monitor()
    
    session_id = logger.log_llm_reasoning_start(
        agent_id, task_description, model, metadata
    )
    
    # Log each thinking step
    for i, step in enumerate(thinking_steps, 1):
        logger.log_thinking_step(agent_id, i, step, session_id)
    
    # Log final reasoning chain
    logger.log_reasoning_chain(
        agent_id, thinking_steps, final_conclusion, session_id, metadata
    )
    
    # Track metrics
    monitor.track_reasoning_session(
        agent_id, session_id, len(thinking_steps), 0, 0
    )
    
    return session_id