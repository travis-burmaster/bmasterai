#!/bin/bash
# Script to run the Agno telemetry example with correct environment

# Set the Python path to include the project root
export PYTHONPATH="../.."

# Use the virtual environment's Python directly
../../venv/bin/python gemini_agno_example.py