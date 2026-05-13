import requests
import json

url = "http://127.0.0.1:8005/generate-course"

def test_config(skill, style):
    payload = {
        "topic": "Python",
        "skill_level": skill,
        "hours_per_week": 10,
        "learning_style": style,
        "goal": "Professional development"
    }
    print(f"\n--- Testing: {skill}, {style} ---")
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        if response.status_code == 200:
            print(f"Status: {data.get('status')}")
            print(f"Is Fallback: {data.get('is_fallback')}")
            print(f"Title: {data.get('course', {}).get('course_title')}")
            modules = data.get('course', {}).get('modules', [])
            if modules:
                print(f"Module 1 Title: {modules[0]['title']}")
                print(f"Module 1 Topics: {modules[0]['topics'][:2]}")
        else:
            print(f"Error: {response.status_code} - {data}")
    except Exception as e:
        print(f"Exception: {e}")

test_config("beginner", "hands-on")
test_config("advanced", "theoretical")
