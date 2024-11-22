import os
import sys
import unittest

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from job import JobABC, JobFactory


class TestJobLoader(unittest.TestCase):
    def test_load_from_file(self):
        params = {"file_path": "sample_job.json"}
        job = JobFactory._load_from_file(params)
        self.assertIsInstance(job, JobABC)
        self.assertEqual(job.name, "File Job")

    def test_load_from_datastore(self):
        params = {"job_id": "123"}
        job = JobFactory._load_from_datastore(params)
        self.assertIsInstance(job, JobABC)
        self.assertEqual(job.name, "Datastore Job")

    def test_factory_file(self):
        job_context = {"type": "file", "params": {"file_path": "sample_job.json"}}
        job = JobFactory.load_job(job_context)
        self.assertIsInstance(job, JobABC)
        self.assertEqual(job.name, "File Job")

    def test_factory_datastore(self):
        job_context = {"type": "datastore", "params": {"job_id": "123"}}
        job = JobFactory.load_job(job_context)
        self.assertIsInstance(job, JobABC)
        self.assertEqual(job.name, "Datastore Job")

    def test_factory_invalid_type(self):
        job_context = {"type": "invalid", "params": {}}
        with self.assertRaises(ValueError):
            JobFactory.load_job(job_context)

if __name__ == '__main__':
    unittest.main()
