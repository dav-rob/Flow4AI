from flow4ai.flowmanagerMP import FlowManagerMP
from flow4ai.job import JobABC
from tests.test_utils.simple_job import SimpleJob


class AsyncTestJob(JobABC):
    """Job to confirm the basics of async functionality are working: """
    def __init__(self):
        super().__init__(name="AsyncTestJob")
    
    async def run(self, task):
        if isinstance(task, dict) and task.get('fail'):
            raise ValueError("Simulated task failure")
        if isinstance(task, dict) and task.get('delay'):
            await asyncio.sleep(task['delay'])
        return {'task': task, 'completed': True}

def test_imports_are_working():
  job = SimpleJob("Test Job")
  flowmanagerMP = FlowManagerMP(job)
  testvar="test"
  assert testvar == "test"
