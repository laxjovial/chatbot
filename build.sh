#!/bin/bash
pip install --upgrade pip
# Step 1: Install all required packages
pip install -r requirements.txt

# Step 2: Download spaCy models
python -m spacy download xx_ent_wiki_sm
