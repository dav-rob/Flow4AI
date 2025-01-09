import os
from typing import Any, Dict, Optional, Union

from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
from openai import AsyncOpenAI

from jobchain import jc_logging as logging
from jobchain.job import JobABC


class OpenAIClient:
    """
    Singleton class for AsyncOpenAI client.
    """
    _client = None

    @classmethod
    def get_client(cls, params: Dict[str, Any] = None):
        if cls._client is None:
            # Load environment variables from api.env file
            load_dotenv("api.env")

            # Initialize params if None
            params = params or {}

            # Determine the API key
            api_key = os.getenv(params.get("api_key")) if params.get("api_key") else os.getenv('OPENAI_API_KEY')

            # Optional: Check if the API key is not set and raise an error 
            if not api_key:
                raise ValueError("API key is not set. Please provide an API key.")
            
            # Create client with all params
            cls._client = AsyncOpenAI(api_key=api_key, **params)
        return cls._client

class OpenAIJob(JobABC):

    # Shared AsyncLimiter for all jobs, default to 5,000 requests per minute
    default_rate_limit = {"max_rate": 5000, "time_period": 60}

    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        """
        Initialize an OpenAIJob instance, with properties dict, with three top-level keys, client, api, and rate_limit.
        Example properties:
        {
            client: {
                api_key: str | None = None,
                organization: str | None = None,
                project: str | None = None,
                base_url: str | URL | None = None,
                websocket_base_url: str | URL | None = None,
                timeout: float | Timeout | NotGiven | None = NOT_GIVEN,
                max_retries: int = DEFAULT_MAX_RETRIES,
                default_headers: Mapping[str, str] | None = None,
                default_query: Mapping[str, object] | None = None,
                http_client: AsyncClient | None = None,
                _strict_response_validation: bool = False
            },
            api: {
                messages: Iterable[ChatCompletionMessageParam],
                model: ChatModel | str,
                audio: ChatCompletionAudioParam | NotGiven | None = NOT_GIVEN,
                frequency_penalty: float | NotGiven | None = NOT_GIVEN,
                function_call: FunctionCall | NotGiven = NOT_GIVEN,
                functions: Iterable[Function] | NotGiven = NOT_GIVEN,
                logit_bias: Dict[str, int] | NotGiven | None = NOT_GIVEN,
                logprobs: bool | NotGiven | None = NOT_GIVEN,
                max_completion_tokens: int | NotGiven | None = NOT_GIVEN,
                max_tokens: int | NotGiven | None = NOT_GIVEN,
                metadata: Dict[str, str] | NotGiven | None = NOT_GIVEN,
                modalities: List[ChatCompletionModality] | NotGiven | None = NOT_GIVEN,
                n: int | NotGiven | None = NOT_GIVEN,
                parallel_tool_calls: bool | NotGiven = NOT_GIVEN,
                prediction: ChatCompletionPredictionContentParam | NotGiven | None = NOT_GIVEN,
                presence_penalty: float | NotGiven | None = NOT_GIVEN,
                reasoning_effort: ChatCompletionReasoningEffort | NotGiven = NOT_GIVEN,
                response_format: ResponseFormat | NotGiven = NOT_GIVEN,
                seed: int | NotGiven | None = NOT_GIVEN,
                service_tier: NotGiven | Literal['auto', 'default'] | None = NOT_GIVEN,
                stop: str | List[str] | NotGiven | None = NOT_GIVEN,
                store: bool | NotGiven | None = NOT_GIVEN,
                stream: NotGiven | Literal[False] | None = NOT_GIVEN,
                stream_options: ChatCompletionStreamOptionsParam | NotGiven | None = NOT_GIVEN,
                temperature: float | NotGiven | None = NOT_GIVEN,
                tool_choice: ChatCompletionToolChoiceOptionParam | NotGiven = NOT_GIVEN,
                tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
                top_logprobs: int | NotGiven | None = NOT_GIVEN,
                top_p: float | NotGiven | None = NOT_GIVEN,
                user: str | NotGiven = NOT_GIVEN,
                extra_headers: Headers | None = None,
                extra_query: Query | None = None,
                extra_body: Body | None = None,
                timeout: float | Timeout | NotGiven | None = NOT_GIVEN
            },
            rate_limit: {
                max_rate: Allow up to max_rate / time_period acquisitions before blocking.
                time_period: duration of the time period in which to limit the rate. Note that up to max_rate acquisitions are allowed within this time period in a burst
            }
        }
        """
        super().__init__(name, properties)
        
        # Initialize OpenAI client with properties
        self.client = OpenAIClient.get_client(self.properties.get("client", {}))
        
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