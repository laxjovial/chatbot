#!/bin/bash

# Optional: remove NLTK data if not needed anymore
rm -rf nltk_data

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
