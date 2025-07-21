import requests
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentDiscovery:
    def __init__(self, api_base_url: str = "https://api.example.com/agents"):
        self.api_base_url = api_base_url
        self.session = requests.Session()

    def search_agents(self, query: str, filters: Optional[Dict] = None) -> List[Dict]:
        """
        Search for AI agents based on query and optional filters
        
        Args:
            query (str): Search query string
            filters (dict, optional): Additional filter parameters
            
        Returns:
            List[Dict]: List of matching agent records
        """
        try:
            params = {"q": query}
            if filters:
                params.update(filters)
                
            response = self.session.get(
                f"{self.api_base_url}/search",
                params=params
            )
            response.raise_for_status()
            
            return response.json().get("agents", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching agents: {str(e)}")
            return []

    def get_agent_details(self, agent_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific agent
        
        Args:
            agent_id (str): Unique identifier of the agent
            
        Returns:
            Optional[Dict]: Agent details or None if not found
        """
        try:
            response = self.session.get(f"{self.api_base_url}/{agent_id}")
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching agent details: {str(e)}")
            return None

    def integrate_agent(self, agent_id: str, integration_params: Dict) -> bool:
        """
        Integrate an AI agent with the current system
        
        Args:
            agent_id (str): ID of the agent to integrate
            integration_params (Dict): Integration configuration parameters
            
        Returns:
            bool: True if integration successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.api_base_url}/{agent_id}/integrate",
                json=integration_params
            )
            response.raise_for_status()
            
            return response.json().get("success", False)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error integrating agent: {str(e)}")
            return False

    def validate_agent_compatibility(self, agent_id: str) -> Dict:
        """
        Check if an agent is compatible with the current system
        
        Args:
            agent_id (str): ID of the agent to validate
            
        Returns:
            Dict: Compatibility check results
        """
        try:
            response = self.session.get(
                f"{self.api_base_url}/{agent_id}/compatibility"
            )
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error validating agent compatibility: {str(e)}")
            return {"compatible": False, "errors": [str(e)]}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()