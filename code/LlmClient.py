import requests
import json
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

    def send_prompt(self, payload: Dict[str, Any]) -> str:
        payload["stream"] = True  # Enable streaming
        result = ""

        with requests.post(
            self.url,
            headers=self.headers,
            json=payload,
            verify=False,
            timeout=100,
            stream=True,
        ) as response:
            print(f"LLM response status: {response.status_code}")
            response.raise_for_status()

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    if line.strip() == "data: [DONE]":
                        break
                    try:
                        line_data = line.strip().removeprefix("data: ")
                        delta = json.loads(line_data)
                        content_piece = (
                            delta["choices"][0].get("delta", {}).get("content")
                        )
                        if content_piece:
                            result += content_piece
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e} - line: {line}")
                    except (KeyError, IndexError) as e:
                        print(f"Unexpected format: {e} - delta: {delta}")

        return result
