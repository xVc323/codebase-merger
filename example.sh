#!/bin/bash

# Example script demonstrating the use of the codebase merger tool

# Set variables
REPO_URL="https://github.com/tiangolo/fastapi"  # A well-known Python repo as an example
OUTPUT_FILE="fastapi_codebase.md"
EXCLUDE_PATTERNS=("docs/.*" "tests/.*" "\.md$" "\.git/.*")

# Print header
echo "==================================================="
echo "GitHub Codebase Merger - Example Usage"
echo "==================================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 to use this tool."
    exit 1
fi

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Error: Git is not installed. Please install Git to use this tool."
    exit 1
fi

# Run the script with example arguments
echo "Cloning and merging repository: $REPO_URL"
echo "Output file: $OUTPUT_FILE"
echo "Excluding patterns: ${EXCLUDE_PATTERNS[*]}"
echo ""
echo "This may take a few minutes depending on the repository size..."
echo ""

# Build exclude arguments
EXCLUDE_ARGS=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    EXCLUDE_ARGS+=" -e \"$pattern\""
done

# Run the command
python3 codebase_merger.py "$REPO_URL" -o "$OUTPUT_FILE" $EXCLUDE_ARGS

# Check if the command was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "Success! The merged codebase has been saved to: $OUTPUT_FILE"
    echo ""
    echo "File size: $(du -h "$OUTPUT_FILE" | cut -f1)"
    echo "Line count: $(wc -l "$OUTPUT_FILE" | cut -d' ' -f1) lines"
    
    # Show a preview of the file
    echo ""
    echo "Preview of the first 20 lines:"
    echo "---------------------------------------------------"
    head -n 20 "$OUTPUT_FILE"
    echo "---------------------------------------------------"
    echo ""
    echo "To view the entire file, use: less $OUTPUT_FILE"
else
    echo ""
    echo "Error: Something went wrong during the merge process."
    echo "Please check the error messages above."
fi 