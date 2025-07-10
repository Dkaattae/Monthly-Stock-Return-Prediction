import requests, json

with open("json_records.json") as f:
    data = json.load(f)

resp = requests.post("http://localhost:9696/predict", json=data)
print(resp.json())