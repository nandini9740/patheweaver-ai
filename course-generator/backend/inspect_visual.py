import requests
import json
p={'topic':'python','skill_level':'beginner','hours_per_week':5,'learning_style':'visual','goal':'learn concepts visually'}
r=requests.post('http://127.0.0.1:8005/generate-course', json=p, timeout=10)
print('POST status', r.status_code)
try:
    j=r.json()
    cid=j.get('id')
    print('returned id', cid)
    gr=requests.get(f'http://127.0.0.1:8005/course/{cid}', timeout=10)
    print('GET /course status', gr.status_code)
    data=gr.json()
    modules=data.get('course', {}).get('modules', [])
    for m in modules:
        print('module', m.get('module_number'), 'visual_aid:', m.get('visual_aid')[:120] if m.get('visual_aid') else None)
except Exception as e:
    print('err parsing json', e)
    print(r.text)
