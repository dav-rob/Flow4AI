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
        if self.expected_inputs: # if this is not a head job
            for short_job_name in self.test_inputs: # self.test_input is guaranteed to be in the order it is loaded in
                data = self.get_input_from(inputs,short_job_name)
                if not data:
                    logging.error(f"Failed to get input from {short_job_name}")
                    raise Exception(f"Job {self.name} failed to get input from {short_job_name}")
                received_data.append(data['result']) # return from run() from parent job is a str it is converted to dict.
        
        short_job_name = self.parse_job_name(self.name)
        received_data.append(f"{short_job_name}")
        return_data = ".".join(received_data)
        if self.valid_return and return_data != self.valid_return:
            logging.error(f"Invalid return data: {return_data}")
            raise Exception(f"Job {self.name} returned invalid data: {return_data}, should have been {self.valid_return}")

        return return_data


