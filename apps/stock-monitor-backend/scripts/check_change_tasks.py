#!/usr/bin/env python3
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
tasks = r.get('okooo:repair_tasks')
if tasks:
    data = json.loads(tasks)
    # Find tasks with mobile_change
    change_tasks = [t for t in data if t['page_type'] == 'mobile_change']
    print(f'Tasks with mobile_change: {len(change_tasks)}')
    for t in change_tasks[:3]:
        print(json.dumps(t, indent=2, ensure_ascii=False))
