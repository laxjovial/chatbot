from fastapi import FastAPI
from pydantic import BaseModel
import spacy

app = FastAPI()

nlp_en = spacy.load("en_core_web_trf")
nlp_multi = spacy.load("xx_ent_wiki_sm")

class TextPayload(BaseModel):
    text: str

@app.post("/extract_entities")
def extract_entities(payload: TextPayload):
    text = payload.text
    # Simple heuristic: use English model if text mostly English, else multilingual
    # For demo, always use English model (customize as needed)
    doc = nlp_en(text)
    if not doc.ents:
        doc = nlp_multi(text)
    entities = [ent.text for ent in doc.ents]
    return {"entities": entities}
