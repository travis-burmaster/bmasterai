
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import json

from utils.gemini_base import BaseAgent, BaseTool


class WorkflowStage(Enum):
    """Enumeration of research workflow stages"""
    INITIALIZATION = "initialization"
    SEARCH_PLANNING = "search_planning"
    INFORMATION_GATHERING = "information_gathering"
    SYNTHESIS = "synthesis"
    EDITING = "editing"
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    ERROR = "error"


class ResearchTask:
    """Represents a research task with metadata and progress tracking"""
    
    def __init__(self, task_id: str, query: str, requirements: Dict[str, Any]):
        self.task_id = task_id
        self.query = query
        self.requirements = requirements
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.stage = WorkflowStage.INITIALIZATION
        self.progress = 0.0
        self.results = {}
        self.errors = []
        self.agent_outputs = {}
        
    def update_progress(self, stage: WorkflowStage, progress: float, results: Dict = None):
        """Update task progress and stage"""
        self.stage = stage
        self.progress = progress
        self.updated_at = datetime.now()
        if results:
            self.results.update(results)
    
    def add_agent_output(self, agent_name: str, output: Any):
        """Add output from a specific agent"""
        self.agent_outputs[agent_name] = {
            'output': output,
            'timestamp': datetime.now()
        }
    
    def add_error(self, error: str, agent_name: str = None):
        """Add error to task tracking"""
        self.errors.append({
            'error': error,
            'agent': agent_name,
            'timestamp': datetime.now()
        })
        self.stage = WorkflowStage.ERROR


class ResearchCoordinator(BaseAgent):
    """
    Coordinator agent that orchestrates the research workflow.
    Manages specialized agents and coordinates the research process.
    """
    
    def __init__(self, 
                 name: str = "ResearchCoordinator",
                 description: str = "Coordinates multi-agent research workflow",
                 **kwargs):
        super().__init__(name=name, description=description, **kwargs)
        
        self.logger = logging.getLogger(__name__)
        self.active_tasks: Dict[str, ResearchTask] = {}
        self.agents: Dict[str, BaseAgent] = {}
        self.workflow_stages = list(WorkflowStage)
        self.progress_callbacks: List[Callable] = []
        
        # Workflow configuration
        self.stage_weights = {
            WorkflowStage.INITIALIZATION: 0.05,
            WorkflowStage.SEARCH_PLANNING: 0.10,
            WorkflowStage.INFORMATION_GATHERING: 0.40,
            WorkflowStage.SYNTHESIS: 0.30,
            WorkflowStage.EDITING: 0.10,
            WorkflowStage.FINALIZATION: 0.05
        }
    
    def register_agent(self, agent_type: str, agent: BaseAgent):
        """Register a specialized agent with the coordinator"""
        self.agents[agent_type] = agent
        self.logger.info(f"Registered {agent_type} agent: {agent.name}")
    
    def add_progress_callback(self, callback: Callable):
        """Add callback function for progress updates"""
        self.progress_callbacks.append(callback)
    
    def _notify_progress(self, task_id: str, stage: WorkflowStage, progress: float, message: str = ""):
        """Notify all registered callbacks about progress updates"""
        for callback in self.progress_callbacks:
            try:
                callback(task_id, stage.value, progress, message)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")
    
    async def start_research_task(self, 
                                query: str, 
                                requirements: Dict[str, Any] = None,
                                task_id: str = None) -> str:
        """
        Start a new research task
        
        Args:
            query: Research query/topic
            requirements: Additional requirements and parameters
            task_id: Optional custom task ID
            
        Returns:
            Task ID for tracking
        """
        if task_id is None:
            task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if requirements is None:
            requirements = {}
        
        # Create new research task
        task = ResearchTask(task_id, query, requirements)
        self.active_tasks[task_id] = task
        
        self.logger.info(f"Started research task {task_id}: {query}")
        self._notify_progress(task_id, WorkflowStage.INITIALIZATION, 0.0, "Task initialized")
        
        # Start the research workflow asynchronously
        asyncio.create_task(self._execute_research_workflow(task_id))
        
        return task_id
    
    async def _execute_research_workflow(self, task_id: str):
        """Execute the complete research workflow for a task"""
        task = self.active_tasks.get(task_id)
        if not task:
            self.logger.error(f"Task {task_id} not found")
            return
        
        try:
            # Stage 1: Search Planning
            await self._execute_search_planning(task)
            
            # Stage 2: Information Gathering
            await self._execute_information_gathering(task)
            
            # Stage 3: Synthesis
            await self._execute_synthesis(task)
            
            # Stage 4: Editing
            await self._execute_editing(task)
            
            # Stage 5: Finalization
            await self._execute_finalization(task)
            
            # Mark as completed
            task.update_progress(WorkflowStage.COMPLETED, 1.0)
            self._notify_progress(task_id, WorkflowStage.COMPLETED, 1.0, "Research completed successfully")
            
        except Exception as e:
            error_msg = f"Workflow error: {str(e)}"
            task.add_error(error_msg, "ResearchCoordinator")
            self.logger.error(f"Error in research workflow for task {task_id}: {e}")
            self._notify_progress(task_id, WorkflowStage.ERROR, task.progress, error_msg)
    
    async def _execute_search_planning(self, task: ResearchTask):
        """Execute search planning stage"""
        stage = WorkflowStage.SEARCH_PLANNING
        self.logger.info(f"Starting {stage.value} for task {task.task_id}")
        
        search_agent = self.agents.get('search')
        if not search_agent:
            raise ValueError("Search agent not registered")
        
        # Generate search plan
        planning_prompt = f"""
        Create a comprehensive search plan for the research query: "{task.query}"
        
        Requirements: {json.dumps(task.requirements, indent=2)}
        
        Generate:
        1. List of key search terms and phrases
        2. Different angles and perspectives to explore
        3. Specific questions that need to be answered
        4. Priority order for information gathering
        
        Format the response as a structured plan.
        """
        
        try:
            search_plan = await search_agent.process(planning_prompt)
            task.add_agent_output('search_planning', search_plan)
            
            progress = self.stage_weights[stage]
            task.update_progress(stage, progress)
            self._notify_progress(task.task_id, stage, progress, "Search plan created")
            
        except Exception as e:
            raise Exception(f"Search planning failed: {str(e)}")
    
    async def _execute_information_gathering(self, task: ResearchTask):
        """Execute information gathering stage"""
        stage = WorkflowStage.INFORMATION_GATHERING
        self.logger.info(f"Starting {stage.value} for task {task.task_id}")
        
        search_agent = self.agents.get('search')
        if not search_agent:
            raise ValueError("Search agent not registered")
        
        search_plan = task.agent_outputs.get('search_planning', {}).get('output', '')
        
        # Execute searches based on the plan
        search_prompt = f"""
        Execute comprehensive research based on this search plan:
        {search_plan}
        
        Original query: "{task.query}"
        Requirements: {json.dumps(task.requirements, indent=2)}
        
        Gather detailed information from multiple sources and perspectives.
        Provide comprehensive, well-sourced information.
        """
        
        try:
            search_results = await search_agent.process(
                search_prompt, 
                research_mode=True,
                depth=task.requirements.get('depth', 'medium')
            )
            task.add_agent_output('information_gathering', search_results)
            
            progress = sum(self.stage_weights[s] for s in [WorkflowStage.INITIALIZATION, WorkflowStage.SEARCH_PLANNING, WorkflowStage.INFORMATION_GATHERING])
            task.update_progress(stage, progress)
            self._notify_progress(task.task_id, stage, progress, "Information gathering completed")
            
        except Exception as e:
            raise Exception(f"Information gathering failed: {str(e)}")
    
    async def _execute_synthesis(self, task: ResearchTask):
        """Execute synthesis stage"""
        stage = WorkflowStage.SYNTHESIS
        self.logger.info(f"Starting {stage.value} for task {task.task_id}")
        
        synthesis_agent = self.agents.get('synthesis')
        if not synthesis_agent:
            raise ValueError("Synthesis agent not registered")
        
        gathered_info = task.agent_outputs.get('information_gathering', {}).get('output', '')
        
        synthesis_prompt = f"""
        Analyze and synthesize the following research information:
        
        {gathered_info}
        
        Original query: "{task.query}"
        Requirements: {json.dumps(task.requirements, indent=2)}
        
        Create a comprehensive synthesis that:
        1. Identifies key themes and patterns
        2. Analyzes different perspectives
        3. Draws meaningful insights
        4. Structures information logically
        5. Highlights important findings
        """
        
        try:
            synthesis_results = await synthesis_agent.process(synthesis_prompt)
            task.add_agent_output('synthesis', synthesis_results)
            
            progress = sum(self.stage_weights[s] for s in [WorkflowStage.INITIALIZATION, WorkflowStage.SEARCH_PLANNING, WorkflowStage.INFORMATION_GATHERING, WorkflowStage.SYNTHESIS])
            task.update_progress(stage, progress)
            self._notify_progress(task.task_id, stage, progress, "Synthesis completed")
            
        except Exception as e:
            raise Exception(f"Synthesis failed: {str(e)}")
    
    async def _execute_editing(self, task: ResearchTask):
        """Execute editing stage"""
        stage = WorkflowStage.EDITING
        self.logger.info(f"Starting {stage.value} for task {task.task_id}")
        
        editing_agent = self.agents.get('editing')
        if not editing_agent:
            raise ValueError("Editing agent not registered")
        
        synthesis_output = task.agent_outputs.get('synthesis', {}).get('output', '')
        
        editing_prompt = f"""
        Edit and refine the following research synthesis:
        
        {synthesis_output}
        
        Original query: "{task.query}"
        Requirements: {json.dumps(task.requirements, indent=2)}
        
        Ensure:
        1. Clear and engaging writing
        2. Logical flow and structure
        3. Proper formatting
        4. Consistency in style
        5. Professional presentation
        """
        
        try:
            edited_content = await editing_agent.process(editing_prompt)
            task.add_agent_output('editing', edited_content)
            
            progress = sum(self.stage_weights[s] for s in [WorkflowStage.INITIALIZATION, WorkflowStage.SEARCH_PLANNING, WorkflowStage.INFORMATION_GATHERING, WorkflowStage.SYNTHESIS, WorkflowStage.EDITING])
            task.update_progress(stage, progress)
            self._notify_progress(task.task_id, stage, progress, "Editing completed")
            
        except Exception as e:
            raise Exception(f"Editing failed: {str(e)}")
    
    async def _execute_finalization(self, task: ResearchTask):
        """Execute finalization stage"""
        stage = WorkflowStage.FINALIZATION
        self.logger.info(f"Starting {stage.value} for task {task.task_id}")
        
        edited_content = task.agent_outputs.get('editing', {}).get('output', '')
        
        # Create final report structure
        final_report = {
            'query': task.query,
            'requirements': task.requirements,
            'content': edited_content,
            'metadata': {
                'task_id': task.task_id,
                'created_at': task.created_at.isoformat(),
                'completed_at': datetime.now().isoformat(),
                'agents_used': list(task.agent_outputs.keys())
            }
        }
        
        task.results['final_report'] = final_report
        
        progress = 0.95  # Almost complete
        task.update_progress(stage, progress)
        self._notify_progress(task.task_id, stage, progress, "Report finalized")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a research task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'query': task.query,
            'stage': task.stage.value,
            'progress': task.progress,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'errors': task.errors,
            'agent_outputs': {k: v['timestamp'].isoformat() for k, v in task.agent_outputs.items()}
        }
    
    def get_task_results(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get results of a completed research task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        return task.results
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get status of all tasks"""
        return [self.get_task_status(task_id) for task_id in self.active_tasks.keys()]
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running research task"""
        task = self.active_tasks.get(task_id)
        if not task:
            return False
        
        task.add_error("Task cancelled by user", "ResearchCoordinator")
        self.logger.info(f"Cancelled task {task_id}")
        return True
    
    def cleanup_completed_tasks(self, max_age_hours: int = 24):
        """Clean up old completed tasks"""
        current_time = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.active_tasks.items():
            if task.stage in [WorkflowStage.COMPLETED, WorkflowStage.ERROR]:
                age_hours = (current_time - task.updated_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.active_tasks[task_id]
            self.logger.info(f"Cleaned up old task {task_id}")
        
        return len(tasks_to_remove)
    
    async def process(self, input_data: str, **kwargs) -> str:
        """
        Process method for BaseAgent compatibility
        Starts a research task and returns the task ID
        """
        requirements = kwargs.get('requirements', {})
        task_id = await self.start_research_task(input_data, requirements)
        return f"Started research task: {task_id}"
