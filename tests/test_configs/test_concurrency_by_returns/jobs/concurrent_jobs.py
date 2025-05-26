import asyncio
from typing import Any, Dict, Optional

from flow4ai import f4a_logging as logging
from flow4ai.job import JobABC


class ConcurrencyTestJob(JobABC):
    def __init__(self, name: Optional[str] = None, properties: Dict[str, Any] = {}):
        super().__init__(name, properties)
        self.test_inputs: list = properties.get("test_inputs", [])
        self.valid_return: str = properties.get("valid_return", "")

    def get_random_sleep_duration(self) -> float:
        """Generate a random sleep duration between 0 and 1 second.
        
        The duration will be randomly selected from one of 10 equal deciles (0.0-0.1, 0.1-0.2, ..., 0.9-1.0)
        with equal probability for each decile.
        
        Returns:
            float: Sleep duration in seconds
        """
        import random
        decile = random.randint(0, 5)  # Choose a decile (0-5)
        base = decile * 0.1  # Base value for the chosen decile
        offset = random.random() * 0.1  # Random offset within the decile
        return base + offset

    async def run(self, task):
        await asyncio.sleep(self.get_random_sleep_duration())
        received_data = []
        if not self.is_head_job(): 
            for short_job_name in self.test_inputs: # self.test_input is guaranteed to be in the order it is loaded in
                inputs = self.get_inputs()
                data = inputs.get(short_job_name)
                if not data:
                    logging.error(f"Failed to get input from {short_job_name}")
                    raise Exception(f"Job {self.name} failed to get input from {short_job_name}")
                received_data.append(data['result']) # return from run() from parent job is a str it is converted to dict.
        #task = self.get_task(task)
        await asyncio.sleep(self.get_random_sleep_duration())
        short_job_name = self.parse_job_name(self.name)
        received_data.append(f"{short_job_name}")
        return_data = ".".join(received_data)
        await asyncio.sleep(self.get_random_sleep_duration())
        if self.valid_return and return_data != self.valid_return:
            logging.error(f"Invalid return data: {return_data}")
            raise Exception(f"Job {self.name} returned invalid data: {return_data}, should have been {self.valid_return}")

        logging.info(f"Job {self.name} returned: {return_data} for task {task['task']}")
        return return_data
