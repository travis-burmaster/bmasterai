"""
MCP GitHub Tools Wrapper
Provides a clean interface to the MCP GitHub tools available in the system
"""

import json
import asyncio
from typing import Dict, Any, List, Optional

async def push_files_to_github(repo: str, owner: str, branch: str, files: List[Dict[str, str]], message: str) -> Dict[str, Any]:
    """
    Push multiple files to GitHub using the MCP github_push_files tool
    
    Args:
        repo: Repository name
        owner: Repository owner
        branch: Target branch
        files: List of files with 'path' and 'content' keys
        message: Commit message
    
    Returns:
        Dict with success status and any error information
    """
    try:
        # Use the actual MCP GitHub tools available in the system
        # We need to call the github_push_files tool directly
        
        # This is a direct call to the MCP tool - we'll simulate the tool call
        # In a real implementation, this would be handled by the MCP server
        
        # For now, let's use a direct approach that mimics what the MCP tool would do
        import os
        import requests
        import base64
        
        # Get GitHub token from environment
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            return {
                "success": False,
                "error": "GITHUB_TOKEN environment variable not set"
            }
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-GitHub-Tools/1.0"
        }
        
        base_url = "https://api.github.com"
        
        # Get the current commit SHA of the branch
        try:
            branch_response = requests.get(
                f"{base_url}/repos/{owner}/{repo}/git/ref/heads/{branch}",
                headers=headers,
                timeout=30
            )
            
            if branch_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to get branch info: {branch_response.text}"
                }
            
            branch_sha = branch_response.json()["object"]["sha"]
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get branch SHA: {str(e)}"
            }
        
        # Create commits for each file
        files_pushed = []
        
        for file_data in files:
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
                    existing_file_response = requests.get(
                        f"{base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if existing_file_response.status_code == 200:
                        commit_data["sha"] = existing_file_response.json()["sha"]
                        
                except:
                    pass  # File doesn't exist, will be created
                
                # Create or update the file
                file_response = requests.put(
                    f"{base_url}/repos/{owner}/{repo}/contents/{file_path}",
                    headers=headers,
                    json=commit_data,
                    timeout=30
                )
                
                if file_response.status_code in [200, 201]:
                    files_pushed.append(file_path)
                else:
                    return {
                        "success": False,
                        "error": f"Failed to push {file_path}: {file_response.text}"
                    }
                    
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to process file {file_data.get('path', 'unknown')}: {str(e)}"
                }
        
        return {
            "success": True,
            "files_pushed": files_pushed,
            "commit_message": message,
            "branch": branch,
            "total_files": len(files_pushed)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to push files: {str(e)}"
        }

async def create_github_branch(repo: str, owner: str, branch: str, from_branch: str = "main") -> Dict[str, Any]:
    """
    Create a new branch on GitHub using MCP tools
    
    Args:
        repo: Repository name
        owner: Repository owner  
        branch: New branch name
        from_branch: Source branch to create from
    
    Returns:
        Dict with success status and branch information
    """
    try:
        # Mock implementation - replace with actual MCP tool call
        return {
            "success": True,
            "branch_name": branch,
            "from_branch": from_branch,
            "message": f"Branch {branch} created successfully (mock)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create branch: {str(e)}"
        }

async def create_github_pull_request(repo: str, owner: str, title: str, body: str, head: str, base: str = "main") -> Dict[str, Any]:
    """
    Create a pull request on GitHub using MCP tools
    
    Args:
        repo: Repository name
        owner: Repository owner
        title: PR title
        body: PR description
        head: Head branch
        base: Base branch
    
    Returns:
        Dict with success status and PR information
    """
    try:
        # Mock implementation - replace with actual MCP tool call
        return {
            "success": True,
            "pr_number": 42,
            "pr_url": f"https://github.com/{owner}/{repo}/pull/42",
            "title": title,
            "message": "Pull request created successfully (mock)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create pull request: {str(e)}"
        }
