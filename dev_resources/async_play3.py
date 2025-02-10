import os

import aiofiles
import aiohttp
import openai
from dotenv import load_dotenv
from pydantic import BaseModel

from jobchain.taskmanager import TaskManager


# 1. Pydantic model for OpenAI response
class ChurchInfo(BaseModel):
    name: str
    construction_year: int
    architectural_style: str
    architect: str

# 1. Async OpenAI call with response format
async def get_church_info():
    prompt = "Tell me about Santa Maria delle Grazie in Milan"

    load_dotenv("api.env")
    api_key = os.getenv("OPENAI_API_KEY")
    
    client = openai.AsyncClient(api_key=api_key)  # Requires OPENAI_API_KEY in environment
    response = await client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        response_format=ChurchInfo,
    )
    
    content = response.choices[0].message.parsed
    return content

# 2. Async Wikipedia downloader
async def download_wikipedia_page():
    url = "https://en.wikipedia.org/wiki/Santa_Maria_delle_Grazie,_Milan"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            content = await response.text()
            
    async with aiofiles.open("santa_maria.html", "w", encoding="utf-8") as f:
        await f.write(content)
    
    return "Download completed"

# 3. Mock database task that raises an error
async def failing_db_query():
    # Simulate database connection error
    raise ConnectionError("Database connection timed out")

if __name__ == "__main__":
    manager = TaskManager()
    
    # Submit all tasks
    manager.submit(get_church_info)
    manager.submit(download_wikipedia_page)
    manager.submit(failing_db_query)
    
    # Give tasks time to execute (in real usage you'd use proper synchronization)
    import time
    time.sleep(5)
    
    # Print results
    print("Task counts:", manager.get_counts())
    results = manager.pop_results()
    
    print("\nCompleted tasks:")
    for result in results["completed"]:
        print(f"- {result[1]['func'].__name__}: {result[0]}")
    
    print("\nErrors:")
    for error in results["errors"]:
        print(f"- {error[1]['func'].__name__}: {error[0]}")
