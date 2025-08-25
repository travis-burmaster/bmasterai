"""
BMasterAI Reasoning Logging Example

This example demonstrates how to use BMasterAI's enhanced logging system
to capture LLM thinking processes, reasoning chains, and decision points.
"""

import time
import json
from typing import Dict, List, Any

# Import BMasterAI components
from bmasterai import (
    configure_logging, get_logger, get_monitor,
    ReasoningSession, ChainOfThought, with_reasoning_logging, log_reasoning,
    LogLevel
)


class ReasoningAgent:
    """
    Example agent that demonstrates various reasoning logging patterns
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        # Start monitoring
        self.monitor.start_monitoring()
    
    def analyze_sentiment_with_context_manager(self, text: str) -> str:
        """
        Analyze sentiment using ReasoningSession context manager
        This provides the most comprehensive logging of the reasoning process
        """
        with ReasoningSession(
            self.agent_id, 
            f"Analyze sentiment of text: '{text[:50]}...'", 
            "reasoning-model-v1",
            metadata={"text_length": len(text), "method": "context_manager"}
        ) as session:
            
            # Step 1: Initial analysis
            session.think(
                f"I need to analyze the sentiment of this text: '{text}'. "
                f"Let me start by examining the key words and phrases.",
                confidence=0.9
            )
            
            # Step 2: Word analysis
            positive_words = ["good", "great", "excellent", "amazing", "love"]
            negative_words = ["bad", "terrible", "hate", "awful", "horrible"]
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            session.think(
                f"I found {positive_count} positive words and {negative_count} negative words. "
                f"Positive words detected: {[w for w in positive_words if w in text_lower]}. "
                f"Negative words detected: {[w for w in negative_words if w in text_lower]}.",
                confidence=0.8
            )
            
            # Step 3: Decision point
            if positive_count > negative_count:
                sentiment = "positive"
                reasoning = f"More positive words ({positive_count}) than negative ({negative_count})"
            elif negative_count > positive_count:
                sentiment = "negative"
                reasoning = f"More negative words ({negative_count}) than positive ({positive_count})"
            else:
                sentiment = "neutral"
                reasoning = "Equal number of positive and negative words, or neither found"
            
            session.decide(
                "Sentiment classification",
                ["positive", "negative", "neutral"],
                sentiment,
                reasoning,
                confidence=0.85
            )
            
            # Step 4: Final conclusion
            final_result = f"The text has {sentiment} sentiment"
            session.conclude(final_result, confidence=0.9)
            
            return final_result
    
    def analyze_with_chain_of_thought(self, problem: str) -> str:
        """
        Solve a problem using ChainOfThought utility
        """
        cot = ChainOfThought(
            self.agent_id, 
            f"Solve problem: {problem}", 
            "reasoning-model-v1"
        )
        
        # Build reasoning chain step by step
        cot.step("First, I need to understand what type of problem this is.")
        cot.step(f"The problem is: '{problem}'. This appears to be a logical reasoning task.")
        
        # Add decision point
        if "calculate" in problem.lower() or any(op in problem for op in ['+', '-', '*', '/', '=']):
            approach = "mathematical"
            cot.decide(
                "Problem solving approach",
                ["mathematical", "logical", "creative"],
                approach,
                "The problem contains mathematical terms or operators"
            )
        else:
            approach = "logical"
            cot.decide(
                "Problem solving approach", 
                ["mathematical", "logical", "creative"],
                approach,
                "This appears to be a logical reasoning problem"
            )
        
        cot.step(f"Using {approach} approach to solve this problem.")
        cot.step("Applying relevant rules and checking for consistency.")
        
        # Return conclusion
        return cot.conclude(f"Based on {approach} reasoning, here's my analysis of the problem.")
    
    @with_reasoning_logging("Process user query", "gpt-4")
    def process_with_decorator(self, agent_id: str, query: str, reasoning_session=None) -> str:
        """
        Example function using the reasoning logging decorator
        """
        if reasoning_session:
            reasoning_session.think(f"Received query: {query}")
            reasoning_session.think("Determining the best approach to handle this query")
            
            if "?" in query:
                approach = "question_answering"
                reasoning_session.decide(
                    "Query type classification",
                    ["question_answering", "command_execution", "information_request"],
                    approach,
                    "Query contains question mark, treating as Q&A"
                )
            else:
                approach = "general_processing"
                reasoning_session.decide(
                    "Query type classification",
                    ["question_answering", "command_execution", "information_request"], 
                    approach,
                    "No specific indicators, using general processing"
                )
            
            result = f"Processed query using {approach} approach"
            reasoning_session.conclude(result)
            return result
        
        return "Processed without reasoning session"
    
    def quick_reasoning_example(self, task: str) -> str:
        """
        Example using the quick log_reasoning function
        """
        thinking_steps = [
            f"Task received: {task}",
            "Analyzing task requirements and constraints",
            "Identifying the most appropriate solution strategy", 
            "Considering potential edge cases and challenges",
            "Formulating the optimal approach"
        ]
        
        conclusion = f"Optimal approach identified for task: {task}"
        
        session_id = log_reasoning(
            self.agent_id,
            f"Quick analysis of task: {task}",
            thinking_steps,
            conclusion,
            "quick-reasoning-v1",
            metadata={"task_type": "analysis", "complexity": "medium"}
        )
        
        return f"Analysis complete (session: {session_id})"
    
    def export_reasoning_logs(self, format_type: str = "markdown") -> str:
        """Export reasoning logs for this agent"""
        return self.logger.export_reasoning_logs(
            agent_id=self.agent_id,
            output_format=format_type
        )


def main():
    """
    Demonstrate various reasoning logging capabilities
    """
    print("🧠 BMasterAI Reasoning Logging Example")
    print("=" * 50)
    
    # Configure logging with reasoning enabled
    logger = configure_logging(
        log_level=LogLevel.DEBUG,
        enable_console=True,
        enable_reasoning_logs=True,
        reasoning_log_file="example_reasoning.jsonl"
    )
    
    # Create reasoning agent
    agent = ReasoningAgent("reasoning-agent-001")
    
    print("\n1. Sentiment Analysis with Context Manager")
    print("-" * 40)
    text = "This product is absolutely amazing! I love how great it works."
    result1 = agent.analyze_sentiment_with_context_manager(text)
    print(f"Result: {result1}")
    
    print("\n2. Problem Solving with Chain of Thought")
    print("-" * 40)
    problem = "If all cats are mammals and some mammals fly, can some cats fly?"
    result2 = agent.analyze_with_chain_of_thought(problem)
    print(f"Result: {result2}")
    
    print("\n3. Processing with Decorator")
    print("-" * 40)
    query = "What is the weather like today?"
    result3 = agent.process_with_decorator(agent.agent_id, query)
    print(f"Result: {result3}")
    
    print("\n4. Quick Reasoning Logging")
    print("-" * 40)
    task = "Optimize database query performance"
    result4 = agent.quick_reasoning_example(task)
    print(f"Result: {result4}")
    
    # Wait a moment for all logs to be written
    time.sleep(1)
    
    print("\n5. Export Reasoning Logs")
    print("-" * 40)
    
    # Export as markdown
    markdown_logs = agent.export_reasoning_logs("markdown")
    print("Markdown export (first 500 chars):")
    print(markdown_logs[:500] + "..." if len(markdown_logs) > 500 else markdown_logs)
    
    # Show some statistics
    print("\n6. Agent Statistics")
    print("-" * 40)
    stats = logger.get_agent_stats(agent.agent_id)
    print(f"Total events logged: {stats['total_events']}")
    print(f"Event breakdown:")
    for event_type, count in stats['event_types'].items():
        print(f"  - {event_type}: {count}")
    
    # Show reasoning-specific metrics
    monitor = agent.monitor
    reasoning_steps_stats = monitor.metrics_collector.get_metric_stats('reasoning_session_steps', 10)
    if reasoning_steps_stats:
        print(f"\nReasoning session statistics:")
        print(f"  - Average steps per session: {reasoning_steps_stats.get('avg', 0):.1f}")
        print(f"  - Max steps in a session: {reasoning_steps_stats.get('max', 0)}")
    
    print(f"\n✅ Example completed! Check the logs directory for detailed reasoning logs.")
    print(f"Main log: logs/bmasterai.jsonl")
    print(f"Reasoning log: logs/reasoning/example_reasoning.jsonl")


if __name__ == "__main__":
    main()