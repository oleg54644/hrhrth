"""Sync HTTP wrappers (called from threads, not main loop)"""

import urllib.request, urllib.error, json

class APIClient:
    def __init__(self, storage):
        self.storage = storage

    def _base(self):
        return self.storage.get_server().rstrip('/')

    def _post(self, path, data, token=None):
        url = self._base() + path
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read()), None
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read())
                return None, err.get('error', str(e))
            except:
                return None, str(e)
        except Exception as e:
            return None, str(e)

    def _get(self, path, token=None):
        url = self._base() + path
        req = urllib.request.Request(url)
        if token:
            req.add_header('Authorization', f'Bearer {token}')
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read()), None
        except Exception as e:
            return None, str(e)

    def register(self, username, password):
        return self._post('/api/register', {'username': username, 'password': password})

    def login(self, username, password):
        return self._post('/api/login', {'username': username, 'password': password})

    def me(self, token):
        return self._get('/api/me', token=token)

    def resolve(self, number, token):
        return self._get(f'/api/resolve/{number}', token=token)
