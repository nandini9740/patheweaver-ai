import requests
url = "http://localhost:8001/generate-course"
payload = {
    "topic": "origami",
    "skill_level": "beginner",
    "hours_per_week": 5,
    "learning_style": "hands-on",
    "goal": "pass exam"
}
response = requests.post(url, json=payload)
data = response.json()
print("Keys in response:", data.keys())
if 'is_fallback' in data:
    print("is_fallback:", data['is_fallback'])
else:
    print("is_fallback NOT FOUND in response")
