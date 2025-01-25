import asyncio
import sys
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any, Dict, Optional, Type, Union

import jobchain.jc_logging as logging
from jobchain.job import Task, create_job_graph
from jobchain.utils import timing_decorator


class AsyncPlay:

    def __init__(self):
      self.name:str = "AsyncPlay"
      self.expected_inputs:set[str] = set()
      self.next_jobs:list[JobABC] = [] 
      self.timeout = 3000
      self.input_event = asyncio.Event()
      self.execution_started = False
      self.inputs:dict = {}

    async def receive_input(self, from_job: str, data: Dict[str, Any]) -> None:
        
        if self.expected_inputs.issubset(set(self.inputs.keys())):
            self.input_event.set()

    async def execute(self, task):
      
      result = await self.run(task)
      return result
  
    async def run(self, task: dict) -> Dict:
      await asyncio.sleep(1)
      print(f"Finished {task}")
      return {"task": task}

# Using create_task() for concurrency

async def run_tasks():
    results = [None, "a string",None]
    if any(results):
        end_result = results[0]
    return end_result

# Using asyncio.run() as entry point
@timing_decorator
def main():
    result = asyncio.run(run_tasks())
    print(result)

@timing_decorator
def test():
    asyncio.run(test_simple_graph())

if __name__ == '__main__':
  if len(sys.argv) > 1 and sys.argv[1] == 'main':
    main()
#   elif len(sys.argv) > 1 and sys.argv[1] == 'test':
#     test()
  else:
    print("Usage: python async_play.py [main]")
