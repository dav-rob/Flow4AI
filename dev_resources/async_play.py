import asyncio
from typing import Dict, List

from jobchain.utils import timing_decorator


async def api_call(i: int) -> Dict:
    print(f"Starting {i}")
    await asyncio.sleep(1)
    print(f"Finished {i}")
    return {"id": i}


# Using create_task() for concurrency
async def run_tasks():
    # Create multiple tasks to run concurrently
    tasks: List[asyncio.Task] = [
        asyncio.create_task(api_call(i)) for i in range(3)
    ]
    
    # await each task
    results = await asyncio.gather(*tasks)
    return results


# Using asyncio.run() as entry point
@timing_decorator
def main():
    asyncio.run(run_tasks())


if __name__ == '__main__':
    main()
