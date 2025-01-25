(.venv) davidroberts [JobChain] (main)$ python -m pytest tests/test_concurrency.py::test_concurrency_by_expected_returns -s
Logging level: INFO
======================================================================= test session starts =======================================================================
platform darwin -- Python 3.11.11, pytest-8.3.4, pluggy-1.5.0
rootdir: /Users/davidroberts/projects/JobChain
configfile: pytest.ini
plugins: anyio-4.8.0, asyncio-0.25.1
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=function
collected 1 item                                                                                                                                                  

tests/test_concurrency.py 2025-01-25 01:19:49 [INFO] JobChain:47 - Initializing JobChain
2025-01-25 01:19:49 [INFO] JobChain:180 - Job executor process started with PID 93547
2025-01-25 01:19:49 [INFO] JobChain:190 - Result processor process started with PID 93548
Logging level: INFO
Logging level: INFO
2025-01-25 01:19:49 [INFO] AsyncWorker:358 - Creating job map from JobLoader
2025-01-25 01:19:49 [INFO] AsyncWorker:359 - Using directories from process: ['/Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns']
2025-01-25 01:19:49 [INFO] jobchain.job_loader:66 - Added /Users/davidroberts/projects/JobChain/src/jobchain/jobs to Python path
2025-01-25 01:19:49 [INFO] jobchain.job_loader:74 - Loading jobs from /Users/davidroberts/projects/JobChain/src/jobchain/jobs/llm_jobs.py
2025-01-25 01:19:49 [INFO] jobchain.job_loader:91 - Found valid job class: OpenAIJob
Registered custom job: OpenAIJob
2025-01-25 01:19:49 [INFO] jobchain.job_loader:66 - Added /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns/jobs to Python path
2025-01-25 01:19:49 [INFO] jobchain.job_loader:74 - Loading jobs from /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns/jobs/concurrent_jobs.py
2025-01-25 01:19:49 [INFO] jobchain.job_loader:91 - Found valid job class: ConcurrencyTestJob
Registered custom job: ConcurrencyTestJob
2025-01-25 01:19:49 [INFO] jobchain.job_loader:531 - Reloading configs...
2025-01-25 01:19:49 [INFO] jobchain.job_loader:275 - Looking for config files in directories: [PosixPath('/Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns')]
2025-01-25 01:19:49 [INFO] jobchain.job_loader:295 - Found valid jobchain directory: /Users/davidroberts/projects/JobChain/tests/test_configs/test_concurrency_by_returns

Checking test_graph for cycles...
No cycles detected
Graph test_graph passed all validations
2025-01-25 01:19:49 [INFO] AsyncWorker:368 - Created job map with head jobs: ['test_graph$$$$A$$']
2025-01-25 01:19:49 [INFO] root:36 - Names of jobs in head job: {'test_graph$$$$A$$': {'test_graph$$$$D$$', 'test_graph$$$$A$$', 'test_graph$$$$F$$', 'test_graph$$$$C$$', 'test_graph$$$$B$$', 'test_graph$$$$E$$', 'test_graph$$$$G$$'}}
2025-01-25 01:19:49 [INFO] JobChain:259 - *** task_queue ended ***
2025-01-25 01:19:49 [INFO] AsyncWorker:413 - Received end signal in task queue
2025-01-25 01:19:52 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=92b99449-7504-45a2-8f90-df8320988d4d, job_name=test_graph$$$$A$$, data={'task': '10', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:52 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=92b99449-7504-45a2-8f90-df8320988d4d, job_name=test_graph$$$$A$$, data={'task': '10', 'job_name': 'test_graph$$$$A$$'})}
Logging level: INFO
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=d4470a61-99b8-4d18-99c9-42216ca27a48, job_name=test_graph$$$$A$$, data={'task': '16', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=d4470a61-99b8-4d18-99c9-42216ca27a48, job_name=test_graph$$$$A$$, data={'task': '16', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=28322281-5355-47ae-aa71-f0831f97c7c6, job_name=test_graph$$$$A$$, data={'task': '33', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=28322281-5355-47ae-aa71-f0831f97c7c6, job_name=test_graph$$$$A$$, data={'task': '33', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=0f751a3f-f2b0-49b1-845e-6139eca34220, job_name=test_graph$$$$A$$, data={'task': '49', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=0f751a3f-f2b0-49b1-845e-6139eca34220, job_name=test_graph$$$$A$$, data={'task': '49', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=41ba4553-4200-43b6-ad3b-e98d6484260f, job_name=test_graph$$$$A$$, data={'task': '23', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 5, Active: 65
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=41ba4553-4200-43b6-ad3b-e98d6484260f, job_name=test_graph$$$$A$$, data={'task': '23', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a5c8694c-d1bb-42e0-8446-b34a0394b9bf, job_name=test_graph$$$$A$$, data={'task': '51', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a5c8694c-d1bb-42e0-8446-b34a0394b9bf, job_name=test_graph$$$$A$$, data={'task': '51', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=42d271c6-ab79-4ecc-a8b3-dc88ad04796e, job_name=test_graph$$$$A$$, data={'task': '62', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=42d271c6-ab79-4ecc-a8b3-dc88ad04796e, job_name=test_graph$$$$A$$, data={'task': '62', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=32218625-b1a1-4177-b21c-c163130ec196, job_name=test_graph$$$$A$$, data={'task': '0', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=32218625-b1a1-4177-b21c-c163130ec196, job_name=test_graph$$$$A$$, data={'task': '0', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f48b7b9c-d36e-4d15-93f9-b4ce5ea85895, job_name=test_graph$$$$A$$, data={'task': '39', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f48b7b9c-d36e-4d15-93f9-b4ce5ea85895, job_name=test_graph$$$$A$$, data={'task': '39', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=b2f8e373-70f1-4f67-be99-842a4a8791b5, job_name=test_graph$$$$A$$, data={'task': '36', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 10, Active: 60
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=b2f8e373-70f1-4f67-be99-842a4a8791b5, job_name=test_graph$$$$A$$, data={'task': '36', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=56bcbe98-1bc4-4a84-b6f1-103eb0b2b31b, job_name=test_graph$$$$A$$, data={'task': '63', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=56bcbe98-1bc4-4a84-b6f1-103eb0b2b31b, job_name=test_graph$$$$A$$, data={'task': '63', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=44417651-9881-4c95-a5ba-dc742774defb, job_name=test_graph$$$$A$$, data={'task': '60', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=44417651-9881-4c95-a5ba-dc742774defb, job_name=test_graph$$$$A$$, data={'task': '60', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=11138628-7e39-4852-b0c2-fbb23fb1a8d6, job_name=test_graph$$$$A$$, data={'task': '57', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=11138628-7e39-4852-b0c2-fbb23fb1a8d6, job_name=test_graph$$$$A$$, data={'task': '57', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=c5de4ed3-6f2f-4681-be98-36322d5d2e05, job_name=test_graph$$$$A$$, data={'task': '30', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=c5de4ed3-6f2f-4681-be98-36322d5d2e05, job_name=test_graph$$$$A$$, data={'task': '30', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f9c2eefa-d687-407d-92a2-c2625dcbe471, job_name=test_graph$$$$A$$, data={'task': '12', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 15, Active: 55
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f9c2eefa-d687-407d-92a2-c2625dcbe471, job_name=test_graph$$$$A$$, data={'task': '12', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=bdb5dbda-8063-429c-95bb-bf4a34432080, job_name=test_graph$$$$A$$, data={'task': '3', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=bdb5dbda-8063-429c-95bb-bf4a34432080, job_name=test_graph$$$$A$$, data={'task': '3', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=e40c723b-e3b9-458f-ac55-bde891b8069c, job_name=test_graph$$$$A$$, data={'task': '20', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=e40c723b-e3b9-458f-ac55-bde891b8069c, job_name=test_graph$$$$A$$, data={'task': '20', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=e8ce6fa2-1a9c-4237-9d03-187eb9344a1f, job_name=test_graph$$$$A$$, data={'task': '52', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=e8ce6fa2-1a9c-4237-9d03-187eb9344a1f, job_name=test_graph$$$$A$$, data={'task': '52', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:53 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a7bbef97-a0bb-44a9-a781-3b243d3780a6, job_name=test_graph$$$$A$$, data={'task': '34', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=7b90fccf-7915-4fd6-a0c1-e47e71b90d39, job_name=test_graph$$$$A$$, data={'task': '64', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a7bbef97-a0bb-44a9-a781-3b243d3780a6, job_name=test_graph$$$$A$$, data={'task': '34', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=7b90fccf-7915-4fd6-a0c1-e47e71b90d39, job_name=test_graph$$$$A$$, data={'task': '64', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 20, Active: 50
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=1670062c-f0c4-414b-938b-a2d533b2bfc2, job_name=test_graph$$$$A$$, data={'task': '4', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=1670062c-f0c4-414b-938b-a2d533b2bfc2, job_name=test_graph$$$$A$$, data={'task': '4', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=c4ef6fb2-acc8-4912-8d1c-b7ea60801568, job_name=test_graph$$$$A$$, data={'task': '50', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=c4ef6fb2-acc8-4912-8d1c-b7ea60801568, job_name=test_graph$$$$A$$, data={'task': '50', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a569638d-fc30-4155-98aa-5800c44c3d11, job_name=test_graph$$$$A$$, data={'task': '31', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a569638d-fc30-4155-98aa-5800c44c3d11, job_name=test_graph$$$$A$$, data={'task': '31', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=31f9d2b6-7700-4c59-9901-af3913c64ee8, job_name=test_graph$$$$A$$, data={'task': '24', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=440e103d-535d-4245-951a-48f30c503067, job_name=test_graph$$$$A$$, data={'task': '14', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=31f9d2b6-7700-4c59-9901-af3913c64ee8, job_name=test_graph$$$$A$$, data={'task': '24', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=440e103d-535d-4245-951a-48f30c503067, job_name=test_graph$$$$A$$, data={'task': '14', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 25, Active: 45
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=dd236727-78ab-4f16-aa74-cc1db4b984e9, job_name=test_graph$$$$A$$, data={'task': '53', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=4ada4d7e-b9bd-4e37-8e87-a3884e2f71df, job_name=test_graph$$$$A$$, data={'task': '35', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=61002291-3f95-4590-9893-267661e35970, job_name=test_graph$$$$A$$, data={'task': '68', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=dd236727-78ab-4f16-aa74-cc1db4b984e9, job_name=test_graph$$$$A$$, data={'task': '53', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=4ada4d7e-b9bd-4e37-8e87-a3884e2f71df, job_name=test_graph$$$$A$$, data={'task': '35', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=35b505ba-6145-4bd7-abf6-db2c51c862cc, job_name=test_graph$$$$A$$, data={'task': '54', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=61002291-3f95-4590-9893-267661e35970, job_name=test_graph$$$$A$$, data={'task': '68', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=0db5dcf6-515e-4be4-b3dc-a3e019ec0d6f, job_name=test_graph$$$$A$$, data={'task': '45', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=35b505ba-6145-4bd7-abf6-db2c51c862cc, job_name=test_graph$$$$A$$, data={'task': '54', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 30, Active: 40
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=0db5dcf6-515e-4be4-b3dc-a3e019ec0d6f, job_name=test_graph$$$$A$$, data={'task': '45', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=88a70a95-d50f-4a34-b84b-5e80fd6f52db, job_name=test_graph$$$$A$$, data={'task': '69', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=88a70a95-d50f-4a34-b84b-5e80fd6f52db, job_name=test_graph$$$$A$$, data={'task': '69', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=0094676c-c8d4-428b-b72a-3f02c78720eb, job_name=test_graph$$$$A$$, data={'task': '25', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=0094676c-c8d4-428b-b72a-3f02c78720eb, job_name=test_graph$$$$A$$, data={'task': '25', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a430e256-50c9-4437-853d-5f7117ac21ed, job_name=test_graph$$$$A$$, data={'task': '6', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a430e256-50c9-4437-853d-5f7117ac21ed, job_name=test_graph$$$$A$$, data={'task': '6', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=60d5f51f-115e-4833-a25d-df6830998213, job_name=test_graph$$$$A$$, data={'task': '66', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=60d5f51f-115e-4833-a25d-df6830998213, job_name=test_graph$$$$A$$, data={'task': '66', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=e3a3e177-4a27-4e09-a232-bef71dddae7f, job_name=test_graph$$$$A$$, data={'task': '38', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=e3a3e177-4a27-4e09-a232-bef71dddae7f, job_name=test_graph$$$$A$$, data={'task': '38', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 35, Active: 35
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=b9991b6d-12f4-4ed5-bf58-c0fcf9ded159, job_name=test_graph$$$$A$$, data={'task': '26', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=b9991b6d-12f4-4ed5-bf58-c0fcf9ded159, job_name=test_graph$$$$A$$, data={'task': '26', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=b0cedf87-77a6-49ff-9437-c7aa6998f612, job_name=test_graph$$$$A$$, data={'task': '46', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=b0cedf87-77a6-49ff-9437-c7aa6998f612, job_name=test_graph$$$$A$$, data={'task': '46', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=fdb82caf-2e40-4ed5-a536-05ee6875f8ca, job_name=test_graph$$$$A$$, data={'task': '1', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=b35de45d-3991-42b0-bf25-dbad58be55c8, job_name=test_graph$$$$A$$, data={'task': '44', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=fdb82caf-2e40-4ed5-a536-05ee6875f8ca, job_name=test_graph$$$$A$$, data={'task': '1', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=b35de45d-3991-42b0-bf25-dbad58be55c8, job_name=test_graph$$$$A$$, data={'task': '44', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=07ca830b-a396-49de-a821-40235d48d5c7, job_name=test_graph$$$$A$$, data={'task': '19', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=07ca830b-a396-49de-a821-40235d48d5c7, job_name=test_graph$$$$A$$, data={'task': '19', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 40, Active: 30
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=4a7e2e43-0488-401e-aa27-774ed69bf5e3, job_name=test_graph$$$$A$$, data={'task': '18', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=4a7e2e43-0488-401e-aa27-774ed69bf5e3, job_name=test_graph$$$$A$$, data={'task': '18', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=bc152654-3849-43ea-87f8-3f7fb770c028, job_name=test_graph$$$$A$$, data={'task': '55', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=bc152654-3849-43ea-87f8-3f7fb770c028, job_name=test_graph$$$$A$$, data={'task': '55', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=8ebd3ceb-21fb-4454-ae48-2204421a3acb, job_name=test_graph$$$$A$$, data={'task': '11', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=8ebd3ceb-21fb-4454-ae48-2204421a3acb, job_name=test_graph$$$$A$$, data={'task': '11', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=28787498-d8d5-4838-933b-8513aad23057, job_name=test_graph$$$$A$$, data={'task': '28', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=28787498-d8d5-4838-933b-8513aad23057, job_name=test_graph$$$$A$$, data={'task': '28', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=9fe6f432-ff3e-4829-bd6e-a7b583670e9d, job_name=test_graph$$$$A$$, data={'task': '40', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=9fe6f432-ff3e-4829-bd6e-a7b583670e9d, job_name=test_graph$$$$A$$, data={'task': '40', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 45, Active: 25
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=9801dc64-655b-4740-b381-6891f0cd5c7c, job_name=test_graph$$$$A$$, data={'task': '5', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=9801dc64-655b-4740-b381-6891f0cd5c7c, job_name=test_graph$$$$A$$, data={'task': '5', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=1dfc157b-8ba7-4111-8361-bf6092c6777d, job_name=test_graph$$$$A$$, data={'task': '17', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=1dfc157b-8ba7-4111-8361-bf6092c6777d, job_name=test_graph$$$$A$$, data={'task': '17', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=5a3da1ef-9464-4bd7-89a8-3a53aeeb2f46, job_name=test_graph$$$$A$$, data={'task': '8', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=5a3da1ef-9464-4bd7-89a8-3a53aeeb2f46, job_name=test_graph$$$$A$$, data={'task': '8', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=ed17dc92-e5f3-4570-8de4-8a3f462e2e78, job_name=test_graph$$$$A$$, data={'task': '22', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=ed17dc92-e5f3-4570-8de4-8a3f462e2e78, job_name=test_graph$$$$A$$, data={'task': '22', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=8045537e-1856-426e-a5f4-426ff41ede75, job_name=test_graph$$$$A$$, data={'task': '9', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=8045537e-1856-426e-a5f4-426ff41ede75, job_name=test_graph$$$$A$$, data={'task': '9', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 50, Active: 20
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=75482382-5ef5-4187-81c2-685270a8e269, job_name=test_graph$$$$A$$, data={'task': '7', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=75482382-5ef5-4187-81c2-685270a8e269, job_name=test_graph$$$$A$$, data={'task': '7', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=87eeb545-4677-4a90-b999-ec49c4f2ddf4, job_name=test_graph$$$$A$$, data={'task': '21', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=87eeb545-4677-4a90-b999-ec49c4f2ddf4, job_name=test_graph$$$$A$$, data={'task': '21', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=e60080dc-7288-41ec-b355-4c1170671cdb, job_name=test_graph$$$$A$$, data={'task': '32', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=e60080dc-7288-41ec-b355-4c1170671cdb, job_name=test_graph$$$$A$$, data={'task': '32', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f779d1bb-a4de-44f2-a576-43f73f3690f2, job_name=test_graph$$$$A$$, data={'task': '61', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f779d1bb-a4de-44f2-a576-43f73f3690f2, job_name=test_graph$$$$A$$, data={'task': '61', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=6ead0e77-dca0-4d4b-ada5-7bbc62d3a67b, job_name=test_graph$$$$A$$, data={'task': '13', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 55, Active: 15
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=6ead0e77-dca0-4d4b-ada5-7bbc62d3a67b, job_name=test_graph$$$$A$$, data={'task': '13', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a2e0ffcc-e5d1-4aee-a852-d435ee8efaa7, job_name=test_graph$$$$A$$, data={'task': '15', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a2e0ffcc-e5d1-4aee-a852-d435ee8efaa7, job_name=test_graph$$$$A$$, data={'task': '15', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=977d0bca-73ca-465e-a79d-1c199c97d86e, job_name=test_graph$$$$A$$, data={'task': '2', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=977d0bca-73ca-465e-a79d-1c199c97d86e, job_name=test_graph$$$$A$$, data={'task': '2', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=da644158-4239-42ba-9ef9-7f84a679b74d, job_name=test_graph$$$$A$$, data={'task': '47', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:54 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=da644158-4239-42ba-9ef9-7f84a679b74d, job_name=test_graph$$$$A$$, data={'task': '47', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=50ff77ee-bfa2-4ed0-9429-35868a843d65, job_name=test_graph$$$$A$$, data={'task': '67', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f770d1ee-bfcd-4715-aadc-27301f672197, job_name=test_graph$$$$A$$, data={'task': '65', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=50ff77ee-bfa2-4ed0-9429-35868a843d65, job_name=test_graph$$$$A$$, data={'task': '67', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=f770d1ee-bfcd-4715-aadc-27301f672197, job_name=test_graph$$$$A$$, data={'task': '65', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 60, Active: 10
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a77c49be-b78a-40d1-9f78-4e5679f36814, job_name=test_graph$$$$A$$, data={'task': '27', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a77c49be-b78a-40d1-9f78-4e5679f36814, job_name=test_graph$$$$A$$, data={'task': '27', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a18d57ed-9c12-474e-a864-e71b30522770, job_name=test_graph$$$$A$$, data={'task': '42', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a18d57ed-9c12-474e-a864-e71b30522770, job_name=test_graph$$$$A$$, data={'task': '42', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=a19f6719-1bb7-4da8-9e05-8a8fe99fd184, job_name=test_graph$$$$A$$, data={'task': '29', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E', 'task_pass_through': Task(id=a19f6719-1bb7-4da8-9e05-8a8fe99fd184, job_name=test_graph$$$$A$$, data={'task': '29', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=38729701-2f7a-4fe2-a15e-ebed3972c8df, job_name=test_graph$$$$A$$, data={'task': '41', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=38729701-2f7a-4fe2-a15e-ebed3972c8df, job_name=test_graph$$$$A$$, data={'task': '41', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=68aa7e30-0bea-4c57-bdd0-36469525cdcc, job_name=test_graph$$$$A$$, data={'task': '48', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 65, Active: 5
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=68aa7e30-0bea-4c57-bdd0-36469525cdcc, job_name=test_graph$$$$A$$, data={'task': '48', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=28857b59-fa9e-4cb2-add9-49ce614b1b71, job_name=test_graph$$$$A$$, data={'task': '58', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=28857b59-fa9e-4cb2-add9-49ce614b1b71, job_name=test_graph$$$$A$$, data={'task': '58', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=7d0bed93-28f1-4863-a0bb-954e609d63ed, job_name=test_graph$$$$A$$, data={'task': '43', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=7d0bed93-28f1-4863-a0bb-954e609d63ed, job_name=test_graph$$$$A$$, data={'task': '43', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=cc054cb2-4923-4a58-a9e2-be108c986da6, job_name=test_graph$$$$A$$, data={'task': '37', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=cc054cb2-4923-4a58-a9e2-be108c986da6, job_name=test_graph$$$$A$$, data={'task': '37', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=cc6df2c6-d5ef-4939-abf4-a555fa46c132, job_name=test_graph$$$$A$$, data={'task': '59', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=cc6df2c6-d5ef-4939-abf4-a555fa46c132, job_name=test_graph$$$$A$$, data={'task': '59', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] ConcurrencyTestJob:333 - Job test_graph$$$$G$$ returning result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=68732a3a-edd2-4351-8a74-7ffa300b1f50, job_name=test_graph$$$$A$$, data={'task': '56', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] AsyncWorker:449 - Tasks stats - Created: 70, Completed: 70, Active: 0
2025-01-25 01:19:55 [INFO] ResultProcessor:279 - ResultProcessor received result: {'result': 'A.A.B.C.E.A.D.F.G', 'task_pass_through': Task(id=68732a3a-edd2-4351-8a74-7ffa300b1f50, job_name=test_graph$$$$A$$, data={'task': '56', 'job_name': 'test_graph$$$$A$$'})}
2025-01-25 01:19:55 [INFO] AsyncWorker:463 - *** result_queue ended ***
2025-01-25 01:19:55 [INFO] AsyncWorker:478 - Closing event loop
2025-01-25 01:19:56 [INFO] JobChain:121 - Cleaning up JobChain resources
F

============================================================================ FAILURES =============================================================================
______________________________________________________________ test_concurrency_by_expected_returns _______________________________________________________________

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
    
    
        submit_task(70)
    
        job_chain.mark_input_completed() # this waits for all results to be returned
    
>       check_results()

tests/test_concurrency.py:54: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

    def check_results():
        for result in shared_results:
            #logging.info(f"Result: {result}")
>           assert result['result'] == 'A.A.B.C.E.A.D.F.G'
E           AssertionError: assert 'A.A.B.C.E' == 'A.A.B.C.E.A.D.F.G'
E             
E             - A.A.B.C.E.A.D.F.G
E             + A.A.B.C.E

tests/test_concurrency.py:45: AssertionError
------------------------------------------------------------------------ Captured log call ------------------------------------------------------------------------
INFO     JobChain:job_chain.py:47 Initializing JobChain
INFO     JobChain:job_chain.py:180 Job executor process started with PID 93547
INFO     JobChain:job_chain.py:190 Result processor process started with PID 93548
INFO     root:test_concurrency.py:36 Names of jobs in head job: {'test_graph$$$$A$$': {'test_graph$$$$D$$', 'test_graph$$$$A$$', 'test_graph$$$$F$$', 'test_graph$$$$C$$', 'test_graph$$$$B$$', 'test_graph$$$$E$$', 'test_graph$$$$G$$'}}
INFO     JobChain:job_chain.py:259 *** task_queue ended ***
INFO     JobChain:job_chain.py:121 Cleaning up JobChain resources
===================================================================== short test summary info =====================================================================
FAILED tests/test_concurrency.py::test_concurrency_by_expected_returns - AssertionError: assert 'A.A.B.C.E' == 'A.A.B.C.E.A.D.F.G'
======================================================================== 1 failed in 7.17s ========================================================================
(.venv) davidroberts [JobChain] (main)$ 