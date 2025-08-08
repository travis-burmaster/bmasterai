#!/bin/bash
# Script to run the cost monitoring example with correct environment

# Set the Python path to include the project root
export PYTHONPATH="../.."

# Use the virtual environment's Python directly
../../venv/bin/python cost_otel_agno.py