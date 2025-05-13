# GitHub Codebase Merger

A simple Python tool that clones a GitHub repository and merges all code files into a single large file with path comments. This is useful for:

- Creating a consolidated view of an entire codebase
- Preparing code for analysis by LLMs
- Generating documentation or code overviews

## Features

- Clones any public GitHub repository
- Intelligently filters out binary files, large files, and common non-code directories
- Adds clear file path headers for each file
- Allows custom exclude patterns using regex
- Configurable maximum file size
- Available as both CLI and GUI applications

## Requirements

- Python 3.6+
- Git command-line tool installed and accessible
- Tkinter (included with most Python installations) for the GUI version

## Installation

### Option 1: Install from PyPI (recommended)

```bash
pip install codebase-merger
```

### Option 2: Clone the repository

```bash
# Clone this repository
git clone https://github.com/yourusername/codebase-merger.git
cd codebase-merger

# Install the package
pip install -e .

# Make the scripts executable (Linux/Mac)
chmod +x codebase_merger.py codebase_merger_gui.py
```

## Usage

### Command Line Interface

```bash
codebase-merger [GITHUB_REPO_URL] [OPTIONS]
```

Or if you've cloned the repository:

```bash
./codebase_merger.py [GITHUB_REPO_URL] [OPTIONS]
```

#### Arguments

- `GITHUB_REPO_URL`: URL of the GitHub repository to clone (required)

#### Options

- `-o, --output`: Output file path (default: merged_codebase.txt)
- `-e, --exclude`: Regex patterns for files to exclude (can specify multiple)
- `-m, --max-size`: Maximum file size in MB (default: 5MB)

#### CLI Examples

Basic usage:
```bash
codebase-merger https://github.com/username/repository
```

Specifying output file:
```bash
codebase-merger https://github.com/username/repository -o merged_code.md
```

Exclude specific files or patterns:
```bash
codebase-merger https://github.com/username/repository -e "\.md$" -e "tests/.*" -e "docs/.*"
```

Set max file size:
```bash
codebase-merger https://github.com/username/repository -m 10
```

### Graphical User Interface

For those who prefer a GUI, simply run:

```bash
codebase-merger-gui
```

Or if you've cloned the repository:

```bash
./codebase_merger_gui.py
```

The GUI provides all the same functionality as the CLI version with a user-friendly interface:

- Enter a GitHub repository URL
- Select output file location
- Set maximum file size
- Add or remove exclusion patterns
- View real-time progress and status updates

## Output Format

The output file will have the following structure:

```
# MERGED CODEBASE: repository-name
# Generated at: output-filename

================================================================================
FILE: path/to/file1.ext
================================================================================

[contents of file1]

================================================================================
FILE: path/to/file2.ext
================================================================================

[contents of file2]

...
```

## Limitations

- Very large repositories might take a long time to process
- Some binary files might be incorrectly identified as text
- Currently does not support private repositories that require authentication

## Development

### Running Tests

```bash
python -m unittest test_codebase_merger.py
```

### Building the Package

```bash
pip install build
python -m build
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT 