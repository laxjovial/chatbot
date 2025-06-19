#!/bin/bash

# Create a local directory for nltk_data
mkdir -p nltk_data

# Download punkt directly to nltk_data folder (no need for separate nltk_setup.py)
python -m nltk.downloader -d nltk_data punkt

# Install all Python dependencies
pip install -r requirements.txt
