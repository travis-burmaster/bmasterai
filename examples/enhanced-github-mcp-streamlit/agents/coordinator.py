
"""Multi-agent coordinator for orchestrating GitHub analysis workflow"""
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from utils.bmasterai_logging import get_logger, EventType, LogLevel
from utils.bmasterai_monitoring import get_monitor
from agents.github_analyzer import get_github_analyzer
from agents.pr_creator import get_pr_creator
from agents.feature_agent import get_feature_agent

class WorkflowCoordinator:
    """Coordinator agent for managing multi-agent GitHub analysis workflow"""
    
    def __init__(self, agent_id: str = "workflow_coordinator"):
        self.agent_id = agent_id
        self.agent_name = "Workflow Coordinator"
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        # Initialize sub-agents
        self.github_analyzer = get_github_analyzer()
        self.pr_creator = get_pr_creator()
        self.feature_agent = get_feature_agent()
        
        # Log coordinator initialization
        self.logger.log_agent_start(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            metadata={"initialized_at": time.time()}
        )
        
        # Track agent start in monitoring
        self.monitor.track_agent_start(self.agent_id)
    
    async def execute_full_workflow(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete GitHub analysis and PR creation workflow"""
        workflow_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log workflow start
        self.logger.log_task_start(
            agent_id=self.agent_id,
            task_name="full_workflow",
            task_id=workflow_id,
            metadata={
                "repo_url": config.get("repo_url"),
                "create_pr": config.get("create_pr", False),
                "analysis_type": config.get("analysis_type", "comprehensive")
            }
        )
        
        workflow_result = {
            "workflow_id": workflow_id,
            "repo_url": config.get("repo_url"),
            "config": config,
            "steps": {},
            "success": False,
            "error": None
        }
        
        try:
            # Step 1: Repository Analysis
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_COMMUNICATION,
                message="Starting repository analysis",
                metadata={"step": "analysis", "workflow_id": workflow_id}
            )
            
            analysis_result = await self.github_analyzer.analyze_repository(
                repo_url=config["repo_url"],
                analysis_type=config.get("analysis_type", "comprehensive")
            )
            
            workflow_result["steps"]["analysis"] = analysis_result
            
            if not analysis_result.get("success"):
                raise Exception(f"Repository analysis failed: {analysis_result.get('error')}")
            
            # Step 2: Filter and process suggestions
            suggestions = self._process_suggestions(
                analysis_result["result"].get("improvement_suggestions", {}),
                config
            )
            
            workflow_result["steps"]["processed_suggestions"] = suggestions
            
            # Step 3: Create Pull Request (if enabled and suggestions available)
            if config.get("create_pr", False) and suggestions.get("implementable_suggestions"):
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.AGENT_COMMUNICATION,
                    message="Creating improvement pull request",
                    metadata={"step": "pr_creation", "workflow_id": workflow_id}
                )
                
                pr_result = await self.pr_creator.create_improvement_pr(
                    repo_url=config["repo_url"],
                    suggestions=suggestions["implementable_suggestions"],
                    analysis_result=analysis_result["result"]
                )
                
                workflow_result["steps"]["pr_creation"] = pr_result
                
                if not pr_result.get("success"):
                    # Log warning but don't fail entire workflow
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=f"PR creation failed: {pr_result.get('error')}",
                        level=LogLevel.WARNING,
                        metadata={"workflow_id": workflow_id}
                    )
            
            # Step 4: Generate workflow summary
            workflow_summary = self._generate_workflow_summary(workflow_result)
            workflow_result["summary"] = workflow_summary
            
            # Mark workflow as successful
            workflow_result["success"] = True
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful completion
            self.logger.log_task_complete(
                agent_id=self.agent_id,
                task_name="full_workflow",
                task_id=workflow_id,
                duration_ms=duration_ms,
                metadata={
                    "repo_url": config["repo_url"],
                    "analysis_success": analysis_result.get("success", False),
                    "pr_created": "pr_creation" in workflow_result["steps"],
                    "suggestions_count": len(suggestions.get("implementable_suggestions", []))
                }
            )
            
            # Track performance metrics
            self.monitor.track_task_duration(self.agent_id, "full_workflow", duration_ms)
            
            return workflow_result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            workflow_result["error"] = str(e)
            workflow_result["success"] = False
            
            self.logger.log_task_error(
                agent_id=self.agent_id,
                task_name="full_workflow",
                task_id=workflow_id,
                error=str(e),
                duration_ms=duration_ms,
                metadata={"repo_url": config.get("repo_url")}
            )
            
            # Track error
            self.monitor.track_error(self.agent_id, "workflow_error")
            
            return workflow_result
    
    def _process_suggestions(self, suggestions_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process and filter suggestions based on configuration"""
        all_suggestions = suggestions_data.get("suggestions", [])
        
        # Filter by priority
        priority_filter = config.get("priority_filter", ["High", "Medium"])
        filtered_suggestions = [
            s for s in all_suggestions 
            if s.get("priority") in priority_filter
        ]
        
        # Limit number of suggestions
        max_suggestions = config.get("max_suggestions", 5)
        limited_suggestions = filtered_suggestions[:max_suggestions]
        
        # Separate implementable vs. manual suggestions
        implementable_categories = ["documentation", "security", "configuration"]
        
        implementable_suggestions = []
        manual_suggestions = []
        
        for suggestion in limited_suggestions:
            category = suggestion.get("category", "").lower()
            if any(impl_cat in category for impl_cat in implementable_categories):
                implementable_suggestions.append(suggestion)
            else:
                manual_suggestions.append(suggestion)
        
        return {
            "all_suggestions": all_suggestions,
            "filtered_suggestions": filtered_suggestions,
            "implementable_suggestions": implementable_suggestions,
            "manual_suggestions": manual_suggestions,
            "processing_info": {
                "total_suggestions": len(all_suggestions),
                "filtered_count": len(filtered_suggestions),
                "implementable_count": len(implementable_suggestions),
                "manual_count": len(manual_suggestions),
                "filters_applied": {
                    "priority_filter": priority_filter,
                    "max_suggestions": max_suggestions
                }
            }
        }
    
    def _generate_workflow_summary(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive workflow summary"""
        steps = workflow_result.get("steps", {})
        analysis_result = steps.get("analysis", {})
        pr_result = steps.get("pr_creation", {})
        suggestions = steps.get("processed_suggestions", {})
        
        # Extract key metrics
        analysis_success = analysis_result.get("success", False)
        analysis_data = analysis_result.get("result", {}) if analysis_success else {}
        
        quality_score = analysis_data.get("code_analysis", {}).get("quality_score", 0)
        security_score = analysis_data.get("security_analysis", {}).get("score", 0)
        
        pr_success = pr_result.get("success", False) if pr_result else False
        pr_data = pr_result.get("result", {}) if pr_success else {}
        
        # Generate summary
        summary = {
            "workflow_status": "completed" if workflow_result.get("success") else "failed",
            "analysis_performed": analysis_success,
            "pr_created": pr_success,
            "metrics": {
                "code_quality_score": quality_score,
                "security_score": security_score,
                "overall_score": (quality_score * 0.6 + security_score * 0.4) if quality_score and security_score else 0,
                "suggestions_total": suggestions.get("processing_info", {}).get("total_suggestions", 0),
                "suggestions_implementable": suggestions.get("processing_info", {}).get("implementable_count", 0),
                "suggestions_manual": suggestions.get("processing_info", {}).get("manual_count", 0)
            },
            "outcomes": self._generate_outcome_messages(analysis_data, pr_data, suggestions),
            "recommendations": self._generate_recommendations(analysis_data, suggestions),
            "next_steps": self._generate_next_steps(analysis_data, pr_data, suggestions)
        }
        
        return summary
    
    def _generate_outcome_messages(self, analysis_data: Dict[str, Any], 
                                 pr_data: Dict[str, Any], 
                                 suggestions: Dict[str, Any]) -> List[str]:
        """Generate outcome messages for the workflow"""
        outcomes = []
        
        # Analysis outcomes
        quality_score = analysis_data.get("code_analysis", {}).get("quality_score", 0)
        security_score = analysis_data.get("security_analysis", {}).get("score", 0)
        
        if quality_score >= 80:
            outcomes.append("✅ Repository has excellent code quality")
        elif quality_score >= 60:
            outcomes.append("⚠️ Repository has good code quality with room for improvement")
        else:
            outcomes.append("🔧 Repository needs significant code quality improvements")
        
        if security_score >= 90:
            outcomes.append("🔒 Repository has excellent security posture")
        elif security_score >= 70:
            outcomes.append("⚠️ Repository has good security with minor issues")
        else:
            outcomes.append("🚨 Repository has security issues that need attention")
        
        # Suggestions outcomes
        implementable_count = suggestions.get("processing_info", {}).get("implementable_count", 0)
        if implementable_count > 0:
            outcomes.append(f"🤖 {implementable_count} suggestions can be automatically implemented")
        
        manual_count = suggestions.get("processing_info", {}).get("manual_count", 0)
        if manual_count > 0:
            outcomes.append(f"👤 {manual_count} suggestions require manual implementation")
        
        # PR outcomes
        if pr_data:
            pr_info = pr_data.get("pr_result", {}).get("pull_request", {})
            if pr_info.get("number"):
                outcomes.append(f"🔧 Pull Request #{pr_info['number']} created with improvements")
        
        return outcomes
    
    def _generate_recommendations(self, analysis_data: Dict[str, Any], 
                                suggestions: Dict[str, Any]) -> List[str]:
        """Generate workflow-level recommendations"""
        recommendations = []
        
        # Based on quality score
        quality_score = analysis_data.get("code_analysis", {}).get("quality_score", 0)
        if quality_score < 70:
            recommendations.append("Focus on improving code documentation and structure")
        
        # Based on security score
        security_score = analysis_data.get("security_analysis", {}).get("score", 0)
        if security_score < 80:
            recommendations.append("Address security vulnerabilities and implement best practices")
        
        # Based on suggestions
        high_priority_suggestions = [
            s for s in suggestions.get("all_suggestions", [])
            if s.get("priority") == "High"
        ]
        
        if len(high_priority_suggestions) > 3:
            recommendations.append("Prioritize high-impact improvements for maximum benefit")
        
        # Repository health
        if quality_score < 60 or security_score < 70:
            recommendations.append("Consider implementing automated testing and CI/CD pipeline")
        
        return recommendations
    
    def _generate_next_steps(self, analysis_data: Dict[str, Any], 
                           pr_data: Dict[str, Any], 
                           suggestions: Dict[str, Any]) -> List[str]:
        """Generate recommended next steps"""
        next_steps = []
        
        # PR-related steps
        if pr_data and pr_data.get("success"):
            pr_info = pr_data.get("pr_result", {}).get("pull_request", {})
            if pr_info.get("url"):
                next_steps.append(f"Review and merge Pull Request: {pr_info['url']}")
        
        # Manual implementation steps
        manual_suggestions = suggestions.get("manual_suggestions", [])
        high_priority_manual = [s for s in manual_suggestions if s.get("priority") == "High"]
        
        for suggestion in high_priority_manual[:2]:  # Top 2 manual suggestions
            next_steps.append(f"Implement: {suggestion.get('title', 'Manual improvement')}")
        
        # Quality improvement steps
        quality_score = analysis_data.get("code_analysis", {}).get("quality_score", 0)
        if quality_score < 70:
            next_steps.append("Improve code documentation and add missing README sections")
        
        # Security improvement steps
        security_issues = analysis_data.get("security_analysis", {}).get("issues", [])
        high_severity_issues = [i for i in security_issues if i.get("severity") == "high"]
        
        if high_severity_issues:
            next_steps.append("Address high-severity security issues immediately")
        
        # Testing steps
        test_files = analysis_data.get("code_analysis", {}).get("file_structure", {}).get("test_files", 0)
        if test_files == 0:
            next_steps.append("Add automated tests to improve code reliability")
        
        return next_steps[:5]  # Limit to top 5 next steps
    
    async def analyze_repository_only(self, repo_url: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Perform repository analysis without PR creation"""
        return await self.github_analyzer.analyze_repository(repo_url, analysis_type)
    
    async def create_pr_only(self, repo_url: str, suggestions: List[Dict[str, Any]], 
                           analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create PR with given suggestions without analysis"""
        return await self.pr_creator.create_improvement_pr(repo_url, suggestions, analysis_result)
    
    async def execute_feature_implementation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute feature implementation workflow"""
        workflow_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log workflow start
        self.logger.log_task_start(
            agent_id=self.agent_id,
            task_name="feature_implementation_workflow",
            task_id=workflow_id,
            metadata={
                "repo_url": config.get("repo_url"),
                "feature_prompt": config.get("feature_prompt"),
                "base_branch": config.get("base_branch", "main"),
                "feature_branch": config.get("feature_branch")
            }
        )
        
        workflow_result = {
            "workflow_id": workflow_id,
            "workflow_type": "feature_implementation",
            "repo_url": config.get("repo_url"),
            "config": config,
            "steps": {},
            "success": False,
            "error": None
        }
        
        try:
            # Execute feature implementation through feature agent
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.AGENT_COMMUNICATION,
                message="Starting feature implementation",
                metadata={"step": "feature_implementation", "workflow_id": workflow_id}
            )
            
            feature_result = await self.feature_agent.implement_feature(config)
            workflow_result["steps"]["feature_implementation"] = feature_result
            
            if not feature_result.get("success"):
                raise Exception(f"Feature implementation failed: {feature_result.get('error')}")
            
            # Generate workflow summary for feature implementation
            workflow_summary = self._generate_feature_workflow_summary(workflow_result, feature_result)
            workflow_result["summary"] = workflow_summary
            
            # Mark workflow as successful
            workflow_result["success"] = True
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful completion
            self.logger.log_task_complete(
                agent_id=self.agent_id,
                task_name="feature_implementation_workflow",
                task_id=workflow_id,
                duration_ms=duration_ms,
                metadata={
                    "repo_url": config["repo_url"],
                    "feature_success": feature_result.get("success", False),
                    "pr_created": feature_result.get("pr_created", False),
                    "files_modified": len(feature_result.get("files_modified", []))
                }
            )
            
            # Track performance metrics
            self.monitor.track_task_duration(self.agent_id, "feature_implementation_workflow", duration_ms)
            
            return workflow_result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            workflow_result["error"] = str(e)
            workflow_result["success"] = False
            
            self.logger.log_task_error(
                agent_id=self.agent_id,
                task_name="feature_implementation_workflow",
                task_id=workflow_id,
                error=str(e),
                duration_ms=duration_ms,
                metadata={"repo_url": config.get("repo_url")}
            )
            
            # Track error
            self.monitor.track_error(self.agent_id, "feature_workflow_error")
            
            return workflow_result
    
    def _generate_feature_workflow_summary(self, workflow_result: Dict[str, Any], feature_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary for feature implementation workflow"""
        
        feature_plan = feature_result.get("feature_plan", {})
        files_modified = feature_result.get("files_modified", [])
        
        summary = {
            "workflow_status": "completed" if workflow_result.get("success") else "failed",
            "feature_implemented": feature_result.get("success", False),
            "pr_created": feature_result.get("pr_created", False),
            "branch_created": feature_result.get("branch_created", False),
            "metrics": {
                "files_modified": len(files_modified),
                "feature_complexity": feature_plan.get("feature_analysis", {}).get("complexity", "unknown"),
                "dependencies_added": len(feature_plan.get("dependencies", [])),
                "implementation_time_estimate": self._estimate_implementation_time(feature_plan)
            },
            "outcomes": self._generate_feature_outcomes(feature_result, feature_plan),
            "recommendations": self._generate_feature_recommendations(feature_result, feature_plan),
            "next_steps": self._generate_feature_next_steps(feature_result, feature_plan)
        }
        
        return summary
    
    def _estimate_implementation_time(self, feature_plan: Dict[str, Any]) -> str:
        """Estimate implementation time based on feature plan"""
        complexity = feature_plan.get("feature_analysis", {}).get("complexity", "medium")
        files_count = len(feature_plan.get("files_to_modify", []))
        
        time_estimates = {
            "low": "1-2 hours",
            "medium": "2-4 hours", 
            "high": "4-8 hours"
        }
        
        base_estimate = time_estimates.get(complexity, "2-4 hours")
        
        if files_count > 5:
            return f"{base_estimate} (extended due to multiple files)"
        
        return base_estimate
    
    def _generate_feature_outcomes(self, feature_result: Dict[str, Any], feature_plan: Dict[str, Any]) -> List[str]:
        """Generate outcome messages for feature implementation"""
        outcomes = []
        
        if feature_result.get("success"):
            outcomes.append("✅ Feature implementation completed successfully")
        else:
            outcomes.append("❌ Feature implementation failed")
            
        if feature_result.get("branch_created"):
            branch_name = feature_result.get("feature_branch", "feature branch")
            outcomes.append(f"🌿 Created feature branch: {branch_name}")
            
        files_modified = feature_result.get("files_modified", [])
        if files_modified:
            outcomes.append(f"📝 Modified {len(files_modified)} files")
            
        if feature_result.get("pr_created"):
            pr_url = feature_result.get("pr_url")
            if pr_url:
                outcomes.append(f"🔧 Created pull request: {pr_url}")
            else:
                outcomes.append("🔧 Pull request created successfully")
                
        complexity = feature_plan.get("feature_analysis", {}).get("complexity", "medium")
        outcomes.append(f"📊 Feature complexity: {complexity.title()}")
        
        return outcomes
    
    def _generate_feature_recommendations(self, feature_result: Dict[str, Any], feature_plan: Dict[str, Any]) -> List[str]:
        """Generate recommendations for feature implementation"""
        recommendations = []
        
        if feature_result.get("pr_created"):
            recommendations.append("Review the generated code changes before merging")
            recommendations.append("Test the implementation thoroughly in a development environment")
            
        # Testing recommendations
        testing_strategy = feature_plan.get("testing_strategy", {})
        if testing_strategy.get("unit_tests"):
            recommendations.append("Implement the suggested unit tests")
            
        if testing_strategy.get("integration_tests"):
            recommendations.append("Run integration tests to ensure compatibility")
            
        # Dependencies recommendations
        dependencies = feature_plan.get("dependencies", [])
        if dependencies:
            recommendations.append("Review and install new dependencies carefully")
            recommendations.append("Update documentation to reflect new dependencies")
            
        # Potential issues
        issues = feature_plan.get("potential_issues", [])
        if issues:
            recommendations.append("Address potential issues mentioned in the implementation plan")
            
        return recommendations
    
    def _generate_feature_next_steps(self, feature_result: Dict[str, Any], feature_plan: Dict[str, Any]) -> List[str]:
        """Generate next steps for feature implementation"""
        next_steps = []
        
        if feature_result.get("pr_created"):
            pr_url = feature_result.get("pr_url")
            if pr_url:
                next_steps.append(f"Review pull request: {pr_url}")
            next_steps.append("Test the implemented feature")
            next_steps.append("Merge the pull request after review")
        elif feature_result.get("branch_created"):
            branch_name = feature_result.get("feature_branch")
            next_steps.append(f"Review changes in branch: {branch_name}")
            next_steps.append("Create pull request manually if needed")
            
        # Testing steps
        testing_strategy = feature_plan.get("testing_strategy", {})
        manual_tests = testing_strategy.get("manual_testing", [])
        if manual_tests:
            next_steps.append("Execute manual testing steps")
            
        # Documentation steps
        files_modified = feature_result.get("files_modified", [])
        if any("README" in f for f in files_modified):
            next_steps.append("Update project documentation")
            
        return next_steps[:5]  # Limit to top 5 next steps
    
    def stop(self):
        """Stop the coordinator and all sub-agents"""
        self.logger.log_agent_stop(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            metadata={"stopped_at": time.time()}
        )
        
        # Stop sub-agents
        self.github_analyzer.stop()
        self.pr_creator.stop()
        
        self.monitor.track_agent_stop(self.agent_id)

def get_workflow_coordinator() -> WorkflowCoordinator:
    """Get workflow coordinator instance"""
    return WorkflowCoordinator()
