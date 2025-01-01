import os
from typing import Any, Dict, Optional, Union

from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
from openai import AsyncOpenAI

import ..jc_logging as logging
from ..job import JobABC


class OpenAIClient:
    """
    Singleton class for AsyncOpenAI client.
    """
    _client = None

    @classmethod
    def get_client(cls, api_key: str = None):
        if cls._client is None:
            # Load environment variables from api.env file
            load_dotenv("api.env")

            # Determine the API key
            api_key = api_key or os.getenv('OPENAI_API_KEY')

            # Optional: Check if the API key is not set and raise an error 
            if not api_key:
                raise ValueError("API key is not set. Please provide an API key.")
            cls._client = AsyncOpenAI(api_key=api_key)
        return cls._client

class OpenAIJob(JobABC):

    client = OpenAIClient.get_client()
    # Shared AsyncLimiter for all jobs, default to 5,000 requests per minute
    default_rate_limit = {"max_rate": 5000, "time_period": 60}

    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
        
        # Rate limiter configuration
        rate_limit_config = self.properties.get("rate_limit", self.default_rate_limit)
        self.limiter = AsyncLimiter(**rate_limit_config)

        # Extract other relevant properties for OpenAI client
        self.api_properties = self.properties.get("api", {})

    async def run(self, task: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """
        Perform an OpenAI API call while adhering to rate limits.
        """
        default_properties = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": task.get("prompt", "You are a helpful assistant.")}
            ],
            "temperature": 0.7,
        }

        # Merge default API properties with those specified in the properties
        request_properties = {**default_properties, **self.api_properties}

        # Acquire the rate limiter before making the request
        async with self.limiter:
            try:
                self.logger.info(f"{self.name} is making an OpenAI API call.")
                response = await self.client.chat.completions.create(**request_properties)
                self.logger.info(f"{self.name} received a response.")
                return {"response": response.choices[0].message.content}
            except Exception as e:
                self.logger.error(f"Error in {self.name}: {e}")
                return {"error": str(e)}