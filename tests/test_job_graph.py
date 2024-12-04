import unittest
from job import JobABC

class MockJob(JobABC):
    def run(self):
        pass

class MockJobSubclass(MockJob):
    pass

class TestJobGraph(unittest.TestCase):
    def test_job_name_always_present(self):
        # Test with explicit name
        job1 = MockJob(name="explicit_name")
        self.assertEqual(job1.name, "explicit_name")
        
        # Test with auto-generated name
        job2 = MockJob()
        self.assertIsNotNone(job2.name)
        self.assertIsInstance(job2.name, str)
        self.assertGreater(len(job2.name), 0)
        
        # Test subclass with explicit name
        job3 = MockJobSubclass(name="subclass_name")
        self.assertEqual(job3.name, "subclass_name")
        
        # Test subclass with auto-generated name
        job4 = MockJobSubclass()
        self.assertIsNotNone(job4.name)
        self.assertIsInstance(job4.name, str)
        self.assertGreater(len(job4.name), 0)

    def test_auto_generated_names_are_unique(self):
        # Create multiple jobs without explicit names
        num_jobs = 100  # Test with a significant number of jobs
        jobs = [MockJob() for _ in range(num_jobs)]
        
        # Collect all names in a set
        names = {job.name for job in jobs}
        
        # If all names are unique, the set should have the same length as the list
        self.assertEqual(len(names), num_jobs)
        
        # Test uniqueness across different subclass instances
        mixed_jobs = [
            MockJob() if i % 2 == 0 else MockJobSubclass()
            for i in range(num_jobs)
        ]
        mixed_names = {job.name for job in mixed_jobs}
        self.assertEqual(len(mixed_names), num_jobs)

if __name__ == '__main__':
    unittest.main()
