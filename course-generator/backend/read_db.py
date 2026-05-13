import sqlite3, json
conn = sqlite3.connect('courses.db')
c = conn.cursor()
c.execute('SELECT id, generated_json FROM courses ORDER BY created_at DESC LIMIT 1')
r = c.fetchone()
print('row:', bool(r))
if r:
    print('id', r[0])
    gj = r[1]
    try:
        j = json.loads(gj)
        print('module1 visual:', j.get('modules', [])[0].get('visual_aid')[:120])
    except Exception as e:
        print('err parse', e)
        print(gj[:400])
conn.close()
