import requests
import json

url = "http://localhost:8000/generate-course"
payload = {
    "topic": "origami",
    "skill_level": "beginner",
    "hours_per_week": 5,
    "learning_style": "hands-on",
    "goal": "pass exam"
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
