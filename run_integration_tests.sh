#!/bin/bash
# Integration test runner for RustCoder Python to Rust conversion

set -e

echo "================================================"
echo "RustCoder Integration Tests"
echo "================================================"
echo ""

# Check if backend is running
echo "Checking if RustCoder backend is available..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✓ Backend is running"
else
    echo "✗ Backend is not running"
    echo ""
    echo "Please start the backend first:"
    echo "  docker-compose up"
    echo ""
    exit 1
fi

echo ""
echo "Running integration tests..."
echo ""

# Run the test script
python tests/integration/test_conversions.py

echo ""
echo "Tests complete!"

