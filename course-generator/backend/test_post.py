import requests
import json

payload={'topic':'python','skill_level':'beginner','hours_per_week':5,'learning_style':'hands-on','goal':'build a simple app'}
try:
    r=requests.post('http://127.0.0.1:8005/generate-course', json=payload, timeout=10)
    print('Status:', r.status_code)
    print('Headers:', r.headers.get('content-type'))
    print('Body:', r.text)
except Exception as e:
    print('Request error:', e)
