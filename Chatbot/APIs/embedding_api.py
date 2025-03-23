from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
app = FastAPI()

model = SentenceTransformer("all-MiniLM-L12-v2")
# to ensure that the request includes text,and improve type checking
class TextRequest(BaseModel):
    text: str
@app.post("/embedding")
def get_embedding(request: TextRequest):
    embedding =  model.encode(request.text).tolist()
    return {"embedding": embedding}
