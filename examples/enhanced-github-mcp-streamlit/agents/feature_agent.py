
"""Feature Agent for implementing user-requested features and bug fixes"""
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from utils.bmasterai_logging import get_logger, EventType, LogLevel
from utils.bmasterai_monitoring import get_monitor
from utils.llm_client import get_llm_client
from integrations.github_client import GitHubClient
from config import get_config_manager
import re
import os
import json

class FeatureAgent:
    """Agent responsible for implementing features based on user prompts"""
    
    def __init__(self, agent_id: str = "feature_agent"):
        self.agent_id = agent_id
        self.agent_name = "Feature Implementation Agent"
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.llm_client = get_llm_client()
        self.github_client = GitHubClient()
        
        # Get model configuration
        self.config_manager = get_config_manager()
        self.model_config = self.config_manager.get_model_config()
        self.model = self.model_config.feature_agent_model
        
        # Log agent initialization
        self.logger.log_agent_start(
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            metadata={"initialized_at": time.time()}
        )
        
        # Track agent start in monitoring
        self.monitor.track_agent_start(self.agent_id)
    
    async def implement_feature(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to implement a feature based on user prompt"""
        task_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log task start
        self.logger.log_task_start(
            agent_id=self.agent_id,
            task_name="implement_feature",
            task_id=task_id,
            metadata={
                "repo_url": config.get("repo_url"),
                "feature_prompt": config.get("feature_prompt"),
                "base_branch": config.get("base_branch", "main"),
                "feature_branch": config.get("feature_branch")
            }
        )
        
        result = {
            "task_id": task_id,
            "success": False,
            "error": None,
            "repo_info": {},
            "feature_plan": {},
            "code_changes": [],
            "branch_created": False,
            "files_modified": [],
            "pr_created": False,
            "pr_url": None
        }
        
        try:
            # Step 1: Parse repository URL and get repo info
            repo_info = self._parse_repo_url(config["repo_url"])
            result["repo_info"] = repo_info
            
            # Step 2: Analyze repository structure
            repo_structure = await self._analyze_repository_structure(repo_info)
            
            # Step 3: Generate feature implementation plan
            feature_plan = await self._generate_feature_plan(
                config["feature_prompt"],
                repo_structure,
                repo_info
            )
            result["feature_plan"] = feature_plan
            
            # Step 4: Generate code changes
            code_changes = await self._generate_code_changes(
                feature_plan,
                repo_structure,
                repo_info
            )
            result["code_changes"] = code_changes
            
            # Step 5: Create feature branch
            branch_name = config.get("feature_branch") or self._generate_branch_name(config["feature_prompt"])
            branch_created = await self._create_feature_branch(
                repo_info,
                config.get("base_branch", "main"),
                branch_name
            )
            result["branch_created"] = branch_created
            result["feature_branch"] = branch_name
            
            # Step 6: Apply code changes to branch
            if branch_created and code_changes:
                modified_files = await self._apply_code_changes(
                    repo_info,
                    branch_name,
                    code_changes
                )
                result["files_modified"] = modified_files
            
            # Step 7: Create pull request
            if result["files_modified"]:
                pr_result = await self._create_pull_request(
                    repo_info,
                    branch_name,
                    config.get("base_branch", "main"),
                    feature_plan,
                    config["feature_prompt"]
                )
                result["pr_created"] = pr_result.get("success", False)
                result["pr_url"] = pr_result.get("pr_url")
            
            result["success"] = True
            
            # Log successful completion
            self.logger.log_task_complete(
                agent_id=self.agent_id,
                task_name="implement_feature",
                task_id=task_id,
                duration_ms=(time.time() - start_time) * 1000,
                metadata={
                    "files_modified": len(result["files_modified"]),
                    "pr_created": result["pr_created"],
                    "branch_name": branch_name
                }
            )
            
        except Exception as e:
            result["error"] = str(e)
            
            # Log error
            self.logger.log_task_error(
                agent_id=self.agent_id,
                task_name="implement_feature",
                task_id=task_id,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
                metadata={"repo_url": config.get("repo_url")}
            )
        
        return result
    
    def _parse_repo_url(self, repo_url: str) -> Dict[str, str]:
        """Parse GitHub repository URL to extract owner and repo name"""
        # Handle various GitHub URL formats
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',
            r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$',
            r'github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, repo_url.strip())
            if match:
                owner, repo = match.groups()
                return {
                    "owner": owner,
                    "repo": repo,
                    "full_name": f"{owner}/{repo}",
                    "url": f"https://github.com/{owner}/{repo}"
                }
        
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    async def _analyze_repository_structure(self, repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Analyze repository structure to understand codebase"""
        try:
            # Get repository contents
            contents = self.github_client._make_request(
                "GET",
                f"repos/{repo_info['full_name']}/contents"
            )
            
            # Get repository info
            repo_data = self.github_client._make_request(
                "GET",
                f"repos/{repo_info['full_name']}"
            )
            
            # Analyze file structure
            file_structure = await self._build_file_tree(repo_info, contents)
            
            # Detect project type and framework
            project_type = self._detect_project_type(contents, file_structure)
            
            return {
                "repo_data": repo_data,
                "file_structure": file_structure,
                "project_type": project_type,
                "main_language": repo_data.get("language"),
                "languages": await self._get_repository_languages(repo_info),
                "readme_content": await self._get_readme_content(repo_info)
            }
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to analyze repository structure: {str(e)}",
                level=LogLevel.ERROR
            )
            
            # Return a safe default structure
            return {
                "repo_data": {},
                "file_structure": {
                    "files": [],
                    "directories": [],
                    "important_files": {},
                    "config_files": [],
                    "source_files": []
                },
                "project_type": "unknown",
                "main_language": "unknown",
                "languages": {},
                "readme_content": ""
            }
    
    async def _build_file_tree(self, repo_info: Dict[str, str], contents: List[Dict]) -> Dict[str, Any]:
        """Build a comprehensive file tree of the repository"""
        file_tree = {
            "files": [],
            "directories": [],
            "important_files": {},
            "config_files": [],
            "source_files": []
        }
        
        important_patterns = {
            "package.json": "nodejs_config",
            "requirements.txt": "python_deps",
            "Pipfile": "python_pipenv",
            "pyproject.toml": "python_poetry",
            "Cargo.toml": "rust_config",
            "go.mod": "go_module",
            "pom.xml": "maven_config",
            "build.gradle": "gradle_config",
            "Dockerfile": "docker_config",
            "docker-compose.yml": "docker_compose",
            "README.md": "readme",
            ".gitignore": "gitignore"
        }
        
        # Ensure contents is a list
        if not isinstance(contents, list):
            contents = []
            
        for item in contents:
            # Ensure item is a dictionary with required keys
            if not isinstance(item, dict) or "type" not in item or "name" not in item:
                continue
                
            if item["type"] == "file":
                file_tree["files"].append(item["name"])
                
                # Check for important files
                if item["name"] in important_patterns:
                    file_tree["important_files"][important_patterns[item["name"]]] = item["name"]
                
                # Categorize files
                if item["name"].endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c', '.rs', '.go')):
                    file_tree["source_files"].append(item["name"])
                elif item["name"].endswith(('.json', '.yml', '.yaml', '.toml', '.ini', '.cfg')):
                    file_tree["config_files"].append(item["name"])
                    
            elif item["type"] == "dir":
                file_tree["directories"].append(item["name"])
        
        return file_tree
    
    def _detect_project_type(self, contents: List[Dict], file_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Detect the type of project and frameworks used"""
        project_info = {
            "type": "unknown",
            "framework": None,
            "build_system": None,
            "package_manager": None
        }
        
        important_files = file_structure.get("important_files", {})
        directories = file_structure.get("directories", [])
        
        # Detect project type based on files and structure
        if "nodejs_config" in important_files:
            project_info["type"] = "nodejs"
            project_info["package_manager"] = "npm"
            
            # Check for specific frameworks
            if "next.config.js" in file_structure["files"] or "next" in directories:
                project_info["framework"] = "nextjs"
            elif "src" in directories and any("react" in f.lower() for f in file_structure["files"]):
                project_info["framework"] = "react"
            elif "nuxt.config.js" in file_structure["files"]:
                project_info["framework"] = "nuxtjs"
                
        elif any(key in important_files for key in ["python_deps", "python_pipenv", "python_poetry"]):
            project_info["type"] = "python"
            
            if "python_poetry" in important_files:
                project_info["package_manager"] = "poetry"
            elif "python_pipenv" in important_files:
                project_info["package_manager"] = "pipenv"
            else:
                project_info["package_manager"] = "pip"
                
            # Check for Python frameworks
            if "manage.py" in file_structure["files"]:
                project_info["framework"] = "django"
            elif "app.py" in file_structure["files"] or "main.py" in file_structure["files"]:
                project_info["framework"] = "flask_or_fastapi"
                
        elif "rust_config" in important_files:
            project_info["type"] = "rust"
            project_info["package_manager"] = "cargo"
            
        elif "go_module" in important_files:
            project_info["type"] = "go"
            project_info["package_manager"] = "go_modules"
        
        return project_info
    
    async def _get_repository_languages(self, repo_info: Dict[str, str]) -> Dict[str, int]:
        """Get programming languages used in the repository"""
        try:
            languages = self.github_client._make_request(
                "GET",
                f"repos/{repo_info['full_name']}/languages"
            )
            return languages
        except:
            return {}
    
    async def _get_readme_content(self, repo_info: Dict[str, str]) -> Optional[str]:
        """Get README content if available"""
        try:
            readme = self.github_client._make_request(
                "GET",
                f"repos/{repo_info['full_name']}/readme"
            )
            
            if readme.get("content"):
                import base64
                content = base64.b64decode(readme["content"]).decode('utf-8')
                return content
        except:
            pass
        
        return None
    
    async def _generate_feature_plan(self, feature_prompt: str, repo_structure: Dict[str, Any], repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Generate a detailed plan for implementing the requested feature"""
        
        # Prepare context for LLM
        file_structure = repo_structure.get("file_structure", {})
        important_files = file_structure.get("important_files", {})
        source_files = file_structure.get("source_files", [])
        
        # Safely extract key files
        key_files = []
        if isinstance(important_files, dict):
            key_files = list(important_files.values())
        
        # Safely extract source files
        if not isinstance(source_files, list):
            source_files = []
        
        context = {
            "repository": repo_info["full_name"],
            "project_type": repo_structure.get("project_type", "unknown"),
            "main_language": repo_structure.get("main_language", "unknown"),
            "file_structure": file_structure,
            "readme_summary": repo_structure.get("readme_content", "")[:1000] if repo_structure.get("readme_content") else "",
            "key_files": key_files,
            "source_files": source_files
        }
        
        prompt = f"""
You are a senior software engineer tasked with implementing a feature request for a GitHub repository.

Repository Context:
- Repository: {context['repository']}
- Project Type: {context['project_type']}
- Main Language: {context['main_language']}
- Key Files: {', '.join(context['key_files'])}
- Source Files: {', '.join(context['source_files'][:10])}

README Summary:
{context['readme_summary']}

Feature Request:
{feature_prompt}

Please create a detailed implementation plan that includes:

1. **Feature Analysis**: Break down what the user is asking for
2. **Implementation Strategy**: High-level approach to implement this feature
3. **Files to Modify**: List specific files that need to be created or modified
4. **Code Changes**: Detailed description of changes needed for each file
5. **Dependencies**: Any new dependencies that might be needed
6. **Testing Strategy**: How this feature should be tested
7. **Potential Issues**: Any challenges or edge cases to consider

IMPORTANT: Respond with ONLY a valid JSON object. Do not include any explanatory text before or after the JSON. The response must start with {{ and end with }}.

Use this exact JSON structure:
{{
    "feature_analysis": {{
        "summary": "Brief summary of the feature request",
        "requirements": ["list", "of", "specific", "requirements"],
        "complexity": "low|medium|high"
    }},
    "implementation_strategy": {{
        "approach": "Description of the implementation approach",
        "architecture_changes": "Any architectural changes needed",
        "integration_points": ["list", "of", "integration", "points"]
    }},
    "files_to_modify": [
        {{
            "path": "path/to/file.ext",
            "action": "create|modify|delete",
            "purpose": "Why this file needs to be changed",
            "priority": "high|medium|low"
        }}
    ],
    "code_changes": [
        {{
            "file": "path/to/file.ext",
            "description": "What changes to make",
            "change_type": "add_function|modify_function|add_class|modify_class|add_import|etc"
        }}
    ],
    "dependencies": [
        {{
            "name": "dependency-name",
            "version": "version-spec",
            "purpose": "Why this dependency is needed"
        }}
    ],
    "testing_strategy": {{
        "unit_tests": ["list", "of", "unit", "tests", "needed"],
        "integration_tests": ["list", "of", "integration", "tests"],
        "manual_testing": ["list", "of", "manual", "testing", "steps"]
    }},
    "potential_issues": [
        {{
            "issue": "Description of potential issue",
            "mitigation": "How to address this issue"
        }}
    ]
}}
"""
        try:
            # Try to get structured response with retry logic
            max_retries = 2
            plan = None
            
            for attempt in range(max_retries + 1):
                try:
                    # Call the LLM and get structured response directly
                    plan = await self.llm_client.call_llm_structured(
                        model=self.model,
                        prompt=prompt,
                        max_tokens=4000
                    )
                    
                    # If we got a valid response without parsing errors, break
                    if isinstance(plan, dict) and "Failed to parse JSON" not in str(plan.get("error", "")):
                        break
                        
                except Exception as e:
                    if attempt == max_retries:
                        raise e
                    
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=f"LLM call attempt {attempt + 1} failed: {str(e)}, retrying...",
                        level=LogLevel.WARNING
                    )
                    
                    # Wait a bit before retrying
                    await asyncio.sleep(1)
            
            if plan is None:
                raise ValueError("Failed to get valid response after all retries")
            
            # Validate that we got a proper dict response
            if not isinstance(plan, dict):
                raise ValueError(f"Expected dict response, got {type(plan)}")
            
            # Check if LLM returned a parsing error
            if "error" in plan and "Failed to parse JSON" in str(plan.get("error", "")):
                # Try to generate a fallback plan using a simpler approach
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message="JSON parsing failed, attempting fallback plan generation",
                    level=LogLevel.WARNING
                )
                
                # Generate a simple fallback plan
                plan = self._generate_fallback_plan(feature_prompt, repo_structure, repo_info)
            
            elif "error" in plan:
                raise ValueError(f"LLM returned error: {plan['error']}")
            
            # Validate required fields and provide defaults if missing
            plan = self._validate_and_fix_plan(plan, feature_prompt)
            
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_COMPLETE,
                message="Feature plan generated successfully",
                metadata={
                    "complexity": plan.get("feature_analysis", {}).get("complexity"),
                    "files_to_modify": len(plan.get("files_to_modify", [])),
                    "dependencies": len(plan.get("dependencies", []))
                }
            )
            
            return plan
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to generate feature plan: {str(e)}",
                level=LogLevel.ERROR
            )
            raise
    
    def _generate_fallback_plan(self, feature_prompt: str, repo_structure: Dict[str, Any], repo_info: Dict[str, str]) -> Dict[str, Any]:
        """Generate a simple fallback plan when JSON parsing fails"""
        return {
            "feature_analysis": {
                "summary": f"Implementation of: {feature_prompt[:100]}...",
                "requirements": ["Implement requested feature", "Maintain code quality", "Add appropriate tests"],
                "complexity": "medium"
            },
            "implementation_strategy": {
                "approach": "Analyze existing codebase and implement feature following established patterns",
                "architecture_changes": "Minimal changes to existing architecture",
                "integration_points": ["Main application logic", "User interface", "Data layer"]
            },
            "files_to_modify": [
                {
                    "path": "main.py",
                    "action": "modify",
                    "purpose": "Add feature implementation",
                    "priority": "high"
                }
            ],
            "code_changes": [
                {
                    "file": "main.py",
                    "description": "Add feature implementation code",
                    "change_type": "add_function"
                }
            ],
            "dependencies": [],
            "testing_strategy": {
                "unit_tests": ["Test main functionality"],
                "integration_tests": ["Test feature integration"],
                "manual_testing": ["Verify feature works as expected"]
            },
            "potential_issues": [
                {
                    "issue": "Feature complexity may require additional refinement",
                    "mitigation": "Break down into smaller, manageable tasks"
                }
            ]
        }
    
    def _validate_and_fix_plan(self, plan: Dict[str, Any], feature_prompt: str) -> Dict[str, Any]:
        """Validate and fix the plan structure, providing defaults for missing fields"""
        # Ensure all required top-level keys exist
        required_keys = [
            "feature_analysis", "implementation_strategy", "files_to_modify",
            "code_changes", "dependencies", "testing_strategy", "potential_issues"
        ]
        
        for key in required_keys:
            if key not in plan:
                if key == "feature_analysis":
                    plan[key] = {
                        "summary": f"Implementation of: {feature_prompt[:100]}",
                        "requirements": ["Implement requested feature"],
                        "complexity": "medium"
                    }
                elif key == "implementation_strategy":
                    plan[key] = {
                        "approach": "Standard implementation approach",
                        "architecture_changes": "Minimal changes",
                        "integration_points": ["Main application"]
                    }
                elif key in ["files_to_modify", "code_changes", "dependencies", "potential_issues"]:
                    plan[key] = []
                elif key == "testing_strategy":
                    plan[key] = {
                        "unit_tests": ["Test main functionality"],
                        "integration_tests": ["Test integration"],
                        "manual_testing": ["Manual verification"]
                    }
        
        # Validate nested structures
        if not isinstance(plan.get("feature_analysis"), dict):
            plan["feature_analysis"] = {"summary": feature_prompt, "requirements": [], "complexity": "medium"}
        
        if not isinstance(plan.get("files_to_modify"), list):
            plan["files_to_modify"] = []
        
        if not isinstance(plan.get("code_changes"), list):
            plan["code_changes"] = []
        
        return plan
    
    async def _generate_code_changes(self, feature_plan: Dict[str, Any], repo_structure: Dict[str, Any], repo_info: Dict[str, str]) -> List[Dict[str, Any]]:
        """Generate actual code changes based on the feature plan"""
        
        code_changes = []
        files_to_modify = feature_plan.get("files_to_modify", [])
        
        for file_info in files_to_modify:
            if file_info["action"] in ["create", "modify"]:
                try:
                    # Get current file content if it exists
                    current_content = ""
                    if file_info["action"] == "modify":
                        current_content = await self._get_file_content(repo_info, file_info["path"])
                    
                    # Generate new content
                    new_content = await self._generate_file_content(
                        file_info,
                        current_content,
                        feature_plan,
                        repo_structure
                    )
                    
                    code_changes.append({
                        "file_path": file_info["path"],
                        "action": file_info["action"],
                        "current_content": current_content,
                        "new_content": new_content,
                        "purpose": file_info["purpose"]
                    })
                    
                except Exception as e:
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=f"Failed to generate code for {file_info['path']}: {str(e)}",
                        level=LogLevel.WARNING
                    )
        
        return code_changes
    
    async def _get_file_content(self, repo_info: Dict[str, str], file_path: str, branch: str = "main") -> str:
        """Get content of a file from the repository"""
        try:
            file_data = self.github_client._make_request(
                "GET",
                f"repos/{repo_info['full_name']}/contents/{file_path}?ref={branch}"
            )
            
            if file_data.get("content"):
                import base64
                content = base64.b64decode(file_data["content"]).decode('utf-8')
                return content
        except:
            pass
        
        return ""
    
    async def _generate_file_content(self, file_info: Dict[str, Any], current_content: str, feature_plan: Dict[str, Any], repo_structure: Dict[str, Any]) -> str:
        """Generate content for a specific file"""
        
        prompt = f"""
You are implementing a feature in a {repo_structure['project_type']['type']} project.

Feature Plan Summary:
{feature_plan.get('feature_analysis', {}).get('summary', '')}

File to {'modify' if file_info['action'] == 'modify' else 'create'}: {file_info['path']}
Purpose: {file_info['purpose']}

Current Content:
```
{current_content}
```

Implementation Requirements:
{json.dumps(feature_plan.get('code_changes', []), indent=2)}

Please generate the complete file content that implements the required changes.
Follow these guidelines:
1. Maintain existing code style and patterns
2. Add proper error handling
3. Include appropriate comments
4. Follow best practices for the language/framework
5. Ensure the code is production-ready

Return only the complete file content, no explanations or markdown formatting.
"""
        
        try:
            response_data = await self.llm_client.call_llm(
                model=self.model,
                prompt=prompt,
                max_tokens=6000,
                temperature=0.2
            )
            
            # Extract the response content
            response = response_data.get("response", "") if isinstance(response_data, dict) else str(response_data)
            
            return response.strip()
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to generate content for {file_info['path']}: {str(e)}",
                level=LogLevel.ERROR
            )
            raise
    
    def _generate_branch_name(self, feature_prompt: str) -> str:
        """Generate a branch name from the feature prompt"""
        # Clean and format the prompt for branch name
        branch_name = re.sub(r'[^a-zA-Z0-9\s-]', '', feature_prompt.lower())
        branch_name = re.sub(r'\s+', '-', branch_name.strip())
        branch_name = branch_name[:50]  # Limit length
        
        # Add prefix and timestamp
        timestamp = int(time.time())
        return f"feature/{branch_name}-{timestamp}"
    
    async def _create_feature_branch(self, repo_info: Dict[str, str], base_branch: str, branch_name: str) -> bool:
        """Create a new feature branch using MCP GitHub tools"""
        try:
            # Use the MCP github_create_branch tool
            result = await self._call_github_create_branch(
                repo=repo_info["repo"],
                owner=repo_info["owner"],
                branch=branch_name,
                from_branch=base_branch
            )
            
            if result.get("success"):
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Created feature branch: {branch_name}",
                    metadata={"base_branch": base_branch, "branch_name": branch_name}
                )
                return True
            else:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=f"Failed to create branch {branch_name}: {result.get('error', 'Unknown error')}",
                    level=LogLevel.ERROR
                )
                return False
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to create branch {branch_name}: {str(e)}",
                level=LogLevel.ERROR
            )
            return False
    
    async def _call_github_create_branch(self, repo: str, owner: str, branch: str, from_branch: str = "main") -> Dict[str, Any]:
        """Call the MCP GitHub create branch tool"""
        try:
            # This simulates calling the github_create_branch tool
            import os
            
            # Check if we have a GitHub token
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                return {
                    "success": False,
                    "error": "GITHUB_TOKEN environment variable not set"
                }
            
            # Update the GitHub client to use the token
            self.github_client.headers["Authorization"] = f"token {github_token}"
            
            # Get the SHA of the base branch
            base_ref = self.github_client._make_request(
                "GET",
                f"repos/{owner}/{repo}/git/ref/heads/{from_branch}"
            )
            
            base_sha = base_ref["object"]["sha"]
            
            # Create new branch
            response = self.github_client._make_request(
                "POST",
                f"repos/{owner}/{repo}/git/refs",
                {
                    "ref": f"refs/heads/{branch}",
                    "sha": base_sha
                }
            )
            
            return {
                "success": True,
                "branch_name": branch,
                "from_branch": from_branch,
                "sha": base_sha,
                "ref": response.get("ref")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create branch: {str(e)}"
            }
    
    async def _apply_code_changes(self, repo_info: Dict[str, str], branch_name: str, code_changes: List[Dict[str, Any]]) -> List[str]:
        """Apply code changes to the feature branch using MCP GitHub tools"""
        modified_files = []
        
        # Prepare all files for batch push
        files_to_push = []
        
        for change in code_changes:
            try:
                file_path = change["file_path"]
                new_content = change["new_content"]
                
                # Add to files list for batch push
                files_to_push.append({
                    "path": file_path,
                    "content": new_content
                })
                
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Prepared changes for {file_path}",
                    metadata={"action": change["action"], "branch": branch_name}
                )
                
            except Exception as e:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=f"Failed to prepare changes for {change['file_path']}: {str(e)}",
                    level=LogLevel.ERROR
                )
        
        # Push all files in a single commit using MCP GitHub tools
        if files_to_push:
            try:
                # Use the actual MCP GitHub tools available in the system
                # We'll use the github_push_files tool directly
                
                # Prepare files in the format expected by github_push_files
                files_json = json.dumps(files_to_push)
                commit_message = f"Implement feature: {len(files_to_push)} files modified"
                
                # Call the MCP GitHub tool directly
                # This simulates calling the github_push_files tool
                result = await self._call_github_push_files(
                    repo=repo_info["repo"],
                    owner=repo_info["owner"],
                    branch=branch_name,
                    files=files_json,
                    message=commit_message
                )
                
                if result.get("success"):
                    modified_files = [f["path"] for f in files_to_push]
                    
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_COMPLETE,
                        message=f"Successfully pushed {len(files_to_push)} files to {branch_name}",
                        metadata={"files": modified_files, "branch": branch_name}
                    )
                else:
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=f"Failed to push files: {result.get('error', 'Unknown error')}",
                        level=LogLevel.ERROR
                    )
                    
                    # Fallback to direct tool calls
                    modified_files = await self._apply_code_changes_direct(repo_info, branch_name, code_changes)
                    
            except Exception as e:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=f"Failed to push files using MCP tools: {str(e)}",
                    level=LogLevel.ERROR
                )
                
                # Fallback to direct tool calls
                modified_files = await self._apply_code_changes_direct(repo_info, branch_name, code_changes)
        
        return modified_files
    
    async def _call_github_push_files(self, repo: str, owner: str, branch: str, files: str, message: str) -> Dict[str, Any]:
        """Call the MCP GitHub push files tool"""
        try:
            # This method simulates calling the actual MCP github_push_files tool
            # In a real MCP environment, this would be handled by the MCP server
            
            # Parse the files JSON
            files_data = json.loads(files)
            
            # Use our GitHub client with proper error handling and logging
            import base64
            import os
            
            # Check if we have a GitHub token
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                return {
                    "success": False,
                    "error": "GITHUB_TOKEN environment variable not set"
                }
            
            # Update the GitHub client to use the token
            self.github_client.headers["Authorization"] = f"token {github_token}"
            
            files_pushed = []
            
            for file_data in files_data:
                try:
                    file_path = file_data["path"]
                    content = file_data["content"]
                    
                    # Encode content to base64
                    encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
                    
                    # Prepare commit data
                    commit_data = {
                        "message": f"{message} - {file_path}",
                        "content": encoded_content,
                        "branch": branch
                    }
                    
                    # Check if file exists to get SHA for updates
                    try:
                        current_file = self.github_client._make_request(
                            "GET",
                            f"repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
                        )
                        commit_data["sha"] = current_file["sha"]
                    except:
                        pass  # File doesn't exist, will be created
                    
                    # Create or update the file
                    response = self.github_client._make_request(
                        "PUT",
                        f"repos/{owner}/{repo}/contents/{file_path}",
                        commit_data
                    )
                    
                    files_pushed.append(file_path)
                    
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_COMPLETE,
                        message=f"Successfully pushed {file_path} to {branch}",
                        metadata={"file": file_path, "branch": branch, "commit_sha": response.get("commit", {}).get("sha")}
                    )
                    
                except Exception as e:
                    self.logger.log_event(
                        agent_id=self.agent_id,
                        event_type=EventType.TASK_ERROR,
                        message=f"Failed to push {file_data.get('path', 'unknown')}: {str(e)}",
                        level=LogLevel.ERROR
                    )
                    return {
                        "success": False,
                        "error": f"Failed to push {file_data.get('path', 'unknown')}: {str(e)}"
                    }
            
            return {
                "success": True,
                "files_pushed": files_pushed,
                "total_files": len(files_pushed),
                "branch": branch,
                "message": message
            }
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to call github_push_files: {str(e)}",
                level=LogLevel.ERROR
            )
            return {
                "success": False,
                "error": f"Failed to call github_push_files: {str(e)}"
            }
    
    async def _call_github_create_pull_request(self, repo: str, owner: str, title: str, body: str, head: str, base: str = "main") -> Dict[str, Any]:
        """Call the MCP GitHub create pull request tool"""
        try:
            # This simulates calling the github_create_pull_request tool
            import os
            
            # Check if we have a GitHub token
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                return {
                    "success": False,
                    "error": "GITHUB_TOKEN environment variable not set"
                }
            
            # Update the GitHub client to use the token
            self.github_client.headers["Authorization"] = f"token {github_token}"
            
            # Create pull request
            pr_data = {
                "title": title,
                "body": body,
                "head": head,
                "base": base,
                "draft": False
            }
            
            pr_response = self.github_client._make_request(
                "POST",
                f"repos/{owner}/{repo}/pulls",
                pr_data
            )
            
            return {
                "success": True,
                "pr_url": pr_response.get("html_url"),
                "pr_number": pr_response.get("number"),
                "title": title,
                "head": head,
                "base": base
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create pull request: {str(e)}"
            }
    
    async def _apply_code_changes_direct(self, repo_info: Dict[str, str], branch_name: str, code_changes: List[Dict[str, Any]]) -> List[str]:
        """Fallback method using direct GitHub API calls"""
        modified_files = []
        
        for change in code_changes:
            try:
                file_path = change["file_path"]
                new_content = change["new_content"]
                
                # Encode content
                import base64
                encoded_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
                
                # Prepare commit data
                commit_data = {
                    "message": f"Implement: {change['purpose']}",
                    "content": encoded_content,
                    "branch": branch_name
                }
                
                # Get current file SHA if it exists (for updates)
                if change["action"] == "modify":
                    try:
                        current_file = self.github_client._make_request(
                            "GET",
                            f"repos/{repo_info['full_name']}/contents/{file_path}?ref={branch_name}"
                        )
                        commit_data["sha"] = current_file["sha"]
                    except:
                        pass  # File doesn't exist, will be created
                
                # Create or update file
                response = self.github_client._make_request(
                    "PUT",
                    f"repos/{repo_info['full_name']}/contents/{file_path}",
                    commit_data
                )
                
                # Log the response for debugging
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"GitHub API response for {file_path}",
                    metadata={"response": response, "status": "success"}
                )
                
                modified_files.append(file_path)
                
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Applied changes to {file_path}",
                    metadata={"action": change["action"], "branch": branch_name}
                )
                
            except Exception as e:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=f"Failed to apply changes to {change['file_path']}: {str(e)}",
                    level=LogLevel.ERROR,
                    metadata={"error_details": str(e), "file_path": change["file_path"]}
                )
        
        return modified_files
    
    async def _create_pull_request(self, repo_info: Dict[str, str], feature_branch: str, base_branch: str, feature_plan: Dict[str, Any], original_prompt: str) -> Dict[str, Any]:
        """Create a pull request for the implemented feature"""
        try:
            # Generate PR title and description
            pr_title = f"Feature: {feature_plan.get('feature_analysis', {}).get('summary', 'New feature implementation')}"
            
            pr_description = f"""## Feature Implementation

**Original Request:** {original_prompt}

### Summary
{feature_plan.get('feature_analysis', {}).get('summary', 'Feature implementation')}

### Changes Made
"""
            
            # Add files modified
            files_modified = feature_plan.get('files_to_modify', [])
            if files_modified:
                pr_description += "\n#### Files Modified:\n"
                for file_info in files_modified:
                    pr_description += f"- `{file_info['path']}` - {file_info['purpose']}\n"
            
            # Add dependencies if any
            dependencies = feature_plan.get('dependencies', [])
            if dependencies:
                pr_description += "\n#### New Dependencies:\n"
                for dep in dependencies:
                    pr_description += f"- `{dep['name']}` ({dep['version']}) - {dep['purpose']}\n"
            
            # Add testing information
            testing = feature_plan.get('testing_strategy', {})
            if testing:
                pr_description += "\n#### Testing\n"
                if testing.get('manual_testing'):
                    pr_description += "**Manual Testing Steps:**\n"
                    for step in testing['manual_testing']:
                        pr_description += f"1. {step}\n"
            
            # Add potential issues
            issues = feature_plan.get('potential_issues', [])
            if issues:
                pr_description += "\n#### Potential Issues & Mitigations\n"
                for issue in issues:
                    pr_description += f"- **Issue:** {issue['issue']}\n"
                    pr_description += f"  **Mitigation:** {issue['mitigation']}\n"
            
            pr_description += f"\n---\n*This PR was automatically generated by MCP GitHub Analyzer*"
            
            # Create pull request using MCP GitHub tools
            pr_result = await self._call_github_create_pull_request(
                repo=repo_info["repo"],
                owner=repo_info["owner"],
                title=pr_title,
                body=pr_description,
                head=feature_branch,
                base=base_branch
            )
            
            if pr_result.get("success"):
                pr_url = pr_result.get("pr_url")
                
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_COMPLETE,
                    message=f"Created pull request: {pr_url}",
                    metadata={
                        "pr_number": pr_result.get("pr_number"),
                        "feature_branch": feature_branch,
                        "base_branch": base_branch
                    }
                )
                
                return {
                    "success": True,
                    "pr_url": pr_url,
                    "pr_number": pr_result.get("pr_number"),
                    "pr_title": pr_title
                }
            else:
                self.logger.log_event(
                    agent_id=self.agent_id,
                    event_type=EventType.TASK_ERROR,
                    message=f"Failed to create pull request: {pr_result.get('error', 'Unknown error')}",
                    level=LogLevel.ERROR
                )
                
                return {
                    "success": False,
                    "error": pr_result.get("error", "Unknown error")
                }
            
        except Exception as e:
            self.logger.log_event(
                agent_id=self.agent_id,
                event_type=EventType.TASK_ERROR,
                message=f"Failed to create pull request: {str(e)}",
                level=LogLevel.ERROR
            )
            
            return {
                "success": False,
                "error": str(e)
            }

# Singleton instance
_feature_agent = None

def get_feature_agent() -> FeatureAgent:
    """Get the singleton FeatureAgent instance"""
    global _feature_agent
    if _feature_agent is None:
        _feature_agent = FeatureAgent()
    return _feature_agent
