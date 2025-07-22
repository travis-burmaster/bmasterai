
"""GitHub repository analysis agent with BMasterAI integration"""
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional
from utils.bmasterai_logging import get_logger, EventType, LogLevel
from utils.bmasterai_monitoring import get_monitor
from integrations.github_client import get_github_client
from integrations.mcp_client import get_mcp_client
from utils.llm_client import get_llm_client
from config import get_config_manager

class GitHubAnalyzerAgent:
    """Agent for analyzing GitHub repositories with comprehensive monitoring"""
    
    def __init__(self, agent_id: str = "github_analyzer"):
        self.agent_id = agent_id
        self.agent_name = "GitHub Analyzer Agent"
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.github_client = get_github_client()
        self.llm_client = get_llm_client()
        
        # Get model configuration
        self.config_manager = get_config_manager()
        self.model_config = self.config_manager.get_model_config()
        self.model = self.model_config.github_analyzer_model
        
        # Log agent initialization
        self.logger.log_agent_start(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            metadata={"initialized_at": time.time()}
        )
        
        # Track agent start in monitoring
        self.monitor.track_agent_start(self.agent_id)
    
    async def analyze_repository(self, repo_url: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze a GitHub repository with full monitoring and logging"""
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log task start
        self.logger.log_task_start(
            agent_id=self.agent_id,
            task_name="repository_analysis",
            task_id=task_id,
            metadata={
                "repo_url": repo_url,
                "analysis_type": analysis_type
            }
        )
        
        try:
            # Step 1: Get basic repository information
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message="Fetching repository information",
                metadata={"step": "repo_info", "task_id": task_id}
            )
            
            repo_info = await self._fetch_repository_info(repo_url)
            
            # Step 2: Analyze code structure and quality
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message="Analyzing code structure",
                metadata={"step": "code_analysis", "task_id": task_id}
            )
            
            code_analysis = await self._analyze_code_structure(repo_url)
            
            # Step 3: Security and best practices analysis
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message="Performing security analysis",
                metadata={"step": "security_analysis", "task_id": task_id}
            )
            
            security_analysis = await self._analyze_security(repo_url, repo_info)
            
            # Step 4: Generate improvement suggestions using LLM
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_START,
                message="Generating improvement suggestions",
                metadata={"step": "improvement_suggestions", "task_id": task_id}
            )
            
            suggestions = await self._generate_improvement_suggestions(
                repo_info, code_analysis, security_analysis
            )
            
            # Compile results
            duration_ms = (time.time() - start_time) * 1000
            
            result = {
                "task_id": task_id,
                "repo_url": repo_url,
                "analysis_type": analysis_type,
                "timestamp": time.time(),
                "duration_ms": duration_ms,
                "repository_info": repo_info,
                "code_analysis": code_analysis,
                "security_analysis": security_analysis,
                "improvement_suggestions": suggestions,
                "summary": self._generate_analysis_summary(repo_info, code_analysis, security_analysis, suggestions)
            }
            
            # Log successful completion
            self.logger.log_task_complete(
                agent_id=self.agent_id,
                task_name="repository_analysis",
                task_id=task_id,
                duration_ms=duration_ms,
                metadata={
                    "repo_name": repo_info.get("name", "unknown"),
                    "suggestions_count": len(suggestions.get("suggestions", [])),
                    "security_issues": len(security_analysis.get("issues", [])),
                    "code_quality_score": code_analysis.get("quality_score", 0)
                }
            )
            
            # Track performance metrics
            self.monitor.track_task_duration(self.agent_id, "repository_analysis", duration_ms)
            
            return {"success": True, "result": result}
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.log_task_error(
                agent_id=self.agent_id,
                task_name="repository_analysis",
                task_id=task_id,
                error=str(e),
                duration_ms=duration_ms,
                metadata={"repo_url": repo_url}
            )
            
            # Track error
            self.monitor.track_error(self.agent_id, "repository_analysis_error")
            
            return {"success": False, "error": str(e), "task_id": task_id}
    
    async def _fetch_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """Fetch comprehensive repository information"""
        try:
            # Get basic repository stats
            repo_stats = self.github_client.get_repository_stats(repo_url)
            
            # Get repository health check
            health_check = self.github_client.check_repository_health(repo_url)
            
            # Get repository topics
            topics = self.github_client.get_repository_topics(repo_url)
            
            return {
                "basic_info": repo_stats.get("basic_info", {}),
                "languages": repo_stats.get("languages", {}),
                "stats": repo_stats.get("stats", {}),
                "recent_commits": repo_stats.get("recent_commits", [])[:5],  # Last 5 commits
                "health_check": health_check,
                "topics": topics
            }
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to fetch repository info: {str(e)}",
                level=LogLevel.ERROR
            )
            raise
    
    async def _analyze_code_structure(self, repo_url: str) -> Dict[str, Any]:
        """Analyze code structure and quality metrics"""
        try:
            # Get repository contents
            contents = self.github_client.get_repository_contents(repo_url)
            
            # Analyze file structure
            file_analysis = self._analyze_file_structure(contents)
            
            # Analyze key files if available
            key_files_analysis = await self._analyze_key_files(repo_url)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(file_analysis, key_files_analysis)
            
            return {
                "file_structure": file_analysis,
                "key_files": key_files_analysis,
                "quality_score": quality_score,
                "metrics": {
                    "total_files": file_analysis.get("total_files", 0),
                    "code_files": file_analysis.get("code_files", 0),
                    "documentation_files": file_analysis.get("documentation_files", 0),
                    "config_files": file_analysis.get("config_files", 0)
                }
            }
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to analyze code structure: {str(e)}",
                level=LogLevel.ERROR
            )
            return {"error": str(e), "quality_score": 0}
    
    def _analyze_file_structure(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze repository file structure"""
        structure = {
            "total_files": 0,
            "code_files": 0,
            "documentation_files": 0,
            "config_files": 0,
            "test_files": 0,
            "directories": 0,
            "file_types": {},
            "important_files": []
        }
        
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
        doc_extensions = {'.md', '.txt', '.rst', '.adoc'}
        config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'}
        test_indicators = {'test', 'tests', 'spec', '__test__', '.test.', '.spec.'}
        
        for item in contents:
            name = item.get("name", "")
            item_type = item.get("type", "")
            
            if item_type == "dir":
                structure["directories"] += 1
            elif item_type == "file":
                structure["total_files"] += 1
                
                # Get file extension
                ext = "." + name.split(".")[-1] if "." in name else ""
                structure["file_types"][ext] = structure["file_types"].get(ext, 0) + 1
                
                # Categorize file
                if ext.lower() in code_extensions:
                    structure["code_files"] += 1
                elif ext.lower() in doc_extensions:
                    structure["documentation_files"] += 1
                elif ext.lower() in config_extensions:
                    structure["config_files"] += 1
                
                # Check for test files
                if any(indicator in name.lower() for indicator in test_indicators):
                    structure["test_files"] += 1
                
                # Mark important files
                important_files = ['README.md', 'LICENSE', 'requirements.txt', 'package.json', 
                                 'Dockerfile', 'docker-compose.yml', '.gitignore', 'setup.py']
                if name in important_files:
                    structure["important_files"].append(name)
        
        return structure
    
    async def _analyze_key_files(self, repo_url: str) -> Dict[str, Any]:
        """Analyze key repository files for insights"""
        key_files_analysis = {}
        
        important_files = [
            "README.md", "requirements.txt", "package.json", 
            "Dockerfile", "setup.py", ".gitignore"
        ]
        
        for file_name in important_files:
            try:
                content = self.github_client.get_file_content(repo_url, file_name)
                key_files_analysis[file_name] = {
                    "exists": True,
                    "size": len(content),
                    "analysis": self._analyze_file_content(file_name, content)
                }
            except:
                key_files_analysis[file_name] = {"exists": False}
        
        return key_files_analysis
    
    def _analyze_file_content(self, file_name: str, content: str) -> Dict[str, Any]:
        """Analyze specific file content"""
        analysis = {"lines": len(content.split('\n'))}
        
        if file_name == "README.md":
            analysis.update({
                "has_description": "description" in content.lower() or "# " in content,
                "has_installation": "install" in content.lower(),
                "has_usage": "usage" in content.lower() or "example" in content.lower(),
                "has_license": "license" in content.lower(),
                "has_contributing": "contribut" in content.lower()
            })
        elif file_name == "requirements.txt":
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            analysis.update({
                "dependencies_count": len(lines),
                "has_versions": any("==" in line or ">=" in line for line in lines)
            })
        elif file_name == "package.json":
            try:
                import json
                data = json.loads(content)
                analysis.update({
                    "has_description": "description" in data,
                    "has_scripts": "scripts" in data,
                    "dependencies_count": len(data.get("dependencies", {})),
                    "dev_dependencies_count": len(data.get("devDependencies", {}))
                })
            except:
                analysis["parse_error"] = True
        
        return analysis
    
    def _calculate_quality_score(self, file_analysis: Dict[str, Any], key_files: Dict[str, Any]) -> int:
        """Calculate overall code quality score"""
        score = 0
        
        # File structure scoring (40 points max)
        if file_analysis.get("code_files", 0) > 0:
            score += 15
        
        if file_analysis.get("test_files", 0) > 0:
            score += 15
        
        if file_analysis.get("documentation_files", 0) > 0:
            score += 10
        
        # Important files scoring (60 points max)
        important_files_score = {
            "README.md": 20,
            "LICENSE": 10,
            "requirements.txt": 10,
            "package.json": 10,
            ".gitignore": 5,
            "Dockerfile": 5
        }
        
        for file_name, points in important_files_score.items():
            if key_files.get(file_name, {}).get("exists", False):
                score += points
        
        return min(score, 100)
    
    async def _analyze_security(self, repo_url: str, repo_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository for security issues and best practices"""
        security_analysis = {
            "issues": [],
            "recommendations": [],
            "score": 100  # Start with perfect score and deduct
        }
        
        try:
            # Check for sensitive files
            sensitive_files = [".env", "config.py", "secrets.json", "private_key"]
            for file_name in sensitive_files:
                try:
                    self.github_client.get_file_content(repo_url, file_name)
                    security_analysis["issues"].append({
                        "type": "sensitive_file",
                        "severity": "high",
                        "file": file_name,
                        "description": f"Sensitive file {file_name} found in repository"
                    })
                    security_analysis["score"] -= 20
                except:
                    pass  # File not found, which is good
            
            # Check for hardcoded secrets in common files
            files_to_check = ["README.md", "config.py", "settings.py"]
            secret_patterns = ["password", "api_key", "secret", "token"]
            
            for file_name in files_to_check:
                try:
                    content = self.github_client.get_file_content(repo_url, file_name).lower()
                    for pattern in secret_patterns:
                        if pattern in content and "=" in content:
                            security_analysis["issues"].append({
                                "type": "potential_secret",
                                "severity": "medium",
                                "file": file_name,
                                "description": f"Potential hardcoded secret pattern '{pattern}' found in {file_name}"
                            })
                            security_analysis["score"] -= 10
                except:
                    pass
            
            # Check repository settings
            if repo_info.get("basic_info", {}).get("private") is False:
                security_analysis["recommendations"].append({
                    "type": "repository_visibility",
                    "description": "Repository is public - ensure no sensitive data is exposed"
                })
            
            # Check for license
            if not any(key_file.get("exists", False) for key_file in [
                repo_info.get("key_files", {}).get("LICENSE", {}),
                repo_info.get("key_files", {}).get("LICENSE.txt", {})
            ]):
                security_analysis["recommendations"].append({
                    "type": "missing_license",
                    "description": "Consider adding a LICENSE file to clarify usage rights"
                })
                security_analysis["score"] -= 5
            
            # Generate security recommendations
            if security_analysis["score"] < 80:
                security_analysis["recommendations"].append({
                    "type": "security_review",
                    "description": "Consider conducting a thorough security review"
                })
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Security analysis failed: {str(e)}",
                level=LogLevel.ERROR
            )
            security_analysis["error"] = str(e)
        
        return security_analysis
    
    async def _generate_improvement_suggestions(self, repo_info: Dict[str, Any], 
                                              code_analysis: Dict[str, Any], 
                                              security_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate improvement suggestions using LLM"""
        try:
            # Prepare context for LLM
            context = {
                "repository_name": repo_info.get("basic_info", {}).get("name", "Unknown"),
                "language_stats": repo_info.get("languages", {}),
                "quality_score": code_analysis.get("quality_score", 0),
                "security_score": security_analysis.get("score", 0),
                "file_structure": code_analysis.get("file_structure", {}),
                "security_issues": security_analysis.get("issues", []),
                "health_recommendations": repo_info.get("health_check", {}).get("recommendations", [])
            }
            
            # Create prompt for LLM
            prompt = f"""
            Analyze this GitHub repository and provide specific, actionable improvement suggestions:

            Repository: {context['repository_name']}
            Languages: {', '.join(context['language_stats'].keys())}
            Code Quality Score: {context['quality_score']}/100
            Security Score: {context['security_score']}/100

            File Structure:
            - Total files: {context['file_structure'].get('total_files', 0)}
            - Code files: {context['file_structure'].get('code_files', 0)}
            - Documentation files: {context['file_structure'].get('documentation_files', 0)}
            - Test files: {context['file_structure'].get('test_files', 0)}

            Security Issues: {len(context['security_issues'])} issues found
            Health Recommendations: {context['health_recommendations']}

            Please provide:
            1. Top 5 specific improvement suggestions with implementation steps
            2. Priority level (High/Medium/Low) for each suggestion
            3. Estimated implementation time for each
            4. Expected impact on code quality/security

            Format as JSON with this structure:
            {{
                "suggestions": [
                    {{
                        "title": "Suggestion title",
                        "description": "Detailed description",
                        "priority": "High/Medium/Low",
                        "category": "security/documentation/testing/code_quality/performance",
                        "implementation_steps": ["step1", "step2", "step3"],
                        "estimated_time": "time estimate",
                        "expected_impact": "impact description",
                        "files_to_modify": ["file1", "file2"]
                    }}
                ]
            }}
            """
            
            # Call LLM with structured response
            suggestions_response = await self.llm_client.call_llm_structured(
                model=self.model,
                prompt=prompt,
                max_tokens=2000
            )
            
            return suggestions_response
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to generate suggestions: {str(e)}",
                level=LogLevel.ERROR
            )
            
            # Fallback to rule-based suggestions
            return self._generate_fallback_suggestions(repo_info, code_analysis, security_analysis)
    
    def _generate_fallback_suggestions(self, repo_info: Dict[str, Any], 
                                     code_analysis: Dict[str, Any], 
                                     security_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback suggestions when LLM is unavailable"""
        suggestions = []
        
        # Quality-based suggestions
        if code_analysis.get("quality_score", 0) < 60:
            suggestions.append({
                "title": "Improve Code Documentation",
                "description": "Add comprehensive README and inline documentation",
                "priority": "High",
                "category": "documentation",
                "implementation_steps": [
                    "Create detailed README.md",
                    "Add inline code comments",
                    "Document API endpoints"
                ],
                "estimated_time": "2-4 hours",
                "expected_impact": "Better maintainability and onboarding"
            })
        
        # Security-based suggestions
        if security_analysis.get("score", 100) < 80:
            suggestions.append({
                "title": "Address Security Issues",
                "description": "Fix identified security vulnerabilities",
                "priority": "High",
                "category": "security",
                "implementation_steps": [
                    "Remove hardcoded secrets",
                    "Add .env file to .gitignore",
                    "Implement proper secret management"
                ],
                "estimated_time": "1-2 hours",
                "expected_impact": "Improved security posture"
            })
        
        # Testing suggestions
        if code_analysis.get("file_structure", {}).get("test_files", 0) == 0:
            suggestions.append({
                "title": "Add Automated Testing",
                "description": "Implement unit and integration tests",
                "priority": "Medium",
                "category": "testing",
                "implementation_steps": [
                    "Set up testing framework",
                    "Write unit tests for core functions",
                    "Add CI/CD pipeline"
                ],
                "estimated_time": "4-8 hours",
                "expected_impact": "Improved code reliability"
            })
        
        return {"suggestions": suggestions}
    
    def _generate_analysis_summary(self, repo_info: Dict[str, Any], 
                                 code_analysis: Dict[str, Any], 
                                 security_analysis: Dict[str, Any], 
                                 suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive analysis summary"""
        return {
            "overall_score": (
                code_analysis.get("quality_score", 0) * 0.6 + 
                security_analysis.get("score", 0) * 0.4
            ),
            "strengths": self._identify_strengths(repo_info, code_analysis, security_analysis),
            "areas_for_improvement": self._identify_improvements(code_analysis, security_analysis),
            "priority_actions": [
                s for s in suggestions.get("suggestions", []) 
                if s.get("priority") == "High"
            ][:3],
            "metrics": {
                "code_quality": code_analysis.get("quality_score", 0),
                "security_score": security_analysis.get("score", 0),
                "suggestions_count": len(suggestions.get("suggestions", [])),
                "high_priority_issues": len([
                    s for s in suggestions.get("suggestions", []) 
                    if s.get("priority") == "High"
                ])
            }
        }
    
    def _identify_strengths(self, repo_info: Dict[str, Any], 
                          code_analysis: Dict[str, Any], 
                          security_analysis: Dict[str, Any]) -> List[str]:
        """Identify repository strengths"""
        strengths = []
        
        if code_analysis.get("quality_score", 0) >= 80:
            strengths.append("Well-structured codebase")
        
        if security_analysis.get("score", 0) >= 90:
            strengths.append("Good security practices")
        
        if repo_info.get("health_check", {}).get("score", 0) >= 80:
            strengths.append("Healthy repository maintenance")
        
        if code_analysis.get("file_structure", {}).get("test_files", 0) > 0:
            strengths.append("Has automated testing")
        
        return strengths
    
    def _identify_improvements(self, code_analysis: Dict[str, Any], 
                             security_analysis: Dict[str, Any]) -> List[str]:
        """Identify key areas for improvement"""
        improvements = []
        
        if code_analysis.get("quality_score", 0) < 70:
            improvements.append("Code organization and documentation")
        
        if security_analysis.get("score", 0) < 80:
            improvements.append("Security practices and secret management")
        
        if code_analysis.get("file_structure", {}).get("test_files", 0) == 0:
            improvements.append("Test coverage and automated testing")
        
        if code_analysis.get("file_structure", {}).get("documentation_files", 0) == 0:
            improvements.append("Project documentation")
        
        return improvements
    
    def stop(self):
        """Stop the agent and clean up resources"""
        self.logger.log_agent_stop(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            metadata={"stopped_at": time.time()}
        )
        
        self.monitor.track_agent_stop(self.agent_id)

def get_github_analyzer() -> GitHubAnalyzerAgent:
    """Get GitHub analyzer agent instance"""
    return GitHubAnalyzerAgent()
