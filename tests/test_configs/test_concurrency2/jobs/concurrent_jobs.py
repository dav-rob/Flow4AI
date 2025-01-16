import asyncio
from typing import Any, Dict, Optional

import jobchain.jc_logging as logging
from jobchain.job import JobABC


class ConcurrencyTestJob(JobABC):
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
        self.test_inputs: list = properties.get("test_inputs", [])


    async def run(self, inputs):
        received_data = []
        for test_input in self.test_inputs:
            data = get_input_from(test_input)
            if not data:
                logging.error(f"Failed to get input from {test_input}")
                raise Exception(f"Job {self.name} failed to get input from {test_input}")
            received_data.append(data)
        received_data.append(f"{cls.name}")
        return_data = ".".join(received_data)
        return return_data


