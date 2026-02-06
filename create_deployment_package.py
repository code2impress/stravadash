#!/usr/bin/env python3
"""
Create a deployment package for PythonAnywhere
Excludes cache, pycache, .env, and other unnecessary files
"""

import os
import zipfile
from pathlib import Path

# Files and directories to exclude
EXCLUDE_PATTERNS = [
    'cache/',
    '__pycache__/',
    '.env',
    'cred.env',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.git/',
    '.vscode/',
    'venv/',
    'env/',
    '*.zip',
    'create_deployment_package.py',
    '.gitignore',
    '.DS_Store',
    'Thumbs.db',
]

def should_exclude(file_path, exclude_patterns):
    """Check if file should be excluded based on patterns"""
    file_path_str = str(file_path)

    for pattern in exclude_patterns:
        # Check if it's a directory pattern
        if pattern.endswith('/'):
            if pattern.rstrip('/') in file_path_str.split(os.sep):
                return True
        # Check if it's a file extension pattern
        elif pattern.startswith('*.'):
            if file_path_str.endswith(pattern[1:]):
                return True
        # Check exact match
        elif pattern in file_path_str:
            return True

    return False

def create_deployment_zip():
    """Create ZIP file for deployment"""
    project_dir = Path(__file__).parent
    zip_name = 'Strava-Live-Stats-Deploy.zip'
    zip_path = project_dir / zip_name

    print(f"Creating deployment package: {zip_name}")
    print("=" * 60)

    included_files = []
    excluded_files = []

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            root_path = Path(root)

            # Skip excluded directories
            dirs[:] = [d for d in dirs if not should_exclude(root_path / d, EXCLUDE_PATTERNS)]

            for file in files:
                file_path = root_path / file
                relative_path = file_path.relative_to(project_dir)

                # Skip excluded files
                if should_exclude(relative_path, EXCLUDE_PATTERNS):
                    excluded_files.append(str(relative_path))
                    continue

                # Add to ZIP (handle old timestamps)
                try:
                    zipf.write(file_path, relative_path)
                    included_files.append(str(relative_path))
                except ValueError as e:
                    if 'ZIP does not support timestamps before 1980' in str(e):
                        # Create ZipInfo with current timestamp
                        import time
                        zi = zipfile.ZipInfo(str(relative_path))
                        zi.date_time = time.localtime()[:6]
                        with open(file_path, 'rb') as f:
                            zipf.writestr(zi, f.read(), zipfile.ZIP_DEFLATED)
                        included_files.append(str(relative_path))
                    else:
                        raise

    # Print summary
    print(f"\n[+] Included {len(included_files)} files:")
    for f in sorted(included_files)[:10]:  # Show first 10
        print(f"   + {f}")
    if len(included_files) > 10:
        print(f"   ... and {len(included_files) - 10} more")

    print(f"\n[-] Excluded {len(excluded_files)} files:")
    for f in sorted(excluded_files)[:10]:  # Show first 10
        print(f"   - {f}")
    if len(excluded_files) > 10:
        print(f"   ... and {len(excluded_files) - 10} more")

    zip_size = zip_path.stat().st_size / 1024  # KB
    print(f"\n[*] Package created: {zip_name} ({zip_size:.1f} KB)")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Upload this ZIP to PythonAnywhere")
    print("2. Follow instructions in DEPLOYMENT.md")
    print(f"\nZIP location: {zip_path}")

if __name__ == '__main__':
    create_deployment_zip()
