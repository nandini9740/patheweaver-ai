import requests
p={'topic':'python','skill_level':'beginner','hours_per_week':5,'learning_style':'visual','goal':'learn concepts visually'}
try:
    r=requests.post('http://127.0.0.1:8005/generate-course', json=p, timeout=10)
    print(r.status_code)
    print(r.text)
except Exception as e:
    print('Error', e)
