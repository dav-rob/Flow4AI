from typing import Any, Dict

from job import JobABC


class MockJob(JobABC):
    async def run(self, inputs: Dict[str, Any]) -> Any:
        print(f"\nMockJob '{self.name}' with properties: {self.properties}, inputs: {inputs}")
        return {self.name:f"Ran function '{self.name}' with {inputs}"}