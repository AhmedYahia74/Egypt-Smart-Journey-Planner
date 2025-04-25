from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
import numpy as np
app = FastAPI()


model = SentenceTransformer("Camellia-Mohamed/fine-tuned-sbert-for-tourism")
def split_into_chunks(text, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

class TextRequest(BaseModel):
    text: str
@app.post("/embedding")
def get_embedding(request: TextRequest):
    chunks = split_into_chunks(request.text)
    chunk_embeddings = model.encode(chunks)
    final_embedding = np.mean(chunk_embeddings, axis=0)
    return {"embedding": final_embedding.tolist()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)