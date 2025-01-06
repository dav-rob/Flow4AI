import argparse
import ast
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, NamedTuple, Set


class ImportInfo(NamedTuple):
    """Information about where and how a package is imported."""
    file_path: str
    import_statement: str
    line_number: int

STDLIB_MODULES = sys.stdlib_module_names

def normalize_package_name(name: str) -> str:
    """Normalize package names to their pip-installable form."""
    PACKAGE_MAPPINGS = package_map = {
    'yaml': 'pyyaml',
    'dotenv': 'python-dotenv',
    'PIL': 'pillow',
    'bs4': 'beautifulsoup4',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'mx': 'mxnet',
    'tf': 'tensorflow',
    'px': 'plotly-express',
    'psycopg2': 'psycopg2-binary'
}

    root_name = name.split('.')[0].lower()
    return PACKAGE_MAPPINGS.get(root_name, root_name)

def is_stdlib_module(module_name: str) -> bool:
    """Check if a module is part of the Python standard library."""
    return module_name.split('.')[0].lower() in STDLIB_MODULES

def _get_package_name(project_root: Path) -> str:
    """Detect the main package name by looking at src directory structure."""
    src_dir = project_root / 'src'
    if src_dir.exists():
        # Look for the first directory in src that contains an __init__.py
        for item in src_dir.iterdir():
            if item.is_dir() and (item / '__init__.py').exists():
                return item.name
    return ''

def is_local_module(module_name: str, project_root: Path) -> bool:
    """Check if a module is local to the project."""
    package_name = _get_package_name(project_root)
    if package_name:
        # Check if it's part of our own package
        if module_name.startswith(f"{package_name}.") or module_name == package_name:
            return True
        
    # Check src directory specifically for project modules
    src_dir = project_root / 'src'
    if src_dir.exists() and package_name:
        module_parts = module_name.split('.')
        possible_src_paths = [
            src_dir / package_name / '/'.join(module_parts) / "__init__.py",
            src_dir / package_name / '/'.join(module_parts[:-1]) / (module_parts[-1] + ".py") if module_parts else src_dir / (module_name + ".py"),
            src_dir / package_name / module_parts[0]
        ]
        if any(path.exists() for path in possible_src_paths):
            return True
    
    return False

def is_vendor_path(file_path: str) -> bool:
    """Check if a file is in a vendor directory or site-packages."""
    vendor_indicators = {
        'site-packages',
        'vendor',
        '.venv',
        'venv',
        'virtualenv',
        'env',
    }
    return any(indicator in file_path for indicator in vendor_indicators)

def extract_imports_from_file(file_path: str, project_root: Path) -> Dict[str, ImportInfo]:
    """Extract import statements from a Python file with context."""
    imports = {}
    
    # Skip vendor directories
    if is_vendor_path(file_path):
        return imports
    
    rel_path = os.path.relpath(file_path, project_root)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            if not name.name.startswith('.'):
                                module_name = name.name
                                if not is_stdlib_module(module_name):
                                    if not is_local_module(module_name, project_root):
                                        package = normalize_package_name(module_name)
                                        imports[package] = ImportInfo(
                                            rel_path,
                                            f"import {name.name}",
                                            node.lineno
                                        )
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and not node.module.startswith('.'):
                            module_name = node.module
                            if not is_stdlib_module(module_name):
                                if not is_local_module(module_name, project_root):
                                    package = normalize_package_name(module_name)
                                    names = ', '.join(n.name for n in node.names)
                                    imports[package] = ImportInfo(
                                        rel_path,
                                        f"from {node.module} import {names}",
                                        node.lineno
                                    )
            except SyntaxError:
                print(f"Syntax error in file: {rel_path}")
    except Exception as e:
        print(f"Error processing file {rel_path}: {str(e)}")
    
    return imports

def find_python_files(root_dir: str, recursive: bool = False) -> List[str]:
    """Find all Python files in the given directory.
    
    Args:
        root_dir: Directory to search in
        recursive: If True, search in subdirectories as well
    """
    python_files = []
    if recursive:
        # Walk through all subdirectories
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
    else:
        # Only look in the specified directory
        for item in os.listdir(root_dir):
            full_path = os.path.join(root_dir, item)
            if os.path.isfile(full_path) and item.endswith('.py'):
                python_files.append(full_path)
    return python_files

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Extract Python package imports from a codebase.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default search directories
  python extract_imports.py

  # Specify custom search directories
  python extract_imports.py --dirs path1 path2 path3

  # Search the entire project
  python extract_imports.py --dirs .
        """
    )
    
    parser.add_argument(
        '--dirs',
        nargs='*',
        help='Directories to search for Python files. If not specified, defaults to: '
             '[project_root, project_root/util, project_root/linkedIn_App]'
    )
    
    return parser.parse_args()

def analyse_imports(project_root, search_dirs):
    # Validate directories exist
    for directory in search_dirs:
        if not directory.exists():
            print(f"Warning: Directory does not exist: {directory}")
    # Print search directories
    print("Searching in directories:")
    for directory in search_dirs:
        print(f"  • {directory}")
    print()
    # Collect all Python files
    python_files = []
    for directory in search_dirs:
        if directory.exists():
            # Search recursively if explicitly specified with --dirs or if searching entire project root
            recursive = len(search_dirs) == 1 and (search_dirs[0] == project_root or search_dirs[0] != project_root)
            python_files.extend(find_python_files(str(directory), recursive=recursive))
    # Extract all imports with their context
    all_imports: Dict[str, List[ImportInfo]] = defaultdict(list)
    external_imports: Dict[str, List[ImportInfo]] = defaultdict(list)
    for file_path in python_files:
        file_imports = extract_imports_from_file(file_path, project_root)
        for package, info in file_imports.items():
            all_imports[package].append(info)
            if not is_local_module(package, project_root):
                external_imports[package].append(info)
    
    # Write results to files
    requirements_file = project_root / 'dev_resources' / 'requirements_extracted.txt'
    report_file = project_root / 'dev_resources' / 'import_report.txt'
    with open(requirements_file, 'w') as f_req, open(report_file, 'w') as f_report:
        f_report.write("Third-Party Package Usage Report\n")
        f_report.write("============================\n\n")

        if all_imports:
            f_report.write("Direct Dependencies Found:\n")
            f_report.write("----------------------\n")
            for package, import_infos in sorted(all_imports.items()):
                # Only write external dependencies to requirements
                if package in external_imports:
                    f_req.write(f"{package}\n")
                f_report.write(f"\n{package}:\n")
                for info in import_infos:
                    f_report.write(f"  • {info.file_path} (line {info.line_number})\n")
        else:
            f_report.write("No third-party imports found.\n")
    print(f"Package report has been saved to: {report_file}")
    print(f"Requirements file has been saved to: {requirements_file}")
    # Print direct dependencies to console
    print("\nDirect Dependencies Found:")
    for package, import_infos in sorted(all_imports.items()):
        print(f"\n{package}:")
        for info in import_infos:
            print(f"  • {info.file_path} (line {info.line_number})")
    
    # Generate pip install command only for external dependencies
    if external_imports:
        print("\nTo import these libraries run:")
        print(f"pip install {' '.join(sorted(external_imports.keys()))}")

def get_default_search_dirs(project_root: Path) -> List[Path]:
    """Get the default search directories relative to the project root."""
    return [
        project_root,  # Root directory
        project_root / 'util',  # Util directory
    ]

def main():
    """
    Main function for the script.
    
    Usage:
        python dev_resources/extract_imports.py [--dirs <dir1> [<dir2> ...]]
    
    Arguments:
        --dirs <dir1> [<dir2> ...]: List of directories to search for Python files. If not specified, defaults to:
            [project_root, project_root/util, project_root/linkedIn_App]
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent

    # Parse command line arguments
    args = parse_args()

    # Determine search directories
    if args.dirs:
        # Convert relative paths to absolute paths, relative to project root
        search_dirs = [project_root / d if not os.path.isabs(d) else Path(d) for d in args.dirs]
    else:
        search_dirs = get_default_search_dirs(project_root)

    analyse_imports(project_root, search_dirs)

if __name__ == '__main__':
    main()
