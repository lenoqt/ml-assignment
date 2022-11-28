from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from .inference import infer_m2m100

app = FastAPI()

class Record(BaseModel):
    id: str
    text: str


class Payload(BaseModel):
    fromLang: str
    records: List[Record]
    toLang: str


class RequestTranslation(BaseModel):
    payload: Payload

class ResponseTranslation(BaseModel):
    result: List[Record]


@app.get("/")
def index():
    return {"output": "Hello"}

@app.post("/translation", response_model=ResponseTranslation)
def m2m_100(input: RequestTranslation):
    payload = input.payload.dict()
    target_lang = payload["toLang"]
    records = payload["records"]
    for record in records:
        record["text"] = infer_m2m100(record["text"], target_lang)[0]
    return {"result": records}
