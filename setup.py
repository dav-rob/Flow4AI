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
        'pytest>=7.0.0',
        'pytest-asyncio>=0.21.0',
        'importlib-resources>=5.0.0',
        'opentelemetry-api>=1.0.0',
        'pyyaml>=6.0.0'
    ],
    python_requires='>=3.6',
    # other options can be added here
)