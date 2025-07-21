"""Enhanced workflow coordinator with feature request support"""
import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from utils.bmasterai_logging import get_logger, LogLevel, EventType
from agents.github_analyzer import GitHubAnalyzerAgent
from agents.feature_agent import FeatureAgent
from agents.pr_creator import PRCreatorAgent

class WorkflowCoordinator:
    """Enhanced coordinator for managing analysis and feature request workflows"""
    
    def __init__(self):
        self.logger = get_logger()
        self.github_analyzer = GitHubAnalyzerAgent()
        self.feature_agent = FeatureAgent()
        self.pr_creator = PRCreatorAgent()
        
    async def execute_full_workflow(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full analysis workflow (security and bugs focused)"""
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.log_event(
                agent_id="workflow_coordinator",
                event_type=EventType.TASK_START,
                message=f"Starting analysis workflow {workflow_id}",
                metadata={"config": config, "workflow_id": workflow_id}
            )
            
            # Step 1: Repository Analysis
            analysis_result = await self.github_analyzer.analyze_repository(
                config["repo_url"],
                analysis_type=config.get("analysis_type", "comprehensive")
            )
            
            if not analysis_result.get("success"):
                return {
                    "success": False,
                    "error": f"Repository analysis failed: {analysis_result.get('error')}",
                    "workflow_id": workflow_id
                }
            
            # Step 2: Process suggestions (security and bug fixes)
            processed_suggestions = await self._process_security_suggestions(
                analysis_result["result"]
            )
            
            # Step 3: Create PR if requested
            pr_result = None
            if config.get("create_pr", False):
                pr_result = await self.pr_creator.create_improvement_pr(
                    config["repo_url"],
                    processed_suggestions["implementable_suggestions"],
                    analysis_result["result"]
                )
            
            # Calculate workflow summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            summary = self._generate_workflow_summary(
                analysis_result["result"],
                processed_suggestions,
                pr_result,
                duration
            )
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "duration_seconds": duration,
                "steps": {
                    "analysis": analysis_result,
                    "processed_suggestions": processed_suggestions,
                    "pr_creation": pr_result
                },
                "summary": summary
            }
            
        except Exception as e:
            self.logger.log_event(
                agent_id="workflow_coordinator",
                event_type=EventType.TASK_ERROR,
                message=f"Workflow {workflow_id} failed: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e), "workflow_id": workflow_id}
            )
            
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id
            }
    
    async def execute_feature_request(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute feature request workflow with branch creation and code generation"""
        workflow_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.log_event(
                agent_id="workflow_coordinator",
                event_type=EventType.TASK_START,
                message=f"Starting feature request workflow {workflow_id}",
                metadata={"config": config, "workflow_id": workflow_id}
            )
            
            # Step 1: Analyze repository structure
            repo_analysis = await self.github_analyzer.analyze_repository(
                config["repo_url"],
                analysis_type="structure"
            )
            
            if not repo_analysis.get("success"):
                return {
                    "success": False,
                    "error": f"Repository analysis failed: {repo_analysis.get('error')}",
                    "workflow_id": workflow_id
                }
            
            # Step 2: Implement feature using FeatureAgent
            # Map parameters to match FeatureAgent expectations
            feature_config = {
                "repo_url": config["repo_url"],
                "feature_prompt": config["feature_description"],  # Map description to prompt
                "feature_branch": config.get("feature_branch_name"),  # Map branch_name to branch
                "base_branch": config.get("base_branch", "main"),
                "create_pr": config.get("create_pr", True),
                "include_tests": config.get("include_tests", True),
                "include_docs": config.get("include_docs", True),
                "complexity_level": config.get("complexity_level", "moderate"),
                "code_style": config.get("code_style", "auto-detect"),
                "review_before_commit": config.get("review_before_commit", False)
            }
            
            feature_implementation = await self.feature_agent.implement_feature(feature_config)
            
            if not feature_implementation.get("success"):
                return {
                    "success": False,
                    "error": f"Feature implementation failed: {feature_implementation.get('error')}",
                    "workflow_id": workflow_id
                }
            
            # Calculate workflow summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Extract results from feature implementation
            feature_result = feature_implementation  # FeatureAgent returns result directly, not nested
            
            summary = self._generate_feature_summary(
                feature_result,
                duration
            )
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "duration_seconds": duration,
                "branch_created": feature_result.get("branch_created", False),
                "branch_name": feature_result.get("feature_branch", ""),
                "files_modified": len(feature_result.get("files_modified", [])),
                "pr_created": feature_result.get("pr_created", False),
                "implementation_details": {
                    "branch_name": feature_result.get("feature_branch", ""),
                    "files_changed": [
                        {"path": f, "type": "modified"}
                        for f in feature_result.get("files_modified", [])
                    ],
                    "pr_url": feature_result.get("pr_url"),
                    "pr_description": None  # FeatureAgent doesn't provide PR description in this format
                },
                "steps": {
                    "repository_analysis": repo_analysis,
                    "feature_implementation": feature_implementation
                },
                "summary": summary
            }
            
        except Exception as e:
            self.logger.log_event(
                agent_id="workflow_coordinator",
                event_type=EventType.TASK_ERROR,
                message=f"Feature request workflow {workflow_id} failed: {str(e)}",
                level=LogLevel.ERROR,
                metadata={"error": str(e), "workflow_id": workflow_id}
            )
            
            return {
                "success": False,
                "error": str(e),
                "workflow_id": workflow_id
            }
    

    async def _process_security_suggestions(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Process suggestions focusing on security and bug fixes"""
        try:
            suggestions = analysis_result.get("improvement_suggestions", {}).get("suggestions", [])
            
            # Filter for security and bug-related suggestions
            security_suggestions = [
                s for s in suggestions 
                if any(keyword in s.get("category", "").lower() or keyword in s.get("description", "").lower()
                      for keyword in ["security", "vulnerability", "bug", "error", "fix", "safety"])
            ]
            
            # Categorize suggestions
            implementable = [s for s in security_suggestions if s.get("implementable", False)]
            manual = [s for s in security_suggestions if not s.get("implementable", False)]
            
            return {
                "success": True,
                "total_suggestions": len(suggestions),
                "security_suggestions": len(security_suggestions),
                "implementable_suggestions": implementable,
                "manual_suggestions": manual
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_workflow_summary(self, analysis_result: Dict[str, Any], 
                                 processed_suggestions: Dict[str, Any],
                                 pr_result: Optional[Dict[str, Any]], 
                                 duration: float) -> Dict[str, Any]:
        """Generate workflow summary for analysis"""
        try:
            return {
                "workflow_status": "completed",
                "analysis_performed": True,
                "pr_created": pr_result is not None and pr_result.get("success", False),
                "duration_seconds": duration,
                "metrics": {
                    "overall_score": analysis_result.get("code_analysis", {}).get("quality_score", 0),
                    "security_score": analysis_result.get("security_analysis", {}).get("score", 0),
                    "suggestions_count": processed_suggestions.get("total_suggestions", 0),
                    "security_suggestions": processed_suggestions.get("security_suggestions", 0)
                },
                "outcomes": [
                    f"Analyzed repository for security vulnerabilities and bugs",
                    f"Found {processed_suggestions.get('security_suggestions', 0)} security-related issues",
                    f"Generated {processed_suggestions.get('total_suggestions', 0)} improvement suggestions",
                    "Created pull request with fixes" if pr_result and pr_result.get("success") else "Analysis completed without PR creation"
                ],
                "recommendations": [
                    "Review and address high-priority security issues first",
                    "Implement automated security scanning in CI/CD pipeline",
                    "Regular code quality reviews to prevent future issues"
                ],
                "next_steps": [
                    "Review the generated security analysis report",
                    "Prioritize and implement suggested security fixes",
                    "Test all changes thoroughly before deployment",
                    "Consider setting up automated security monitoring"
                ]
            }
        except Exception as e:
            return {"workflow_status": "error", "error": str(e)}
    
    def _generate_feature_summary(self, feature_result: Dict[str, Any],
                                duration: float) -> Dict[str, Any]:
        """Generate workflow summary for feature request"""
        try:
            return {
                "workflow_status": "completed",
                "feature_implemented": feature_result.get("success", False),
                "pr_created": feature_result.get("pr_created", False),
                "duration_seconds": duration,
                "metrics": {
                    "files_modified": len(feature_result.get("files_modified", [])),
                    "branch_created": feature_result.get("branch_created", False),
                    "implementation_confidence": 0.8
                },
                "outcomes": [
                    f"Successfully created feature branch: {feature_result.get('feature_branch', 'N/A')}",
                    f"Generated and applied code changes to {len(feature_result.get('files_modified', []))} files",
                    "Implemented feature successfully",
                    "Created pull request for review" if feature_result.get("pr_created") else "Feature implemented without PR creation"
                ],
                "recommendations": [
                    "Review the generated code for quality and correctness",
                    "Test the feature thoroughly in a development environment",
                    "Consider adding unit tests for the new functionality",
                    "Update documentation to reflect the new feature"
                ],
                "next_steps": [
                    "Review the feature branch and generated code",
                    "Run tests to ensure functionality works as expected",
                    "Merge the pull request when ready",
                    "Deploy and monitor the new feature"
                ]
            }
        except Exception as e:
            return {"workflow_status": "error", "error": str(e)}

# Global coordinator instance
_coordinator = None

def get_workflow_coordinator() -> WorkflowCoordinator:
    """Get the global workflow coordinator instance"""
    global _coordinator
    if _coordinator is None:
        _coordinator = WorkflowCoordinator()
    return _coordinator
