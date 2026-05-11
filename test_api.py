import requests

url = "http://127.0.0.1:5000/add"

data = {
    "date": "2026-05-08",
    "inflow": 120,
    "outflow": 100,
    "evaporation": 5,
    "waste": 10
}

response = requests.post(url, json=data)

print(response.json())