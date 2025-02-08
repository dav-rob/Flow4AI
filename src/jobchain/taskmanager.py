import asyncio
import threading
from collections import deque

import jobchain.jc_logging as logging


class TaskManager:
    _instance = None
    _lock = threading.Lock()  # Class-level lock for singleton creation

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.__initialized = False
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_TaskManager__initialized') or not self.__initialized:
            with self._lock:
                if not hasattr(self, '_TaskManager__initialized') or not self.__initialized:
                    self._initialize()
                    self.__initialized = True

    def _initialize(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

        self.submitted_count = 0
        self.completed_count = 0
        self.error_count = 0
        self.completed_results = deque()
        self.error_results = deque()

        self._data_lock = threading.Lock()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, func, *args, **kwargs):
        with self._data_lock:
            self.submitted_count += 1

        try:
            coro = func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error processing result: {e}")
            self.logger.info("Detailed stack trace:", exc_info=True)
            with self._data_lock:
                self.error_count += 1
                self.error_results.append(
                    (e, {'func': func, 'args': args, 'kwargs': kwargs})
                )
            return

        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        future.add_done_callback(
            lambda f: self._handle_completion(f, func, args, kwargs)
        )

    def _handle_completion(self, future, func, args, kwargs):
        try:
            result = future.result()
            with self._data_lock:
                self.completed_count += 1
                self.completed_results.append(
                    (result, {'func': func, 'args': args, 'kwargs': kwargs})
                )
        except Exception as e:
            self.logger.error(f"Error processing result: {e}")
            self.logger.info("Detailed stack trace:", exc_info=True)
            with self._data_lock:
                self.error_count += 1
                self.error_results.append(
                    (e, {'func': func, 'args': args, 'kwargs': kwargs})
                )

    def get_counts(self):
        with self._data_lock:
            return {
                'submitted': self.submitted_count,
                'completed': self.completed_count,
                'errors': self.error_count
            }

    def pop_results(self):
        with self._data_lock:
            completed = list(self.completed_results)
            errors = list(self.error_results)
            self.completed_results.clear()
            self.error_results.clear()
            return {
                'completed': completed,
                'errors': errors
            }

