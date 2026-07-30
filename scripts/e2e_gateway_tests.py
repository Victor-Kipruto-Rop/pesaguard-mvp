#!/usr/bin/env python3
import json
import urllib.request
import urllib.error

API_KEY = 'test-api-key'
ENDPOINTS = [
    ('GET', 'http://127.0.0.1:8000/live', None, False),
    ('GET', 'http://127.0.0.1:8000/health', None, False),
    ('POST', 'http://127.0.0.1:8000/api/v1/auth/login', {'username':'test','password':'x'}, False),
    ('POST', 'http://127.0.0.1:8000/api/v1/payments', {'amount':100,'currency':'KES'}, True),
    ('GET', 'http://127.0.0.1:8000/api/v1/transactions', None, True),
    ('GET', 'http://127.0.0.1:8000/api/v1/reports', None, True),
    ('POST', 'http://127.0.0.1:8000/api/v1/audit', {'event':'test'}, True)
]


def call(method, url, body, auth_required=False):
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode()
        headers['Content-Type'] = 'application/json'
    if auth_required:
        headers['x-api-key'] = API_KEY
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return (r.status, r.read().decode())
    except urllib.error.HTTPError as e:
        return (e.code, e.read().decode())
    except Exception as e:
        return (None, str(e))


if __name__ == '__main__':
    results = []
    for method, url, body, auth_required in ENDPOINTS:
        status, body = call(method, url, body, auth_required)
        print(f"{method} {url} (auth={auth_required}) -> {status}\n{body}\n---")
