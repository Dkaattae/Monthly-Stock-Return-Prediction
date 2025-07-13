import requests
import json

def test_predict_endpoint():
    with open("json_records.json") as f:
        data = json.load(f)

    response = requests.post("http://my-prediction-app:9696/predict", json=data)
    
    assert response.status_code == 200
    prediction_json = response.json()

    assert len(prediction_json) == len(data), f"Prediction length not matching input length"

    for pred in prediction_json:
        assert "predicted_1m_return" in pred, f"Prediction not found"
        assert isinstance(pred["predicted_1m_return"], (int, float)), f"Prediction {pred} is not numeric"

if __name__ == "__main__":
    test_predict_endpoint()