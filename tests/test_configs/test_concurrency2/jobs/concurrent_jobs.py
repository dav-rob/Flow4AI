import asyncio
from typing import Any, Dict, Optional

import jobchain.jc_logging as logging
from jobchain.job import JobABC


class ConcurrencyTestJob(JobABC):
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
        self.test_inputs: list = properties.get("test_inputs", [])
        self.valid_return: str = properties.get("valid_return", "")


    async def run(self, inputs):
        received_data = []
        for job_name in self.test_inputs:
            data = self.get_input_from(inputs,job_name)
            if not data:
                logging.error(f"Failed to get input from {job_name}")
                raise Exception(f"Job {self.name} failed to get input from {job_name}")
            received_data.append(data)
        received_data.append(f"{cls.name}")
        return_data = ".".join(received_data)
        if valid_return and return_data != valid_return:
            logging.error(f"Invalid return data: {return_data}")
            raise Exception(f"Job {self.name} returned invalid data: {return_data}, should have been {valid_return}")

        return return_data


