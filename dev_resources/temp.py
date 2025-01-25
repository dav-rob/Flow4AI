(.venv) davidroberts [JobChain] (main)$ python -m pytest tests/test_concurrency.py::test_concurrency_by_expected_returns -s
Logging level: INFO
================================================ test session starts =================================================
platform darwin -- Python 3.11.11, pytest-8.3.4, pluggy-1.5.0
rootdir: /Users/davidroberts/projects/JobChain
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.1
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=function
collected 1 item                                                                                                     

tests/test_concurrency.py 2025-01-25 07:47:30,674 [INFO] JobChain:47 - Initializing JobChain
2025-01-25 07:47:30,797 [INFO] JobChain:180 - Job executor process started with PID 48405
2025-01-25 07:47:30,801 [INFO] JobChain:190 - Result processor process started with PID 48406
Logging level: INFO
Logging level: INFO
2025-01-25 07:47:31,116 [INFO] AsyncWorker:358 - Creating job map from JobLoader
2025-01-25 07:47:31,116 [INFO] AsyncWorker:359 - Using directories from process: ['/Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns']
2025-01-25 07:47:31,116 [INFO] jobchain.job_loader:66 - Added /Users/davidroberts/projects/JobChain/src/jobchain/jobs to Python path
2025-01-25 07:47:31,116 [INFO] jobchain.job_loader:74 - Loading jobs from /Users/davidroberts/projects/JobChain/src/jobchain/jobs/llm_jobs.py
2025-01-25 07:47:31,890 [INFO] jobchain.job_loader:91 - Found valid job class: OpenAIJob
Registered custom job: OpenAIJob
2025-01-25 07:47:31,890 [INFO] jobchain.job_loader:66 - Added /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns/jobs to Python path
2025-01-25 07:47:31,890 [INFO] jobchain.job_loader:74 - Loading jobs from /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns/jobs/concurrent_jobs.py
2025-01-25 07:47:31,891 [INFO] jobchain.job_loader:91 - Found valid job class: ConcurrencyTestJob
Registered custom job: ConcurrencyTestJob
2025-01-25 07:47:31,891 [INFO] jobchain.job_loader:531 - Reloading configs...
2025-01-25 07:47:31,891 [INFO] jobchain.job_loader:275 - Looking for config files in directories: [PosixPath('/Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns')]
2025-01-25 07:47:31,891 [INFO] jobchain.job_loader:295 - Found valid jobchain directory: /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns

Checking test_graph for cycles...
No cycles detected
Graph test_graph passed all validations
2025-01-25 07:47:31,898 [INFO] AsyncWorker:368 - Created job map with head jobs: ['test_graph$$$$A$$']
2025-01-25 07:47:31,916 [INFO] root:36 - Names of jobs in head job: {'test_graph$$$$A$$': {'test_graph$$$$A$$', 'test_graph$$$$B$$', 'test_graph$$$$C$$', 'test_graph$$$$G$$', 'test_graph$$$$D$$', 'test_graph$$$$E$$', 'test_graph$$$$F$$'}}
2025-01-25 07:47:31,926 [INFO] JobChain:259 - *** task_queue ended ***
2025-01-25 07:47:31,931 [INFO] AsyncWorker:413 - Received end signal in task queue
2025-01-25 07:47:32,050 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 4
2025-01-25 07:47:32,332 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 1
2025-01-25 07:47:32,398 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 18
2025-01-25 07:47:32,402 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 24
2025-01-25 07:47:32,442 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 17
2025-01-25 07:47:32,485 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 2
2025-01-25 07:47:32,570 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 0
2025-01-25 07:47:32,691 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 21
2025-01-25 07:47:32,733 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 13
2025-01-25 07:47:32,744 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 19
2025-01-25 07:47:32,747 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 6
2025-01-25 07:47:32,751 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 22
2025-01-25 07:47:32,784 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 14
2025-01-25 07:47:32,790 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 20
2025-01-25 07:47:32,820 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 16
2025-01-25 07:47:32,823 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 15
2025-01-25 07:47:32,865 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 28
2025-01-25 07:47:32,879 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 23
2025-01-25 07:47:32,883 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 29
2025-01-25 07:47:32,890 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 4
2025-01-25 07:47:32,914 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 5
2025-01-25 07:47:32,920 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 17
2025-01-25 07:47:32,949 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 18
2025-01-25 07:47:32,966 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 3
2025-01-25 07:47:32,985 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 8
2025-01-25 07:47:33,011 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 26
2025-01-25 07:47:33,012 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 25
2025-01-25 07:47:33,016 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 0
2025-01-25 07:47:33,022 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 11
2025-01-25 07:47:33,039 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 5
2025-01-25 07:47:33,086 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 14
2025-01-25 07:47:33,099 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 10
2025-01-25 07:47:33,119 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 4
2025-01-25 07:47:33,135 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 27
2025-01-25 07:47:33,142 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 22
2025-01-25 07:47:33,144 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 9
2025-01-25 07:47:33,158 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 0
2025-01-25 07:47:33,173 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 2
2025-01-25 07:47:33,189 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 7
2025-01-25 07:47:33,236 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 20
2025-01-25 07:47:33,255 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 16
2025-01-25 07:47:33,295 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 15
2025-01-25 07:47:33,307 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 23
2025-01-25 07:47:33,330 [INFO] root:52 - Job test_graph$$$$A$$ returned: A for task 12
2025-01-25 07:47:33,343 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 24
2025-01-25 07:47:33,374 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 13
2025-01-25 07:47:33,429 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 1
2025-01-25 07:47:33,439 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 21
2025-01-25 07:47:33,453 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 24
2025-01-25 07:47:33,497 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 1
2025-01-25 07:47:33,500 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 6
2025-01-25 07:47:33,522 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 5
2025-01-25 07:47:33,528 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 28
2025-01-25 07:47:33,553 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 15
2025-01-25 07:47:33,554 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 19
2025-01-25 07:47:33,583 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 17
2025-01-25 07:47:33,592 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 28
2025-01-25 07:47:33,592 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 17
2025-01-25 07:47:33,612 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 3
2025-01-25 07:47:33,649 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 18
2025-01-25 07:47:33,660 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 4
2025-01-25 07:47:33,666 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 23
2025-01-25 07:47:33,688 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 2
2025-01-25 07:47:33,704 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 20
2025-01-25 07:47:33,718 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 2
2025-01-25 07:47:33,726 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 22
2025-01-25 07:47:33,736 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 6
2025-01-25 07:47:33,745 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 11
2025-01-25 07:47:33,749 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 21
2025-01-25 07:47:33,754 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 23
2025-01-25 07:47:33,770 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 29
2025-01-25 07:47:33,782 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 20
2025-01-25 07:47:33,821 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 14
2025-01-25 07:47:33,824 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 16
2025-01-25 07:47:33,825 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 18
2025-01-25 07:47:33,852 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 13
2025-01-25 07:47:33,898 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 0
2025-01-25 07:47:33,909 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 0
2025-01-25 07:47:33,919 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 12
2025-01-25 07:47:33,952 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 26
2025-01-25 07:47:33,953 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 8
2025-01-25 07:47:33,953 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 15
2025-01-25 07:47:33,953 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 25
2025-01-25 07:47:33,960 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 16
2025-01-25 07:47:33,981 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 29
2025-01-25 07:47:34,010 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 8
2025-01-25 07:47:34,030 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 6
2025-01-25 07:47:34,033 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 27
2025-01-25 07:47:34,064 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 19
2025-01-25 07:47:34,072 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 26
2025-01-25 07:47:34,091 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 7
2025-01-25 07:47:34,097 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 5
2025-01-25 07:47:34,098 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 7
2025-01-25 07:47:34,110 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 9
2025-01-25 07:47:34,127 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 14
2025-01-25 07:47:34,127 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 18
2025-01-25 07:47:34,143 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 0
2025-01-25 07:47:34,171 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 9
2025-01-25 07:47:34,184 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 16
2025-01-25 07:47:34,190 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 20
2025-01-25 07:47:34,194 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 3
2025-01-25 07:47:34,201 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 22
2025-01-25 07:47:34,221 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 10
2025-01-25 07:47:34,249 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 24
2025-01-25 07:47:34,256 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 19
2025-01-25 07:47:34,261 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 25
2025-01-25 07:47:34,356 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 4
2025-01-25 07:47:34,361 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 12
2025-01-25 07:47:34,397 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 28
2025-01-25 07:47:34,402 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 10
2025-01-25 07:47:34,422 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 11
2025-01-25 07:47:34,460 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 15
2025-01-25 07:47:34,516 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 13
2025-01-25 07:47:34,530 [INFO] root:52 - Job test_graph$$$$B$$ returned: A.B for task 12
2025-01-25 07:47:34,559 [INFO] root:52 - Job test_graph$$$$D$$ returned: A.D for task 27
2025-01-25 07:47:34,560 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 18
2025-01-25 07:47:34,570 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 1
2025-01-25 07:47:34,574 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 26
2025-01-25 07:47:34,613 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 27
2025-01-25 07:47:34,629 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 14
2025-01-25 07:47:34,633 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 8
2025-01-25 07:47:34,638 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 22
2025-01-25 07:47:34,650 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 17
2025-01-25 07:47:34,660 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 8
2025-01-25 07:47:34,675 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 1
2025-01-25 07:47:34,708 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 21
2025-01-25 07:47:34,724 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 26
2025-01-25 07:47:34,744 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 21
2025-01-25 07:47:34,773 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 28
2025-01-25 07:47:34,777 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 5
2025-01-25 07:47:34,778 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 20
2025-01-25 07:47:34,817 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 11
2025-01-25 07:47:34,831 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 24
2025-01-25 07:47:34,843 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 29
2025-01-25 07:47:34,900 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 10
2025-01-25 07:47:34,913 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 3
2025-01-25 07:47:34,955 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 5
2025-01-25 07:47:34,975 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 17
2025-01-25 07:47:35,003 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 6
2025-01-25 07:47:35,005 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 3
2025-01-25 07:47:35,033 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 13
2025-01-25 07:47:35,098 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 16
2025-01-25 07:47:35,099 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 2
2025-01-25 07:47:35,122 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 28
2025-01-25 07:47:35,170 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 07:47:35,170 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 5
2025-01-25 07:47:35,170 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,171 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,171 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,171 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,171 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 5
2025-01-25 07:47:35,175 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 7
2025-01-25 07:47:35,191 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 26
2025-01-25 07:47:35,192 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 29
2025-01-25 07:47:35,193 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 10
Logging level: INFO
2025-01-25 07:47:35,228 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 23
2025-01-25 07:47:35,263 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 11
2025-01-25 07:47:35,264 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 9
2025-01-25 07:47:35,271 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 25
2025-01-25 07:47:35,276 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 25
2025-01-25 07:47:35,296 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 4
2025-01-25 07:47:35,314 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 7
2025-01-25 07:47:35,319 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 07:47:35,320 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 18
2025-01-25 07:47:35,320 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,320 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,321 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,321 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 15
2025-01-25 07:47:35,321 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,321 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 18
2025-01-25 07:47:35,329 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 0
2025-01-25 07:47:35,329 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 0
2025-01-25 07:47:35,329 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,330 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,330 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,330 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,330 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 0
2025-01-25 07:47:35,412 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 8
2025-01-25 07:47:35,448 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 12
2025-01-25 07:47:35,472 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 14
2025-01-25 07:47:35,489 [INFO] root:52 - Job test_graph$$$$C$$ returned: A.A.B.C for task 19
2025-01-25 07:47:35,536 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 07:47:35,536 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 20
2025-01-25 07:47:35,537 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,537 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,537 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,537 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,537 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 20
2025-01-25 07:47:35,603 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 21
2025-01-25 07:47:35,620 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 27
2025-01-25 07:47:35,663 [INFO] root:52 - Job test_graph$$$$F$$ returned: A.D.F for task 9
2025-01-25 07:47:35,665 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 13
2025-01-25 07:47:35,717 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 07:47:35,717 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 28
2025-01-25 07:47:35,717 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,717 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,718 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,718 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,718 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 28
2025-01-25 07:47:35,718 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 5, Active: 25
2025-01-25 07:47:35,723 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 27
2025-01-25 07:47:35,768 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 07:47:35,768 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 17
2025-01-25 07:47:35,768 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,768 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,769 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,769 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,769 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 17
2025-01-25 07:47:35,795 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 07:47:35,795 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 16
2025-01-25 07:47:35,795 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,795 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,795 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,796 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,796 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 16
2025-01-25 07:47:35,810 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 2
2025-01-25 07:47:35,816 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 1
2025-01-25 07:47:35,838 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 7
2025-01-25 07:47:35,873 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 10
2025-01-25 07:47:35,913 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 19
2025-01-25 07:47:35,920 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 22
2025-01-25 07:47:35,975 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 07:47:35,975 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 26
2025-01-25 07:47:35,975 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 3
2025-01-25 07:47:35,976 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,976 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,976 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,977 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:35,977 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 26
2025-01-25 07:47:35,978 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 24
2025-01-25 07:47:35,986 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 6
2025-01-25 07:47:36,113 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 9
2025-01-25 07:47:36,148 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 07:47:36,148 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 15
2025-01-25 07:47:36,148 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,148 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,149 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,149 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,149 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 15
2025-01-25 07:47:36,211 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 29
2025-01-25 07:47:36,211 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 07:47:36,211 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 8
2025-01-25 07:47:36,212 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,212 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,212 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,212 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,212 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 8
2025-01-25 07:47:36,213 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 10, Active: 20
2025-01-25 07:47:36,246 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 07:47:36,247 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 21
2025-01-25 07:47:36,247 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,247 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,247 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,247 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,247 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 21
2025-01-25 07:47:36,254 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 25
2025-01-25 07:47:36,370 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 07:47:36,370 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 14
2025-01-25 07:47:36,371 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,371 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,371 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 4
2025-01-25 07:47:36,371 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 4
2025-01-25 07:47:36,371 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,372 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,372 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,372 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 14
2025-01-25 07:47:36,372 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,372 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,372 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,373 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 4
2025-01-25 07:47:36,496 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 07:47:36,496 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 13
2025-01-25 07:47:36,496 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,496 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,496 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,497 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,497 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 13
2025-01-25 07:47:36,526 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 3
2025-01-25 07:47:36,527 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 3
2025-01-25 07:47:36,527 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,527 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,527 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,527 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,527 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 3
2025-01-25 07:47:36,528 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 15, Active: 15
2025-01-25 07:47:36,591 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 23
2025-01-25 07:47:36,656 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 07:47:36,657 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 24
2025-01-25 07:47:36,657 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,657 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,657 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,657 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,658 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 24
2025-01-25 07:47:36,719 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 11
2025-01-25 07:47:36,753 [INFO] root:52 - Job test_graph$$$$E$$ returned: A.A.B.C.E for task 12
2025-01-25 07:47:36,757 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 07:47:36,757 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 7
2025-01-25 07:47:36,757 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,758 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,758 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,758 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,758 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 7
2025-01-25 07:47:36,770 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 07:47:36,770 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 2
2025-01-25 07:47:36,770 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,770 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,771 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,771 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,771 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 2
2025-01-25 07:47:36,771 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 07:47:36,771 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 22
2025-01-25 07:47:36,772 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,772 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,772 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,772 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,772 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 22
2025-01-25 07:47:36,836 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 07:47:36,836 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 29
2025-01-25 07:47:36,836 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,837 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,837 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,837 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,837 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 29
2025-01-25 07:47:36,838 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 20, Active: 10
2025-01-25 07:47:36,957 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 07:47:36,957 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 19
2025-01-25 07:47:36,958 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,969 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,972 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,973 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,973 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 19
2025-01-25 07:47:36,992 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 07:47:36,992 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 6
2025-01-25 07:47:36,992 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,993 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,993 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,993 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:36,993 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 6
2025-01-25 07:47:37,018 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 07:47:37,018 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 27
2025-01-25 07:47:37,018 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,018 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,018 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,018 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,018 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 27
2025-01-25 07:47:37,101 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 07:47:37,101 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 25
2025-01-25 07:47:37,101 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,101 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,101 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,102 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,102 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 25
2025-01-25 07:47:37,102 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 07:47:37,102 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 10
2025-01-25 07:47:37,102 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,102 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,102 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,103 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,103 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 10
2025-01-25 07:47:37,103 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 25, Active: 5
2025-01-25 07:47:37,289 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 07:47:37,289 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 23
2025-01-25 07:47:37,289 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,289 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,290 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,290 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,290 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 23
2025-01-25 07:47:37,367 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 07:47:37,367 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 1
2025-01-25 07:47:37,367 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,367 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,368 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,368 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,368 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 1
2025-01-25 07:47:37,506 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 07:47:37,506 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 12
2025-01-25 07:47:37,506 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,506 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,507 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,507 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,507 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 12
2025-01-25 07:47:37,530 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 07:47:37,530 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 9
2025-01-25 07:47:37,530 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,531 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,531 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,531 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:37,531 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 9
2025-01-25 07:47:38,112 [INFO] root:52 - Job test_graph$$$$G$$ returned: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 07:47:38,112 [INFO] ConcurrencyTestJob:319 - Tail Job test_graph$$$$G$$ returning result: A.A.B.C.E.A.D.F.G for task 11
2025-01-25 07:47:38,113 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$E$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:38,113 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$C$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:38,113 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$B$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:38,113 [INFO] ConcurrencyTestJob:338 - Job test_graph$$$$A$$ propagating tail result: A.A.B.C.E.A.D.F.G
2025-01-25 07:47:38,113 [INFO] AsyncWorker:390 - [TASK_TRACK] Completed task A.A.B.C.E.A.D.F.G, returned by job test_graph$$$$G$$, for task 11
2025-01-25 07:47:38,114 [INFO] AsyncWorker:449 - Tasks stats - Created: 30, Completed: 30, Active: 0
2025-01-25 07:47:38,114 [INFO] AsyncWorker:463 - *** result_queue ended ***
2025-01-25 07:47:38,114 [INFO] AsyncWorker:478 - Closing event loop
2025-01-25 07:47:38,247 [INFO] JobChain:121 - Cleaning up JobChain resources
.

================================================= 1 passed in 7.79s ==================================================
(.venv) davidroberts [JobChain] (main)$ 