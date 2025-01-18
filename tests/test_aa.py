from jobchain.job import JobABC, SimpleJob
from jobchain.job_chain import JobChain


class AsyncTestJob(JobABC):
    """Job to confirm the basics of async functionality are working: """
    def __init__(self):
        super().__init__(name="AsyncTestJob")
    
    async def run(self, inputs):
        task = inputs[self.name]  # Get the task from inputs dict
        if isinstance(task, dict) and task.get('fail'):
            raise ValueError("Simulated task failure")
        if isinstance(task, dict) and task.get('delay'):
            await asyncio.sleep(task['delay'])
        return {'task': task, 'completed': True}

def test_imports_are_working():
  job = SimpleJob("Test Job")
  job_chain = JobChain(job)
  testvar="test"
  assert testvar == "test"
