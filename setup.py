from setuptools import find_packages, setup

setup(
    name='jobchain',
    version='0.1.0',
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
      "jobchain": ["resources/*"]
    },
    install_requires=[
        'python-dotenv>=1.0.1',
        'openai>=1.58.0',
        'opentelemetry-sdk>=1.28.1' ,
        'opentelemetry-exporter-otlp-proto-grpc>=1.28.1',
        'anyconfig>=0.14.0',
        'pyyaml>=6.0.2'
    ],
    python_requires='>=3.8.5',
    # other options can be added here
)