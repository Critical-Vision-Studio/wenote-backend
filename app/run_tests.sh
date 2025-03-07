#!/usr/bin/env bash

# Exit on any error, undefined variables, and pipeline failures
set -euo pipefail

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
    rm -rf .coverage htmlcov .pytest_cache tests/__pycache__ tests/*/__pycache__
fi

# Create necessary directories and files
echo "Creating necessary directories and files..."
mkdir -p logs
touch logs/logs.txt

# Create test environment file
echo "Creating test environment file..."
cat > ../.env << EOL
DEBUG=true
REPO_PATH=/tmp/test-repo
MAIN_BRANCH=master
EOL

# Setup virtual environment path (in parent directory)
VENV_DIR="../.venv"

# Activate virtual environment
echo "Activating virtual environment from parent directory..."
source "${VENV_DIR}/bin/activate"

# Set up testing environment using modern Flask configuration
export FLASK_DEBUG=1
export FLASK_TESTING=1
export PYTHONPATH=$(dirname $(pwd))

# Set temporary Git configuration via environment variables
export GIT_AUTHOR_NAME="Test Runner"
export GIT_AUTHOR_EMAIL="test@example.com"
export GIT_COMMITTER_NAME="Test Runner"
export GIT_COMMITTER_EMAIL="test@example.com"

# Base pytest command - note we're in app directory already
PYTEST_CMD="pytest $VERBOSE $PARALLEL $TEST_FILTER --cov=. --cov-report=term $HTML_REPORT"

# Run tests based on group or specific file
echo "Running tests with coverage..."

if [ -n "$SPECIFIC_FILE" ]; then
    # Run specific test file
    $PYTEST_CMD "$SPECIFIC_FILE"
else
    case "$TEST_GROUP" in
        "unit")
            echo "Running unit tests..."
            $PYTEST_CMD tests/unit/
            ;;
        "integration")
            echo "Running integration tests..."
            $PYTEST_CMD tests/integration/
            ;;
        "fast")
            echo "Running only the mocked tests for speed..."
            $PYTEST_CMD tests/unit/test_routes.py
            ;;
        "security")
            echo "Running only security tests..."
            $PYTEST_CMD tests/unit/test_security.py
            ;;
        "performance")
            echo "Running performance tests..."
            $PYTEST_CMD tests/integration/test_performance.py
            ;;
        *)
            # All tests with coverage
            $PYTEST_CMD tests/
            ;;
    esac
fi

echo "Tests completed successfully!"

# Show coverage report location if HTML report was generated
if [ -n "$HTML_REPORT" ]; then
    echo "HTML coverage report generated in htmlcov/index.html"
fi

# Deactivate virtual environment
deactivate 