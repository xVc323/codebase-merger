#!/usr/bin/env python3

import argparse
import os
import re
import sys
import tempfile
import subprocess
import mimetypes

# File extensions/types to skip
SKIP_EXTENSIONS = {
    '.exe', '.dll', '.so', '.dylib', '.jar', '.war', '.ear', '.zip', '.tar', '.gz', '.rar',
    '.7z', '.mp3', '.mp4', '.avi', '.mov', '.mkv', '.png', '.jpg', '.jpeg', '.gif', '.bmp', 
    '.tiff', '.ico', '.svg', '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
    '.pyc', '.pyd', '.pyo', '.class'
}

# Directories to skip
SKIP_DIRS = {
    '.git', 'node_modules', 'venv', 'env', '.env', '.venv', '__pycache__', 
    'build', 'dist', 'target', 'out', '.idea', '.vscode', '.DS_Store', 'bin',
    'obj', 'vendor', 'packages', 'bower_components', '.next', '.nuxt'
}

# Default max file size (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


def should_include_file(file_path, max_size=MAX_FILE_SIZE):
    """
    Determine if a file should be included in the merged output
    based on extension, size, and content type.
    """
    # Skip files with excluded extensions
    _, ext = os.path.splitext(file_path)
    if ext.lower() in SKIP_EXTENSIONS:
        return False
    
    # Skip files that are too large
    if os.path.getsize(file_path) > max_size:
        return False
    
    # Try to determine if the file is binary
    try:
        # Check mimetype first
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and not mime_type.startswith(('text/', 'application/json', 'application/xml', 'application/javascript')):
            return False
        
        # Check file content for binary data
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:  # Null bytes usually indicate binary
                return False
            
            # Try to decode as text
            try:
                chunk.decode('utf-8')
            except UnicodeDecodeError:
                return False
        
        return True
    except Exception:
        # If there's any error, skip the file
        return False


def should_include_dir(dir_path, exclude_patterns=None):
    """
    Determine if a directory should be processed.
    Skips common non-code directories and those matching exclude patterns.
    """
    dir_name = os.path.basename(dir_path)
    
    # Skip common non-code directories
    if dir_name in SKIP_DIRS:
        return False
    
    # Skip directories matching exclude patterns
    if exclude_patterns:
        rel_path = os.path.normpath(dir_path)
        for pattern in exclude_patterns:
            if re.search(pattern, rel_path):
                return False
    
    return True


def clone_repo(repo_url, target_dir):
    """
    Clone a GitHub repository to the target directory.
    Returns True if successful, False otherwise.
    """
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", repo_url, target_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return True
    except subprocess.CalledProcessError:
        return False


def process_repository(repo_dir, output_file, max_file_size=MAX_FILE_SIZE, exclude_patterns=None, status_callback=None):
    """
    Process all files in the repository and merge them into a single output file.
    Returns the number of files processed.
    """
    if status_callback is None:
        status_callback = lambda x: None  # No-op function
    
    repo_name = os.path.basename(os.path.normpath(repo_dir))
    file_count = 0
    
    with open(output_file, 'w', encoding='utf-8') as out_file:
        # Write header
        out_file.write(f"# MERGED CODEBASE: {repo_name}\n")
        out_file.write(f"# Generated at: {output_file}\n\n")
        
        for root, dirs, files in os.walk(repo_dir):
            # Filter directories to skip unwanted ones
            dirs[:] = [d for d in dirs if should_include_dir(os.path.join(root, d), exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, repo_dir)
                
                # Skip files that shouldn't be included or match exclude patterns
                if not should_include_file(file_path, max_file_size):
                    continue
                
                if exclude_patterns:
                    skip = False
                    for pattern in exclude_patterns:
                        if re.search(pattern, rel_path):
                            skip = True
                            break
                    if skip:
                        continue
                
                status_callback(f"Processing: {rel_path}")
                
                # Write file header
                out_file.write("=" * 80 + "\n")
                out_file.write(f"FILE: {rel_path}\n")
                out_file.write("=" * 80 + "\n\n")
                
                # Write file content
                try:
                    with open(file_path, 'r', encoding='utf-8') as in_file:
                        out_file.write(in_file.read())
                except UnicodeDecodeError:
                    try:
                        # Try with latin-1 encoding for files that aren't strictly UTF-8
                        with open(file_path, 'r', encoding='latin-1') as in_file:
                            out_file.write(in_file.read())
                    except Exception as e:
                        out_file.write(f"[Error reading file: {str(e)}]\n")
                
                # Add a newline after each file
                out_file.write("\n\n")
                file_count += 1
    
    return file_count


def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(description="Merge an entire GitHub repository into a single file")
    parser.add_argument("repo_url", help="URL of the GitHub repository to clone")
    parser.add_argument("-o", "--output", default="merged_codebase.txt", help="Output file path")
    parser.add_argument("-e", "--exclude", action="append", help="Regex patterns for files to exclude")
    parser.add_argument("-m", "--max-size", type=int, default=5, help="Maximum file size in MB (default: 5MB)")
    
    args = parser.parse_args()
    
    # Convert max size from MB to bytes
    max_size_bytes = args.max_size * 1024 * 1024
    
    # Create a temporary directory for the repository
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Cloning repository: {args.repo_url}")
        if not clone_repo(args.repo_url, temp_dir):
            print("Error: Failed to clone the repository.", file=sys.stderr)
            return 1
        
        print(f"Processing repository...")
        file_count = process_repository(
            temp_dir, 
            args.output, 
            max_file_size=max_size_bytes,
            exclude_patterns=args.exclude,
            status_callback=lambda msg: print(f"  {msg}")
        )
        
        print(f"Done! Processed {file_count} files.")
        print(f"Output written to: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 