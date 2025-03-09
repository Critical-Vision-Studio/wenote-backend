#!/usr/bin/env bash

# Exit on any error, undefined variables, and pipeline failures
set -euo pipefail

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root directory
cd "$PROJECT_ROOT"

# Help message
show_help() {
    echo "Usage: $0 [OPTIONS] [TEST_GROUP]"
    echo
    echo "Test Groups:"
    echo "  all         Run all tests (default)"
    echo "  unit        Run only unit tests"
    echo "  integration Run only integration tests"
    echo "  fast        Run only mocked tests"
    echo "  security    Run only security tests"
    echo "  performance Run only performance tests"
    echo
    echo "Options:"
    echo "  -h, --help       Show this help message"
    echo "  -v, --verbose    Run tests with verbose output"
    echo "  -p, --parallel   Run tests in parallel"
    echo "  -f, --file       Run specific test file"
    echo "  -k, --filter     Filter tests by keyword"
    echo "  --html           Generate HTML coverage report"
    echo "  --clean          Clean up test artifacts before running"
}

# Default values
VERBOSE=""
PARALLEL=""
HTML_REPORT=""
SPECIFIC_FILE=""
TEST_FILTER=""
CLEAN=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE="-v"
            shift
            ;;
        -p|--parallel)
            PARALLEL="-n auto"
            shift
            ;;
        -f|--file)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        -k|--filter)
            TEST_FILTER="-k $2"
            shift 2
            ;;
        --html)
            HTML_REPORT="--cov-report=html"
            shift
            ;;
        --clean)
            CLEAN="yes"
            shift
            ;;
        *)
            TEST_GROUP="$1"
            shift
            ;;
    esac
done

# Default test group if not provided
TEST_GROUP="${TEST_GROUP:-all}"

# Clean up test artifacts if requested
if [ -n "$CLEAN" ]; then
    echo "Cleaning up test artifacts..."
    rm -rf "$SCRIPT_DIR"/.coverage "$SCRIPT_DIR"/htmlcov "$SCRIPT_DIR"/.pytest_cache "$SCRIPT_DIR"/tests/__pycache__ "$SCRIPT_DIR"/tests/*/__pycache__
fi

# Create necessary directories and files
echo "Creating necessary directories and files..."
mkdir -p "$SCRIPT_DIR/logs"
touch "$SCRIPT_DIR/logs/logs.txt"

# Check for .env file
ENV_FILE="$PROJECT_ROOT/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Warning: .env file not found at $ENV_FILE"
    echo "Please create it with the required settings:"
    echo "DEBUG=true"
    echo "REPO_PATH=/path/to/repo"
    echo "MAIN_BRANCH=master"
    exit 1
fi

# Setup virtual environment path
VENV_DIR="$PROJECT_ROOT/.venv"

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    python3 -m venv .venv
    source "$VENV_DIR/bin/activate"
    echo "Installing dependencies..."
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    # Activate virtual environment
    echo "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
fi

# Set up testing environment using modern Flask configuration
export FLASK_DEBUG=1
export FLASK_TESTING=1
export PYTHONPATH="$PROJECT_ROOT"

# Set temporary Git configuration via environment variables
export GIT_AUTHOR_NAME="Test Runner"
export GIT_AUTHOR_EMAIL="test@example.com"
export GIT_COMMITTER_NAME="Test Runner"
export GIT_COMMITTER_EMAIL="test@example.com"

# Base pytest command - now running from project root
PYTEST_CMD="pytest $VERBOSE $PARALLEL $TEST_FILTER --cov=app --cov-report=term $HTML_REPORT"

# Run tests based on group or specific file
echo "Running tests with coverage..."

if [ -n "$SPECIFIC_FILE" ]; then
    # Run specific test file
    eval "$PYTEST_CMD \"$SCRIPT_DIR/$SPECIFIC_FILE\""
else
    case "$TEST_GROUP" in
        "unit")
            echo "Running unit tests..."
            eval "$PYTEST_CMD $SCRIPT_DIR/tests/unit/"
            ;;
        "integration")
            echo "Running integration tests..."
            eval "$PYTEST_CMD $SCRIPT_DIR/tests/integration/"
            ;;
        "fast")
            echo "Running only the mocked tests for speed..."
            eval "$PYTEST_CMD $SCRIPT_DIR/tests/unit/test_routes.py"
            ;;
        "security")
            echo "Running only security tests..."
            eval "$PYTEST_CMD $SCRIPT_DIR/tests/unit/test_security.py"
            ;;
        "performance")
            echo "Running performance tests..."
            eval "$PYTEST_CMD $SCRIPT_DIR/tests/integration/test_performance.py"
            ;;
        *)
            # All tests with coverage
            eval "$PYTEST_CMD $SCRIPT_DIR/tests/"
            ;;
    esac
fi

echo "Tests completed successfully!"

# Show coverage report location if HTML report was generated
if [ -n "$HTML_REPORT" ]; then
    echo "HTML coverage report generated in $SCRIPT_DIR/htmlcov/index.html"
fi

# Deactivate virtual environment
deactivate 