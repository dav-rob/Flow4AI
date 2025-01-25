(.venv) davidroberts [JobChain] (main)$ python -m pytest tests/test_concurrency.py::test_concurrency_by_expected_returns -s
Logging level: INFO
===================================================== test session starts ======================================================
platform darwin -- Python 3.11.11, pytest-8.3.4, pluggy-1.5.0
rootdir: /Users/davidroberts/projects/JobChain
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.1
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=function
collected 1 item                                                                                                               

tests/test_concurrency.py 2025-01-25 06:13:54 [INFO] JobChain:47 - Initializing JobChain
2025-01-25 06:13:54 [INFO] JobChain:180 - Job executor process started with PID 35856
2025-01-25 06:13:54 [INFO] JobChain:190 - Result processor process started with PID 35857
Logging level: INFO
Logging level: INFO
2025-01-25 06:13:54 [INFO] AsyncWorker:358 - Creating job map from JobLoader
2025-01-25 06:13:54 [INFO] AsyncWorker:359 - Using directories from process: ['/Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns']
2025-01-25 06:13:54 [INFO] jobchain.job_loader:66 - Added /Users/davidroberts/projects/JobChain/src/jobchain/jobs to Python path
2025-01-25 06:13:54 [INFO] jobchain.job_loader:74 - Loading jobs from /Users/davidroberts/projects/JobChain/src/jobchain/jobs/llm_jobs.py
2025-01-25 06:13:55 [INFO] jobchain.job_loader:91 - Found valid job class: OpenAIJob
Registered custom job: OpenAIJob
2025-01-25 06:13:55 [INFO] jobchain.job_loader:66 - Added /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns/jobs to Python path
2025-01-25 06:13:55 [INFO] jobchain.job_loader:74 - Loading jobs from /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns/jobs/concurrent_jobs.py
2025-01-25 06:13:55 [INFO] jobchain.job_loader:91 - Found valid job class: ConcurrencyTestJob
Registered custom job: ConcurrencyTestJob
2025-01-25 06:13:55 [INFO] jobchain.job_loader:531 - Reloading configs...
2025-01-25 06:13:55 [INFO] jobchain.job_loader:275 - Looking for config files in directories: [PosixPath('/Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns')]
2025-01-25 06:13:55 [INFO] jobchain.job_loader:295 - Found valid jobchain directory: /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns

Checking test_graph for cycles...
No cycles detected
Graph test_graph passed all validations
2025-01-25 06:13:55 [INFO] AsyncWorker:368 - Created job map with head jobs: ['test_graph$$$$A$$']
2025-01-25 06:13:55 [INFO] root:36 - Names of jobs in head job: {'test_graph$$$$A$$': {'test_graph$$$$G$$', 'test_graph$$$$B$$', 'test_graph$$$$D$$', 'test_graph$$$$C$$', 'test_graph$$$$A$$', 'test_graph$$$$E$$', 'test_graph$$$$F$$'}}
2025-01-25 06:13:55 [INFO] JobChain:259 - *** task_queue ended ***
2025-01-25 06:13:55 [INFO] AsyncWorker:413 - Received end signal in task queue
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 25
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 4
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 29
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 8
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 19
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 0
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 22
2025-01-25 06:13:55 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 24
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 2
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 20
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 11
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 5
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 27
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 26
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 28
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 12
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 7
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 14
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 4
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 23
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 21
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 6
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 16
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 10
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 24
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 13
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 19
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 17
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 8
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 25
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 5
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 25
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 26
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 4
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 15
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 7
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 1
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 0
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 26
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 20
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 3
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 22
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 9
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 18
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 27
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 11
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 13
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 11
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 29
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 23
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 8
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 20
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 2
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 16
2025-01-25 06:13:56 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 2
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 24
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 6
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 5
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 16
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 4
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 14
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 0
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 27
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 14
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 7
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 25
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 25
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 25
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 23
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 29
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 18
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 12
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 12
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 13
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 21
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 28
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 21
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 3
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 27
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 24
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 25
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 2
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 2
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 3
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 2
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 22
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 10
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 4
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$E$$ has no executing child jobs, returning result at the end: A.A.B.C.E for task 4
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E for task 4
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E for task 4
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 7
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 0
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 17
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 19
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 19
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 19
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 16
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 16
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 16
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 22
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 22
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 22
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 19
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 20
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 28
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 8
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 8
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 8
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 20
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 20
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 20
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 5
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 5
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 5
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 26
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 26
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 26
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 10
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 9
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 4
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 5
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 18
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 6
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 11
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 11
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 11
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 26
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 17
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 7
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 7
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 7
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 21
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 21
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 21
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 9
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 13
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 13
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 13
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 15
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 0
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$E$$ has no executing child jobs, returning result at the end: A.A.B.C.E for task 0
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E for task 0
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E for task 0
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 18
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 15
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 24
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 24
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 24
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 23
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 23
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 23
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 14
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 14
2025-01-25 06:13:57 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 14
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 10
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 1
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 11
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 3
2025-01-25 06:13:57 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 0
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 13
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 23
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 29
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 1
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 27
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 27
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 27
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 7
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 8
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 3
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$E$$ has no executing child jobs, returning result at the end: A.A.B.C.E for task 3
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E for task 3
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 14
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E for task 3
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 19
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 22
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 2
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 6
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 27
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 6
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 6
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 6
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 12
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 12
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 12
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 12
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 21
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 29
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 29
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 29
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 3
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 17
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 10
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 10
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 10
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 15
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 24
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 16
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 28
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 28
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 28
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 28
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 25
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 18
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 18
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 18
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 1
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 20
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 29
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 15
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 15
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 15
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 9
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 1
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 1
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 1
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 8
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 15
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 5
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 11
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 9
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 9
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 9
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 0
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 0
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$F$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 0
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 0
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E for task 0
2025-01-25 06:13:58 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E for task 0
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 21
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 14
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 06:13:58 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 27
Logging level: INFO
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 26
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 13
2025-01-25 06:13:58 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 06:13:58 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 06:13:58 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 7
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 18
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 22
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 12
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 25
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 4
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 4
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$F$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 4
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 4
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E for task 4
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E for task 4
2025-01-25 06:13:59 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 5, Active: 25
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 10
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 28
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 24
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 17
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:337 - Job test_graph$$$$F$$ has no executing child jobs, returning result at the end: A.D.F for task 17
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.D.F for task 17
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 2
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 13
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 18
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 17
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 6
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 19
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 16
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 23
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 20
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 29
2025-01-25 06:13:59 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 10, Active: 20
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 10
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 12
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 3
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 3
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 28
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$F$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 3
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$D$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 3
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E for task 3
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E for task 3
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 15
2025-01-25 06:13:59 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 15, Active: 15
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 8
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 5
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 26
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 14
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 9
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 11
2025-01-25 06:13:59 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 20, Active: 10
2025-01-25 06:13:59 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 06:13:59 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 06:13:59 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 22
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 06:14:00 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 6
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 1
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 06:14:00 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 21
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 06:14:00 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 17
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 06:14:00 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 16
2025-01-25 06:14:00 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 25, Active: 5
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 06:14:00 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 19
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 06:14:00 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 23
2025-01-25 06:14:00 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 06:14:00 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 06:14:00 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 2
2025-01-25 06:14:01 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 06:14:01 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 9
2025-01-25 06:14:01 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:317 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$E$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$C$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$B$$ has 1 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 06:14:01 [INFO] ConcurrencyTestJob:334 - Job test_graph$$$$A$$ has 2 child jobs, one is returning executed result: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 06:14:01 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G for task 1
2025-01-25 06:14:01 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 30, Active: 0
2025-01-25 06:14:01 [INFO] AsyncWorker:463 - *** result_queue ended ***
2025-01-25 06:14:01 [INFO] AsyncWorker:478 - Closing event loop
2025-01-25 06:14:01 [INFO] JobChain:121 - Cleaning up JobChain resources
F

=========================================================== FAILURES ===========================================================
_____________________________________________ test_concurrency_by_expected_returns _____________________________________________

    @pytest.mark.asyncio
    async def test_concurrency_by_expected_returns():
        # Create a manager for sharing the results list between processes
        manager = mp.Manager()
        shared_results = manager.list()
    
        # Create a partial function with our shared results list
        collector = partial(returns_collector, shared_results)
    
        # Set config directory for test
        config_dir = os.path.join(os.path.dirname(__file__), "test_configs/test_concurrency_by_returns")
        ConfigLoader._set_directories([config_dir])
    
        # Create JobChain with parallel processing
        job_chain = JobChain(result_processing_function=collector)
        logging.info(f"Names of jobs in head job: {job_chain.get_job_graph_mapping()}")
    
        def submit_task(range_val:int):
            for i in range(range_val):
                job_chain.submit_task({'task': f'{i}'})
    
        def check_results():
            for result in shared_results:
                #logging.info(f"Result: {result}")
                assert result['result'] == 'A.A.B.C.E.A.D.F.G'
    
            shared_results[:] = []  # Clear the shared_results using slice assignment
    
    
        submit_task(30)
    
        job_chain.mark_input_completed() # this waits for all results to be returned
    
>       check_results()

tests/test_concurrency.py:54: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

    def check_results():
        for result in shared_results:
            #logging.info(f"Result: {result}")
>           assert result['result'] == 'A.A.B.C.E.A.D.F.G'
E           AssertionError: assert 'A.A.B.C.E' == 'A.A.B.C.E.A.D.F.G'
E             
E             - A.A.B.C.E.A.D.F.G
E             + A.A.B.C.E

tests/test_concurrency.py:45: AssertionError
------------------------------------------------------ Captured log call -------------------------------------------------------
INFO     JobChain:job_chain.py:47 Initializing JobChain
INFO     JobChain:job_chain.py:180 Job executor process started with PID 35856
INFO     JobChain:job_chain.py:190 Result processor process started with PID 35857
INFO     root:test_concurrency.py:36 Names of jobs in head job: {'test_graph$$$$A$$': {'test_graph$$$$G$$', 'test_graph$$$$B$$', 'test_graph$$$$D$$', 'test_graph$$$$C$$', 'test_graph$$$$A$$', 'test_graph$$$$E$$', 'test_graph$$$$F$$'}}
INFO     JobChain:job_chain.py:259 *** task_queue ended ***
INFO     JobChain:job_chain.py:121 Cleaning up JobChain resources
=================================================== short test summary info ====================================================
FAILED tests/test_concurrency.py::test_concurrency_by_expected_returns - AssertionError: assert 'A.A.B.C.E' == 'A.A.B.C.E.A.D.F.G'
====================================================== 1 failed in 7.11s =======================================================
(.venv) davidroberts [JobChain] (main)$ 