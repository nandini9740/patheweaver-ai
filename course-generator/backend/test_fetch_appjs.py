import requests
r=requests.get('http://127.0.0.1:8005/app.js')
print(r.status_code)
print(r.text[:800])
