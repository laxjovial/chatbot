#!/bin/bash

# Create nltk_data directory
mkdir -p nltk_data

# Run nltk_setup before installing dependencies
python3 nltk_setup.py

# Now install dependencies
pip install -r requirements.txt
