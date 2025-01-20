import subprocess
import sys

packages = [
    "aiolimiter",
    "python-dotenv",
    "openai",
    "opentelemetry-sdk",
    "opentelemetry-exporter-otlp-proto-grpc",
    "anyconfig",
    "pyyaml"
]

print("Package Versions:")
print("-" * 40)
for pkg in packages:
    result = subprocess.run([sys.executable, "-m", "pip", "show", pkg], 
                          capture_output=True, text=True)
    if result.stdout:
        for line in result.stdout.split('\n'):
            if line.startswith('Name: ') or line.startswith('Version: '):
                print(line.strip())
    else:
        print(f"{pkg}: Not found")
    print("-" * 40)
