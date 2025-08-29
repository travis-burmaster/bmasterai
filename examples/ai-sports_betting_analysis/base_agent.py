"""
Base Agent Framework for Sports Betting Analysis System

This module provides the base class and common functionality for all agents
in the sports betting analysis multi-agent system.
"""

import os
import time
import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field

# BMasterAI Logging Integration
try:
    from bmasterai.logging import BMasterLogger, LogLevel, EventType
    BMASTERAI_AVAILABLE = True
except ImportError:
    import logging
    BMASTERAI_AVAILABLE = False
    print("BMasterAI not available, using standard logging")

# Agno imports
from agno.agent import Agent
from agno.models.google import Gemini

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


class AgentResult(BaseModel):
    """Standard result format for all agents"""
    agent_id: str = Field(description="Unique identifier for the agent")
    success: bool = Field(description="Whether the agent completed successfully")
    data: Dict[str, Any] = Field(description="Agent output data")
    confidence: float = Field(description="Confidence level (0.0 to 1.0)")
    processing_time: float = Field(description="Time taken to process in seconds")
    timestamp: datetime = Field(description="When the result was generated")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseAgent(ABC):
    """
    Base class for all agents in the sports betting analysis system.
    
    Provides common functionality including:
    - BMasterAI logging integration
    - Error handling and retry mechanisms
    - Result standardization
    - Performance monitoring
    """
    
    def __init__(self, agent_id: str, google_api_key: Optional[str] = None):
        self.agent_id = agent_id
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        # Initialize BMasterAI Logger
        if BMASTERAI_AVAILABLE:
            self.logger = BMasterLogger(
                log_file=f"{agent_id}.log",
                json_log_file=f"{agent_id}.json",
                log_level=LogLevel.INFO,
                enable_console=True,
                enable_file=True,
                enable_json=True
            )
        else:
            # Fallback to standard logging
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(agent_id)
        
        # Initialize Gemini agent if API key is available
        if self.google_api_key:
            self.gemini_agent = Agent(
                model=Gemini(id="gemini-1.5-flash", api_key=self.google_api_key),
                markdown=True,
                description=f"I am {agent_id} specialized in sports betting analysis."
            )
        else:
            self.gemini_agent = None
            
        self.start_time = None
        self.processing_stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "average_processing_time": 0.0,
            "last_run_time": None
        }
    
    def log_event(self, event_type: str, message: str, level: str = "INFO", 
                  metadata: Optional[Dict[str, Any]] = None):
        """Log an event using BMasterAI logging or fallback logging"""
        if BMASTERAI_AVAILABLE:
            event_type_enum = getattr(EventType, event_type.upper(), EventType.TASK_UPDATE)
            level_enum = getattr(LogLevel, level.upper(), LogLevel.INFO)
            
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=event_type_enum,
                message=message,
                level=level_enum,
                metadata=metadata or {}
            )
        else:
            log_level = getattr(logging, level.upper(), logging.INFO)
            self.logger.log(log_level, f"{self.agent_id}: {message}")
    
    def start_task(self, task_description: str, metadata: Optional[Dict[str, Any]] = None):
        """Start a new task and log the beginning"""
        self.start_time = time.time()
        task_id = f"{self.agent_id}_{int(self.start_time)}"
        
        self.log_event(
            event_type="TASK_START",
            message=f"Starting {task_description}",
            metadata={
                "task_id": task_id,
                "task_description": task_description,
                **(metadata or {})
            }
        )
        
        return task_id
    
    def complete_task(self, task_id: str, success: bool, result_data: Dict[str, Any],
                     confidence: float = 1.0, error_message: Optional[str] = None):
        """Complete a task and log the result"""
        processing_time = time.time() - (self.start_time or time.time())
        
        # Update processing stats
        self.processing_stats["total_runs"] += 1
        if success:
            self.processing_stats["successful_runs"] += 1
        
        # Calculate average processing time
        if self.processing_stats["total_runs"] > 0:
            old_avg = self.processing_stats["average_processing_time"]
            new_avg = ((old_avg * (self.processing_stats["total_runs"] - 1)) + processing_time) / self.processing_stats["total_runs"]
            self.processing_stats["average_processing_time"] = new_avg
        
        self.processing_stats["last_run_time"] = datetime.now()
        
        # Log completion
        event_type = "TASK_COMPLETE" if success else "TASK_ERROR"
        message = f"Task completed successfully" if success else f"Task failed: {error_message}"
        
        self.log_event(
            event_type=event_type,
            message=message,
            level="INFO" if success else "ERROR",
            metadata={
                "task_id": task_id,
                "processing_time_ms": processing_time * 1000,
                "confidence": confidence,
                "success": success
            }
        )
        
        # Create standardized result
        return AgentResult(
            agent_id=self.agent_id,
            success=success,
            data=result_data,
            confidence=confidence,
            processing_time=processing_time,
            timestamp=datetime.now(),
            error_message=error_message,
            metadata={
                "task_id": task_id,
                "processing_stats": self.processing_stats.copy()
            }
        )
    
    def log_thinking_step(self, step_type: str, reasoning: str, confidence: float = 1.0,
                         data: Optional[Dict[str, Any]] = None):
        """Log a thinking/reasoning step for transparency"""
        self.log_event(
            event_type="TASK_UPDATE",
            message=f"Thinking step: {step_type}",
            metadata={
                "step_type": step_type,
                "reasoning": reasoning,
                "confidence": confidence,
                "data": data or {}
            }
        )
    
    async def run_with_retry(self, max_retries: int = 3, retry_delay: float = 1.0) -> AgentResult:
        """Run the agent with retry logic"""
        last_error = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    self.log_event(
                        event_type="TASK_UPDATE",
                        message=f"Retry attempt {attempt + 1}/{max_retries}",
                        metadata={"attempt": attempt + 1, "max_retries": max_retries}
                    )
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                
                return await self.run_async()
                
            except Exception as e:
                last_error = str(e)
                self.log_event(
                    event_type="TASK_ERROR",
                    message=f"Attempt {attempt + 1} failed: {last_error}",
                    level="WARNING" if attempt < max_retries - 1 else "ERROR",
                    metadata={"attempt": attempt + 1, "error": last_error}
                )
                
                if attempt == max_retries - 1:
                    # Final attempt failed
                    return self.complete_task(
                        task_id=f"{self.agent_id}_failed_{int(time.time())}",
                        success=False,
                        result_data={},
                        confidence=0.0,
                        error_message=f"All {max_retries} attempts failed. Last error: {last_error}"
                    )
        
        # This should never be reached, but just in case
        return self.complete_task(
            task_id=f"{self.agent_id}_unknown_error_{int(time.time())}",
            success=False,
            result_data={},
            confidence=0.0,
            error_message="Unknown error in retry logic"
        )
    
    @abstractmethod
    async def run_async(self) -> AgentResult:
        """
        Abstract method that must be implemented by all concrete agents.
        This method should contain the main logic for the agent.
        """
        pass
    
    def run(self) -> AgentResult:
        """Synchronous wrapper for the async run method"""
        return asyncio.run(self.run_async())
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and statistics for the agent"""
        return {
            "agent_id": self.agent_id,
            "processing_stats": self.processing_stats.copy(),
            "is_configured": self.google_api_key is not None,
            "bmasterai_available": BMASTERAI_AVAILABLE,
            "last_activity": self.processing_stats.get("last_run_time")
        }


class CoordinationAgent(BaseAgent):
    """
    Coordination agent that manages the workflow between other agents
    and synthesizes their results into final recommendations.
    """
    
    def __init__(self):
        super().__init__("coordination_agent")
        self.registered_agents = {}
        self.workflow_results = {}
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent to be managed by the coordinator"""
        self.registered_agents[agent.agent_id] = agent
        self.log_event(
            event_type="TASK_UPDATE",
            message=f"Registered agent: {agent.agent_id}",
            metadata={"registered_agent": agent.agent_id}
        )
    
    async def run_workflow(self, game_data: Dict[str, Any]) -> AgentResult:
        """Run the complete analysis workflow with all registered agents"""
        task_id = self.start_task("Complete sports betting analysis workflow")
        
        try:
            self.log_thinking_step(
                step_type="workflow_start",
                reasoning=f"Starting analysis workflow for game: {game_data.get('game_id', 'unknown')}",
                data={"game_data": game_data}
            )
            
            # Run agents in parallel where possible
            results = {}
            
            # Phase 1: Data collection (must run first)
            if "data_collection_agent" in self.registered_agents:
                self.log_thinking_step(
                    step_type="data_collection",
                    reasoning="Collecting data from external sources"
                )
                data_agent = self.registered_agents["data_collection_agent"]
                data_result = await data_agent.run_async()
                results["data_collection"] = data_result
                
                if not data_result.success:
                    return self.complete_task(
                        task_id=task_id,
                        success=False,
                        result_data={"partial_results": results},
                        confidence=0.0,
                        error_message="Data collection failed"
                    )
            
            # Phase 2: Parallel analysis (statistical, market, news)
            analysis_tasks = []
            for agent_id in ["statistical_analysis_agent", "market_analysis_agent", "news_sentiment_agent"]:
                if agent_id in self.registered_agents:
                    agent = self.registered_agents[agent_id]
                    analysis_tasks.append(agent.run_async())
            
            if analysis_tasks:
                self.log_thinking_step(
                    step_type="parallel_analysis",
                    reasoning=f"Running {len(analysis_tasks)} analysis agents in parallel"
                )
                analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(analysis_results):
                    if isinstance(result, Exception):
                        self.log_event(
                            event_type="TASK_ERROR",
                            message=f"Analysis agent failed: {str(result)}",
                            level="WARNING"
                        )
                    else:
                        agent_name = ["statistical_analysis", "market_analysis", "news_sentiment"][i]
                        results[agent_name] = result
            
            # Phase 3: Probability calculation (must run after analysis)
            if "probability_calculation_agent" in self.registered_agents:
                self.log_thinking_step(
                    step_type="probability_calculation",
                    reasoning="Synthesizing analysis results into probability estimates"
                )
                prob_agent = self.registered_agents["probability_calculation_agent"]
                prob_result = await prob_agent.run_async()
                results["probability_calculation"] = prob_result
            
            # Calculate overall confidence based on successful agents
            successful_agents = sum(1 for r in results.values() if r.success)
            total_agents = len(results)
            overall_confidence = successful_agents / total_agents if total_agents > 0 else 0.0
            
            self.log_thinking_step(
                step_type="workflow_complete",
                reasoning=f"Workflow completed with {successful_agents}/{total_agents} agents successful",
                confidence=overall_confidence,
                data={"results_summary": {k: v.success for k, v in results.items()}}
            )
            
            return self.complete_task(
                task_id=task_id,
                success=True,
                result_data={
                    "agent_results": results,
                    "workflow_summary": {
                        "total_agents": total_agents,
                        "successful_agents": successful_agents,
                        "overall_confidence": overall_confidence
                    }
                },
                confidence=overall_confidence
            )
            
        except Exception as e:
            return self.complete_task(
                task_id=task_id,
                success=False,
                result_data={"partial_results": self.workflow_results},
                confidence=0.0,
                error_message=str(e)
            )
    
    async def run_async(self) -> AgentResult:
        """Default run method for coordination agent"""
        return await self.run_workflow({"game_id": "default_analysis"})

