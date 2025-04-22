import os
from typing import Any, Dict, Optional, Union

from aiolimiter import AsyncLimiter
from openai import AsyncOpenAI

from flow4ai.f4a_logging import logging
from flow4ai.job import JobABC
from flow4ai.job_loader import JobFactory
from flow4ai.utils.api_utils import get_api_key
from flow4ai.utils.llm_utils import clean_prompt

logger = logging.getLogger("OpenAIJob")

class OpenAIClient:
    """
    Singleton class for AsyncOpenAI client.
    """
    _client = None

    @classmethod
    def get_client(cls, params: Dict[str, Any] = None):
        if cls._client is None:
            # Initialize params if None
            params = params or {}
            
            # Get API key using our utility function
            api_key = get_api_key(params, key_name='OPENAI_API_KEY')
            
            # Create client with remaining params
            cls._client = AsyncOpenAI(api_key=api_key, **params)
            logger.info(f"Created client with base_url: {params.get('base_url', 'default')}")
        return cls._client

class OpenAIJob(JobABC):

    # Shared AsyncLimiter for all jobs, default to 5,000 requests per minute
    default_rate_limit = {"max_rate": 5000, "time_period": 60}

    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        """
        Initialize an OpenAIJob instance with a properties dict containing three top-level keys, client, api, and rate_limit.
        All properties are optional.

        Args:
            name (Optional[str], optional): 
                A unique identifier for this job.
                The name must be unique among all jobs to ensure proper job identification 
                and dependency resolution. If not provided, a unique name will be auto-generated.

            properties (Dict[str, Any], optional): Optional properties for the job. A dictionary containing the following keys:

            {
                rate_limit: {
                    max_rate: Allow up to max_rate / time_period acquisitions before blocking.
                    time_period: duration of the time period in which to limit the rate. Note that up to max_rate acquisitions are allowed within this time period in a burst
                },
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
                    response_format: ResponseFormat | NotGiven | None = NOT_GIVEN,
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
        
        Args:
            task: A dictionary containing either:
                - prompt: str - The prompt to send to the model
                - messages: list - Direct message format for the API
                Or any other valid parameters for the chat.completions.create API
        """
        # Start with default properties
        request_properties = {
            "model": "gpt-4o",
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "You are a helpful assistant."}
            ]
        }
        
        # Add API properties from initialization
        request_properties.update(self.api_properties)

        # Check if response_format is a string and replace with the Pydantic class
        if "response_format" in request_properties and isinstance(request_properties["response_format"], str):
            try:
                response_format_name = request_properties["response_format"]
                request_properties["response_format"] = JobFactory.get_pydantic_class(response_format_name)
                logger.info(f"Successfully replaced response_format string with Pydantic class: {response_format_name}")
            except ValueError as e:
                logger.error(f"Could not find Pydantic class for response_format: {request_properties['response_format']}. Error: {e}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while trying to get the Pydantic class: {e}")

        self.create_prompt(request_properties, task)

        # Acquire the rate limiter before making the request
        async with self.limiter:
            try:
                logger.info(f"{self.name} is making an OpenAI API call.")
                if "response_format" in request_properties:
                    response = await self.client.beta.chat.completions.parse(**request_properties)
                else:
                    response = await self.client.chat.completions.create(**request_properties)
                logger.info(f"{self.name} received a response.")
                
                # Handle the response
                if hasattr(response, 'choices') and response.choices:
                    if "response_format" in request_properties:
                        return response.choices[0].message.parsed
                    else:
                        return {"response": response.choices[0].message.content}
                else:
                    return {"error": "No valid response content found"}
            except Exception as e:
                logger.error(f"Error in {self.name}: {e}")
                return {"error": str(e)}

    def create_prompt(self, request_properties, task):
        # Handle the task input
        if isinstance(task, dict):
            # If task has a prompt, convert it to messages format
            if "prompt" in task:
                prompt = clean_prompt(task["prompt"])
                request_properties["messages"] = [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": prompt}
                ]
            # If task already has messages, use those
            elif "messages" in task:
                request_properties["messages"] = task["messages"]

            # Add any other valid API parameters from task
            # request_properties.update({k: v for k, v in task.items() if k not in ["prompt", "messages"]})
        elif task:  # If task is not empty and not a dict
            # If task is not a dict, treat it as the prompt
            prompt = clean_prompt(str(task))
            request_properties["messages"] = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": prompt}
            ]