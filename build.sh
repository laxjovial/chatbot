#!/usr/bin/env bash
pip install -r requirements.txt
python -m spacy download en_core_web_trf
python -m spacy download xx_ent_wiki_sm
