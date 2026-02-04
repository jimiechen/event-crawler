#!/usr/bin/env python3
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
tasks = r.get('okooo:repair_tasks')
if tasks:
    data = json.loads(tasks)
    print(f'Total tasks: {len(data)}')
    print(f'First task: {json.dumps(data[0], indent=2, ensure_ascii=False)}')
    # Check unique page_types
    types = set(t['page_type'] for t in data)
    print(f'\nUnique page_types: {types}')
else:
    print('No tasks found')
