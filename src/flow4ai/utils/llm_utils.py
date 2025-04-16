import re
import string

from flow4ai import jc_logging as logging

logger = logging.getLogger(__name__)

def clean_prompt(text):
    # Keep only printable characters
    return ''.join(char for char in text if char in string.printable)


def clean_prompt(text):
    if not isinstance(text, str):
        logger.error("Input must be a string")
        raise ValueError("Input must be a string")
    
    # Remove control characters but keep normal whitespace
    cleaned_1 = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    cleaned = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', cleaned_1)
    # Optional: Check if the text was modified
    if cleaned != text:
        logger.info("Characters were cleaned from the prompt")
    
    # Optional: Ensure the text isn't empty after cleaning
    if not cleaned.strip():
        logger.error("Prompt is empty after cleaning")
        raise ValueError("Prompt is empty after cleaning")
    
    return cleaned

def check_response_errors(response:dict):
    if response.get("error"):
        logger.error(f"Response has an error: {response}")
        raise ValueError("Response has an error")
    elif response.get("status"):
        status = response.get("status")
        if status == "error":
            logger.error(f"Response has an error: {response}")
            raise ValueError("Response has an error")
