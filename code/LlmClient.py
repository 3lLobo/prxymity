import requests
from typing import Dict, Any


class LLMClient:
    def __init__(self, llm_host: str, llm_token: str) -> None:
        """
        Initialize the LLM client with the host and token.
        :param llm_host: The host URL for the LLM service.
        :param llm_token: The token for authenticating with the LLM service.
        """

        self.url = f"{llm_host}/v1beta/openai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {llm_token}",
            "Content-Type": "application/json",
        }

    def send_prompt(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload,
            verify=False,
            timeout=100,
        )
        print(f"LLM response status: {response.status_code}")
        return response.json()
