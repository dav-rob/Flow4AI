from setuptools import find_packages, setup

setup(
    name='flow4ai',
    version='0.1.0',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
      "flow4ai": ["resources/*"]
    },
    install_requires=[
        'aiolimiter>=1.2.1',
        'python-dotenv>=1.0.1',
        'openai>=1.58.0',
        'opentelemetry-sdk>=1.28.1' ,
        'opentelemetry-exporter-otlp-proto-grpc>=1.28.1',
        'anyconfig>=0.14.0',
        'pyyaml>=6.0.2',
        'contextvars>=2.4',
        "pydantic>=2.10.4"
    ],
    extras_require={
        'test': [
            'pytest>=8.3.4',
            'psutil>=6.1.1',
            'pytest-asyncio>=0.25.1',
        "aiofiles>=24.1.0",
        "aiohttp>=3.11.12",
        "networkx>=3.4.2",
        "matplotlib==3.10.1"
        ],
        'dev': [
          "gitingest>=0.1.3"
        ],
    },
    python_requires='>=3.8.5',
    # other options can be added here
)