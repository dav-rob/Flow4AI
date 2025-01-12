import asyncio
from collections import defaultdict
from dataclasses import dataclass, field

import jobchain.jc_logging as logging
from jobchain.job import JobABC


@dataclass
class JobStats:
    """Track statistics for a job"""
    processed_count: int = 0
    concurrent_executions: int = 0
    max_concurrent: int = 0
    processed_tasks: set = field(default_factory=set)
    processing_times: defaultdict = field(default_factory=lambda: defaultdict(list))

class StateTrackingJob(JobABC):
    """Base job class that tracks state for testing"""
    def __init__(self, name, params=None):
        super().__init__(name)
        self.stats = JobStats()
        self._lock = asyncio.Lock()
        
    async def _track_execution(self, task_id):
        async with self._lock:
            self.stats.concurrent_executions += 1
            self.stats.max_concurrent = max(self.stats.max_concurrent, 
                                          self.stats.concurrent_executions)
            if task_id in self.stats.processed_tasks:
                logging.error(f"Race condition in {self.name}! Task {task_id} processed multiple times")
            self.stats.processed_tasks.add(task_id)
            self.stats.processed_count += 1
            current_concurrent = self.stats.concurrent_executions
            
        try:
            start_time = asyncio.get_event_loop().time()
            yield current_concurrent
            duration = asyncio.get_event_loop().time() - start_time
            self.stats.processing_times[task_id].append(duration)
        finally:
            async with self._lock:
                self.stats.concurrent_executions -= 1

class HeadJob(StateTrackingJob):
    """Head job that passes through input data"""
    async def run(self, inputs):
        task_id = inputs.get('task_id', 'unknown')
        logging.debug(f"HeadJob {self.name} processing task {task_id}")
        
        async for current_concurrent in self._track_execution(task_id):
            await asyncio.sleep(0.001)  # Small delay to increase chance of race conditions
            return {
                'task_id': task_id,
                'source_job': self.name,
                'data': inputs.get('data'),
                'concurrent_count': current_concurrent
            }


class MiddleJob(StateTrackingJob):
    """Middle job that processes inputs"""
    async def run(self, inputs):
        # Get task_id from first input
        first_input = next(iter(inputs.values()))
        task_id = first_input.get('task_id', 'unknown')
        logging.debug(f"MiddleJob {self.name} processing task {task_id}")
        
        async for current_concurrent in self._track_execution(task_id):
            await asyncio.sleep(0.01)  # Longer delay in middle to increase race condition chance
            return {
                'task_id': task_id,
                'source_job': self.name,
                'inputs_processed': list(inputs.keys()),
                'concurrent_count': current_concurrent
            }


class TailJob(StateTrackingJob):
    """Tail job that collects results"""
    async def run(self, inputs):
        first_input = next(iter(inputs.values()))
        task_id = first_input.get('task_id', 'unknown')
        logging.debug(f"TailJob {self.name} processing task {task_id}")
        
        async for current_concurrent in self._track_execution(task_id):
            await asyncio.sleep(0.001)  # Small delay
            return {
                'task_id': task_id,
                'source_job': self.name,
                'final_result': first_input,
                'concurrent_count': current_concurrent
            }
