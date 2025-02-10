import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Union


@dataclass
class TaskInfo:
    name: str
    coroutine: Callable
    parameters: dict

class TaskTimeoutError(Exception):
    def __init__(self, task_name: str, parameters: dict, timeout: float):
        self.task_name = task_name
        self.parameters = parameters
        self.timeout = timeout
        self.timestamp = datetime.now()
        super().__init__(f"Task '{task_name}' timed out after {timeout} seconds. Parameters: {parameters}")

    def to_dict(self) -> Dict:
        return {
            "error_type": "timeout",
            "task_name": self.task_name,
            "parameters": self.parameters,
            "timeout": self.timeout,
            "timestamp": self.timestamp.isoformat(),
            "message": str(self)
        }

async def execute_with_timeout(task_info: TaskInfo, timeout: float) -> Any:
    try:
        result = await asyncio.wait_for(task_info.coroutine(**task_info.parameters),timeout=timeout)
        
        return {
            "status": "success",
            "task_name": task_info.name,
            "result": result,
            "parameters": task_info.parameters
        }
    except asyncio.TimeoutError:
        raise TaskTimeoutError(
            task_name=task_info.name,
            parameters=task_info.parameters,
            timeout=timeout
        )

async def collect_results(tasks: List[TaskInfo], timeout: float = 30.0) -> List[Dict[str, Any]]:
    results = []
    
    task_objects = [
        asyncio.create_task(execute_with_timeout(task_info, timeout),name=task_info.name)
        for task_info in tasks
    ]
    
    try:
        completed, pending = await asyncio.wait(task_objects,return_when=asyncio.ALL_COMPLETED)
        
        for task in completed:
            try:
                result = task.result()
                results.append(result)
            except TaskTimeoutError as e:
                results.append(e.to_dict())
            except Exception as e:
                results.append({
                    "error_type": "execution_error",
                    "task_name": task.get_name(),
                    "error_message": str(e),
                    "timestamp": datetime.now().isoformat()
                })
    
    finally:
        for task in task_objects:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    return results

# Example usage with both successful and timeout cases
async def fast_task(value: str) -> str:
    await asyncio.sleep(1)
    return f"Quick result: {value}"

async def slow_task(value: str) -> str:
    await asyncio.sleep(5)  # This will timeout
    return f"Slow result: {value}"

async def main():
    tasks = [
        TaskInfo(name="fast_task_1",coroutine=fast_task,parameters={"value": "fast one"}),
        TaskInfo(name="slow_task_1",coroutine=slow_task,parameters={"value": "slow one"}),
        TaskInfo(name="fast_task_2",coroutine=fast_task,parameters={"value": "fast two"})
    ]
    
    # Set timeout to 3 seconds to ensure slow_task times out
    results = await collect_results(tasks, timeout=3.0)

    #print(results)
    pretty_json = json.dumps(results, indent=4)
    print(pretty_json)
    
    # print("\nDetailed Results:")
    # print("----------------")
    # for result in results:
    #     if result.get("status") == "success":
    #         print(f"Success - Task: {result['task_name']}")
    #         print(f"Result: {result['result']}")
    #         print(f"Parameters: {result['parameters']}")
    #     else:
    #         print(f"Error - Task: {result['task_name']}")
    #         print(f"Error Type: {result['error_type']}")
    #         print(f"Message: {result.get('message', result.get('error_message'))}")
    #     print("----------------")

    return results

if __name__ == "__main__":
    results = asyncio.run(main())
    
    print("\nFinal Results Summary:")
    print("=====================")
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    print(f"Total tasks: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
