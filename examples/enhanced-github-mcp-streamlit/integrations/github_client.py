
"""GitHub API client for repository operations"""
import os
import requests
import time
from typing import Dict, Any, List, Optional
from utils.bmasterai_logging import get_logger, EventType, LogLevel
from utils.bmasterai_monitoring import get_monitor

class GitHubClient:
    """GitHub API client with BMasterAI logging and monitoring"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.base_url = "https://api.github.com"
        self.logger = get_logger()
        self.monitor = get_monitor()
        
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-GitHub-Analyzer/1.0"
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to GitHub API with logging and monitoring"""
        url = f"{self.base_url}/{endpoint}"
        start_time = time.time()
        
        # Log GitHub operation start
        self.logger.log_event(
            agent_id="github_client",
            event_type=EventType.GITHUB_OPERATION,
            message=f"GitHub {method} request to {endpoint}",
            metadata={"url": url, "method": method, "has_data": data is not None}
        )
        
        try:
            response = requests.request(
                method, 
                url, 
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201, 202]:
                result = response.json() if response.content else {}
                
                # Log successful operation
                self.logger.log_event(
                    agent_id="github_client",
                    event_type=EventType.TASK_COMPLETE,
                    message=f"GitHub {method} to {endpoint} completed",
                    duration_ms=duration_ms,
                    metadata={
                        "status": response.status_code,
                        "result_size": len(str(result)),
                        "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining")
                    }
                )
                
                return result
            else:
                error_msg = f"GitHub API request failed with status {response.status_code}: {response.text}"
                
                # Log error
                self.logger.log_event(
                    agent_id="github_client",
                    event_type=EventType.TASK_ERROR,
                    message=error_msg,
                    level=LogLevel.ERROR,
                    duration_ms=duration_ms,
                    metadata={
                        "status": response.status_code,
                        "error": response.text,
                        "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining")
                    }
                )
                
                raise Exception(error_msg)
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.log_event(
                agent_id="github_client",
                event_type=EventType.TASK_ERROR,
                message=f"GitHub request error: {str(e)}",
                level=LogLevel.ERROR,
                duration_ms=duration_ms,
                metadata={"error": str(e), "url": url}
            )
            
            # Track error in monitoring
            self.monitor.track_error("github_client", "request_error")
            
            raise
    
    def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """Get repository information from GitHub API"""
        # Extract owner and repo from URL
        parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = parts
        endpoint = f"repos/{owner}/{repo}"
        
        return self._make_request("GET", endpoint)
    
    def get_repository_contents(self, repo_url: str, path: str = "") -> List[Dict[str, Any]]:
        """Get repository contents"""
        parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = parts
        endpoint = f"repos/{owner}/{repo}/contents/{path}"
        
        result = self._make_request("GET", endpoint)
        return result if isinstance(result, list) else [result]
    
    def get_file_content(self, repo_url: str, file_path: str) -> str:
        """Get content of a specific file"""
        parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = parts
        endpoint = f"repos/{owner}/{repo}/contents/{file_path}"
        
        result = self._make_request("GET", endpoint)
        
        if result.get("encoding") == "base64":
            import base64
            return base64.b64decode(result["content"]).decode("utf-8")
        else:
            return result.get("content", "")
    
    def get_repository_languages(self, repo_url: str) -> Dict[str, int]:
        """Get repository programming languages"""
        parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = parts
        endpoint = f"repos/{owner}/{repo}/languages"
        
        return self._make_request("GET", endpoint)
    
    def get_repository_stats(self, repo_url: str) -> Dict[str, Any]:
        """Get repository statistics"""
        parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = parts
        
        # Get basic repo info
        repo_info = self.get_repository_info(repo_url)
        
        # Get languages
        try:
            languages = self.get_repository_languages(repo_url)
        except:
            languages = {}
        
        # Get recent commits
        try:
            commits_endpoint = f"repos/{owner}/{repo}/commits"
            recent_commits = self._make_request("GET", commits_endpoint + "?per_page=10")
        except:
            recent_commits = []
        
        return {
            "basic_info": repo_info,
            "languages": languages,
            "recent_commits": recent_commits,
            "stats": {
                "stars": repo_info.get("stargazers_count", 0),
                "forks": repo_info.get("forks_count", 0),
                "size": repo_info.get("size", 0),
                "open_issues": repo_info.get("open_issues_count", 0),
                "default_branch": repo_info.get("default_branch", "main"),
                "created_at": repo_info.get("created_at"),
                "updated_at": repo_info.get("updated_at"),
                "pushed_at": repo_info.get("pushed_at")
            }
        }
    
    def search_code(self, repo_url: str, query: str) -> List[Dict[str, Any]]:
        """Search for code in repository"""
        parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = parts
        search_query = f"{query} repo:{owner}/{repo}"
        endpoint = f"search/code?q={search_query}&per_page=10"
        
        try:
            result = self._make_request("GET", endpoint)
            return result.get("items", [])
        except Exception as e:
            # Code search requires authentication and may have limits
            self.logger.log_event(
                agent_id="github_client",
                event_type=EventType.TASK_ERROR,
                message=f"Code search failed: {str(e)}",
                level=LogLevel.WARNING,
                metadata={"query": query, "repo": f"{owner}/{repo}"}
            )
            return []
    
    def get_repository_topics(self, repo_url: str) -> List[str]:
        """Get repository topics/tags"""
        parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
        
        owner, repo = parts
        endpoint = f"repos/{owner}/{repo}/topics"
        
        try:
            result = self._make_request("GET", endpoint)
            return result.get("names", [])
        except:
            return []
    
    def check_repository_health(self, repo_url: str) -> Dict[str, Any]:
        """Check repository health indicators"""
        repo_info = self.get_repository_info(repo_url)
        
        health_score = 0
        health_factors = []
        
        # Check for README
        try:
            self.get_file_content(repo_url, "README.md")
            health_score += 20
            health_factors.append("Has README")
        except:
            try:
                self.get_file_content(repo_url, "README.txt")
                health_score += 15
                health_factors.append("Has README (txt)")
            except:
                health_factors.append("Missing README")
        
        # Check for LICENSE
        try:
            self.get_file_content(repo_url, "LICENSE")
            health_score += 15
            health_factors.append("Has LICENSE")
        except:
            health_factors.append("Missing LICENSE")
        
        # Check for recent activity (updated within last 6 months)
        import datetime
        if repo_info.get("pushed_at"):
            pushed_date = datetime.datetime.fromisoformat(repo_info["pushed_at"].replace("Z", "+00:00"))
            six_months_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=180)
            
            if pushed_date > six_months_ago:
                health_score += 25
                health_factors.append("Recently active")
            else:
                health_factors.append("Not recently active")
        
        # Check for community engagement
        stars = repo_info.get("stargazers_count", 0)
        if stars > 100:
            health_score += 20
            health_factors.append(f"Good community engagement ({stars} stars)")
        elif stars > 10:
            health_score += 10
            health_factors.append(f"Some community engagement ({stars} stars)")
        else:
            health_factors.append(f"Limited community engagement ({stars} stars)")
        
        # Check for documentation
        try:
            docs_contents = self.get_repository_contents(repo_url, "docs")
            if docs_contents:
                health_score += 10
                health_factors.append("Has documentation directory")
        except:
            pass
        
        # Check for tests
        try:
            test_contents = self.get_repository_contents(repo_url, "tests")
            if test_contents:
                health_score += 10
                health_factors.append("Has tests directory")
        except:
            try:
                test_contents = self.get_repository_contents(repo_url, "test")
                if test_contents:
                    health_score += 10
                    health_factors.append("Has test directory")
            except:
                health_factors.append("No obvious test directory")
        
        health_level = "Poor"
        if health_score >= 80:
            health_level = "Excellent"
        elif health_score >= 60:
            health_level = "Good"
        elif health_score >= 40:
            health_level = "Fair"
        
        return {
            "score": min(health_score, 100),
            "level": health_level,
            "factors": health_factors,
            "recommendations": self._get_health_recommendations(health_factors)
        }
    
    def _get_health_recommendations(self, factors: List[str]) -> List[str]:
        """Get health improvement recommendations"""
        recommendations = []
        
        if "Missing README" in factors:
            recommendations.append("Add a comprehensive README.md file")
        
        if "Missing LICENSE" in factors:
            recommendations.append("Add a LICENSE file to clarify usage terms")
        
        if "Not recently active" in factors:
            recommendations.append("Consider updating the repository with recent changes")
        
        if "Limited community engagement" in factors:
            recommendations.append("Improve documentation and add more features to attract users")
        
        if "No obvious test directory" in factors:
            recommendations.append("Add automated tests to improve code quality")
        
        return recommendations

def get_github_client() -> GitHubClient:
    """Get GitHub client instance"""
    return GitHubClient()
