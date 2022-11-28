from fastapi.testclient import TestClient
from modules.app import ResponseTranslation, RequestTranslation, app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"output": "Hello"}

def test_input_model():
    payload = {
            "payload": {
                "fromLang": "string",
                "records": [
                    {
                        "id": "string",
                        "text": "string"
                    }],
                "toLang": "string"
                }
            }
    request = RequestTranslation(**payload)
    
    assert request
    assert request.payload.dict() == payload["payload"]
    assert request.payload.fromLang == payload["payload"]["fromLang"]
    assert request.payload.toLang == payload["payload"]["toLang"]
    assert request.payload.records == payload["payload"]["records"]

def test_output_model():
    payload = {"result": [{"id": "string", "text": "string"}]}

    response = ResponseTranslation(**payload)

    assert response
    assert response.dict() == payload
    assert response.result == payload["result"]

def test_inference():
    payload = {
            "payload": {
                "fromLang": "en",
                "records": [
                    {
                        "id": "123",
                        "text": "Clean yourself."
                        }
                    ],
                "toLang": "fi"
                }
            }
    response = client.post("/translation", json=payload)

    assert response.status_code == 200
    assert response.json() == { "result": 
                               [
                                   {
                                       "id": "123",
                                       "text": "Puhdista itsesi.",
                                    }
                                ]
                               }
