import importlib.metadata

# For installed packages show the package and version
packages = ["aiolimiter", "python-dotenv", "openai", "opentelemetry-sdk", "opentelemetry-exporter-otlp-proto-grpc", "anyconfig", "pyyaml"]

for package in packages:
    try:
         version = importlib.metadata.version(package)
         print(f"{package}: {version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{package}: Not found")