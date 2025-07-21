
"""MCP (Model Context Protocol) client for GitHub operations"""
import asyncio
import json
import aiohttp
import time
from typing import Dict, Any, List, Optional
from utils.bmasterai_logging import get_logger, EventType, LogLevel
from utils.bmasterai_monitoring import get_monitor

class MCPGitClient:
    """MCP client for Git operations"""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8080):
        self.server_host = server_host
        self.server_port = server_port
        self.base_url = f"http://{server_host}:{server_port}"
        self.logger = get_logger()
        self.monitor = get_monitor()
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the MCP server"""
        url = f"{self.base_url}/{endpoint}"
        start_time = time.time()
        
        # Log MCP operation start
        self.logger.log_event(
            agent_id="mcp_client",
            event_type=EventType.MCP_OPERATION,
            message=f"MCP {method} request to {endpoint}",
            metadata={"url": url, "method": method, "data": data}
        )
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.request(
                method, 
                url, 
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    result = await response.json()
                    
                    # Log successful operation
                    self.logger.log_event(
                        agent_id="mcp_client",
                        event_type=EventType.TASK_COMPLETE,
                        message=f"MCP {method} to {endpoint} completed",
                        duration_ms=duration_ms,
                        metadata={"status": response.status, "result_size": len(str(result))}
                    )
                    
                    return result
                else:
                    error_text = await response.text()
                    error_msg = f"MCP request failed with status {response.status}: {error_text}"
                    
                    # Log error
                    self.logger.log_event(
                        agent_id="mcp_client",
                        event_type=EventType.TASK_ERROR,
                        message=error_msg,
                        level=LogLevel.ERROR,
                        duration_ms=duration_ms,
                        metadata={"status": response.status, "error": error_text}
                    )
                    
                    raise Exception(error_msg)
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.log_event(
                agent_id="mcp_client",
                event_type=EventType.TASK_ERROR,
                message=f"MCP request error: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"error": str(e), "url": url}
            )
            
            # Track error in monitoring
            self.monitor.track_error("mcp_client", "request_error")
            
            raise
    
    async def clone_repository(self, repo_url: str, target_path: str) -> Dict[str, Any]:
        """Clone a Git repository"""
        data = {
            "repository_url": repo_url,
            "target_path": target_path
        }
        return await self._make_request("POST", "git/clone", data)
    
    async def create_branch(self, repo_path: str, branch_name: str, from_branch: str = "main") -> Dict[str, Any]:
        """Create a new Git branch"""
        data = {
            "repository_path": repo_path,
            "branch_name": branch_name,
            "from_branch": from_branch
        }
        return await self._make_request("POST", "git/branch/create", data)
    
    async def commit_changes(self, repo_path: str, message: str, files: List[str] = None) -> Dict[str, Any]:
        """Commit changes to the repository"""
        data = {
            "repository_path": repo_path,
            "commit_message": message,
            "files": files or []
        }
        return await self._make_request("POST", "git/commit", data)
    
    async def push_branch(self, repo_path: str, branch_name: str, remote: str = "origin") -> Dict[str, Any]:
        """Push branch to remote repository"""
        data = {
            "repository_path": repo_path,
            "branch_name": branch_name,
            "remote": remote
        }
        return await self._make_request("POST", "git/push", data)
    
    async def create_pull_request(self, repo_path: str, title: str, description: str, 
                                head_branch: str, base_branch: str = "main") -> Dict[str, Any]:
        """Create a pull request"""
        data = {
            "repository_path": repo_path,
            "title": title,
            "description": description,
            "head_branch": head_branch,
            "base_branch": base_branch
        }
        return await self._make_request("POST", "git/pull-request", data)
    
    async def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """Get repository information"""
        data = {"repository_url": repo_url}
        return await self._make_request("POST", "git/info", data)
    
    async def list_files(self, repo_path: str, pattern: str = "*") -> Dict[str, Any]:
        """List files in repository"""
        data = {
            "repository_path": repo_path,
            "pattern": pattern
        }
        return await self._make_request("POST", "git/files", data)
    
    async def read_file(self, repo_path: str, file_path: str) -> Dict[str, Any]:
        """Read a file from repository"""
        data = {
            "repository_path": repo_path,
            "file_path": file_path
        }
        return await self._make_request("POST", "git/read", data)
    
    async def write_file(self, repo_path: str, file_path: str, content: str) -> Dict[str, Any]:
        """Write content to a file in repository"""
        data = {
            "repository_path": repo_path,
            "file_path": file_path,
            "content": content
        }
        return await self._make_request("POST", "git/write", data)
    
    async def get_diff(self, repo_path: str, from_branch: str, to_branch: str) -> Dict[str, Any]:
        """Get diff between branches"""
        data = {
            "repository_path": repo_path,
            "from_branch": from_branch,
            "to_branch": to_branch
        }
        return await self._make_request("POST", "git/diff", data)

class MockMCPClient:
    """Mock MCP client for testing when MCP server is not available"""
    
    def __init__(self, server_host: str = "localhost", server_port: int = 8080):
        self.server_host = server_host
        self.server_port = server_port
        self.logger = get_logger()
        self.monitor = get_monitor()
        self._mock_repos = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def clone_repository(self, repo_url: str, target_path: str) -> Dict[str, Any]:
        """Mock clone repository"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        # Extract repo name from URL
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        self._mock_repos[target_path] = {
            "url": repo_url,
            "name": repo_name,
            "branches": ["main"],
            "files": {
                "README.md": "# Mock Repository\n\nThis is a mock repository for testing.",
                "src/main.py": "print('Hello, World!')",
                "requirements.txt": "requests>=2.25.0",
                ".gitignore": "*.pyc\n__pycache__/\n.env"
            }
        }
        
        return {
            "success": True,
            "repository_path": target_path,
            "repository_name": repo_name,
            "message": f"Successfully cloned {repo_url} to {target_path}"
        }
    
    async def create_branch(self, repo_path: str, branch_name: str, from_branch: str = "main") -> Dict[str, Any]:
        """Mock create branch"""
        await asyncio.sleep(0.1)
        
        if repo_path in self._mock_repos:
            self._mock_repos[repo_path]["branches"].append(branch_name)
            return {
                "success": True,
                "branch_name": branch_name,
                "message": f"Created branch {branch_name} from {from_branch}"
            }
        else:
            raise Exception(f"Repository not found: {repo_path}")
    
    async def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """Mock get repository info"""
        await asyncio.sleep(0.1)
        
        repo_name = repo_url.split('/')[-1].replace('.git', '')
        
        return {
            "success": True,
            "repository": {
                "name": repo_name,
                "url": repo_url,
                "description": f"Mock repository: {repo_name}",
                "default_branch": "main",
                "languages": ["Python", "JavaScript"],
                "stars": 42,
                "forks": 7,
                "size": 1024,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }
    
    async def list_files(self, repo_path: str, pattern: str = "*") -> Dict[str, Any]:
        """Mock list files"""
        await asyncio.sleep(0.1)
        
        if repo_path in self._mock_repos:
            files = list(self._mock_repos[repo_path]["files"].keys())
            return {
                "success": True,
                "files": files,
                "total_count": len(files)
            }
        else:
            raise Exception(f"Repository not found: {repo_path}")
    
    async def read_file(self, repo_path: str, file_path: str) -> Dict[str, Any]:
        """Mock read file"""
        await asyncio.sleep(0.1)
        
        if repo_path in self._mock_repos:
            files = self._mock_repos[repo_path]["files"]
            if file_path in files:
                return {
                    "success": True,
                    "file_path": file_path,
                    "content": files[file_path],
                    "size": len(files[file_path])
                }
            else:
                raise Exception(f"File not found: {file_path}")
        else:
            raise Exception(f"Repository not found: {repo_path}")
    
    async def commit_changes(self, repo_path: str, message: str, files: List[str] = None) -> Dict[str, Any]:
        """Mock commit changes"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "commit_hash": "abc123def456",
            "message": message,
            "files_changed": files or [],
            "timestamp": "2024-01-15T10:30:00Z"
        }
    
    async def create_pull_request(self, repo_path: str, title: str, description: str,
                                head_branch: str, base_branch: str = "main") -> Dict[str, Any]:
        """Mock create pull request"""
        await asyncio.sleep(0.1)
        
        return {
            "success": True,
            "pull_request": {
                "number": 42,
                "title": title,
                "description": description,
                "head_branch": head_branch,
                "base_branch": base_branch,
                "url": f"https://github.com/mock/repo/pull/42",
                "status": "open"
            }
        }

def get_mcp_client(use_mock: bool = True) -> MCPGitClient:
    """Get MCP client instance"""
    if use_mock:
        return MockMCPClient()
    else:
        return MCPGitClient()
