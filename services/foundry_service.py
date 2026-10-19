"""
services/foundry_service.py
Microsoft Azure AI Foundry connection and client management.
Uses DefaultAzureCredential for authenticating against Azure AI Projects.
"""

import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Ensure environment variables are loaded
load_dotenv()


class FoundryService:
    """Manages connection to Microsoft Azure AI Foundry project and agents."""

    def __init__(self):
        self.endpoint = os.getenv("FOUNDRY_PROJECT_ENDPOINT")
        self.model_name = os.getenv("FOUNDRY_MODEL", "gpt-4.1-mini")
        self.agent_name = os.getenv("FOUNDRY_AGENT_NAME", "AI-Interview-Coach")
        self._project_client: Optional[AIProjectClient] = None
        self._openai_client = None
        self._cached_agent_details: Optional[Dict[str, Any]] = None
        self._cached_connection_status: Optional[Dict[str, Any]] = None

        if not self.endpoint:
            raise ValueError(
                "FOUNDRY_PROJECT_ENDPOINT is not set in your .env file. "
                "Please configure it with your Azure AI Foundry project endpoint URL."
            )

    def get_project_client(self) -> AIProjectClient:
        """Returns or creates the authenticated AIProjectClient."""
        if self._project_client is None:
            credential = DefaultAzureCredential()
            self._project_client = AIProjectClient(
                endpoint=self.endpoint,
                credential=credential
            )
        return self._project_client

    def get_openai_client(self):
        """Returns the project-scoped OpenAI client for Responses and Vector Stores."""
        if self._openai_client is None:
            project_client = self.get_project_client()
            self._openai_client = project_client.get_openai_client()
        return self._openai_client

    def get_agent_details(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches the agent definition directly from Microsoft Foundry.
        Caches the definition to avoid repetitive remote network calls.
        """
        if self._cached_agent_details is not None and not agent_name:
            return self._cached_agent_details

        name = agent_name or self.agent_name
        project_client = self.get_project_client()

        try:
            agent = project_client.agents.get(name)
            agent_dict = agent.as_dict() if hasattr(agent, "as_dict") else dict(agent)
            latest_version = agent_dict.get("versions", {}).get("latest", {})
            definition = latest_version.get("definition", {})

            details = {
                "id": agent_dict.get("id", name),
                "name": agent_dict.get("name", name),
                "model": definition.get("model", self.model_name),
                "instructions": definition.get("instructions", ""),
                "tools": definition.get("tools", []),
                "status": "ready"
            }
            if not agent_name:
                self._cached_agent_details = details
            return details
        except Exception as e:
            fallback = {
                "id": name,
                "name": name,
                "model": self.model_name,
                "instructions": (
                    "You are an AI Interview Coach conducting a realistic, structured, "
                    "and adaptive interview. Ask one grounded question at a time."
                ),
                "tools": [{"type": "file_search"}],
                "status": f"fallback: {str(e)}"
            }
            return fallback

    def verify_connection(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Checks Foundry project connectivity, lists available agents, and returns health status.
        Results are cached to keep Streamlit UI responsive.
        """
        if self._cached_connection_status is not None and not force_refresh:
            return self._cached_connection_status

        try:
            client = self.get_project_client()
            agents_list = []
            for agent in client.agents.list():
                agents_list.append({
                    "name": getattr(agent, "name", "Unnamed"),
                    "id": getattr(agent, "id", "Unknown")
                })
            status = {
                "success": True,
                "endpoint": self.endpoint,
                "model": self.model_name,
                "agents": agents_list
            }
            self._cached_connection_status = status
            return status
        except Exception as e:
            return {
                "success": False,
                "endpoint": self.endpoint,
                "error": str(e)
            }


# Global singleton instance for easy import
_foundry_instance: Optional[FoundryService] = None


def get_foundry_service() -> FoundryService:
    global _foundry_instance
    if _foundry_instance is None:
        _foundry_instance = FoundryService()
    return _foundry_instance
