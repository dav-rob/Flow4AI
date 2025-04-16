from typing import Any, Dict

from flow4ai.job import JobABC


class MockJob(JobABC):
    async def run(self, task: Dict[str, Any]) -> Any:
        inputs = self.get_inputs()
        print(f"\nMockJob '{self.name}' with properties: {self.properties}, inputs: {inputs}")
        return {self.name:f"Ran function '{self.name}' with {inputs}"}