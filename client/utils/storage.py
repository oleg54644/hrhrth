import json, os
from kivy.utils import platform

def _app_dir():
    if platform == 'android':
        from android.storage import app_storage_path
        return app_storage_path()
    return os.path.expanduser('~/.voipphone')

class Storage:
    _FILE = os.path.join(_app_dir(), 'session.json')

    def __init__(self):
        os.makedirs(_app_dir(), exist_ok=True)

    def save(self, data: dict):
        with open(self._FILE, 'w') as f:
            json.dump(data, f)

    def load(self) -> dict:
        try:
            with open(self._FILE) as f:
                return json.load(f)
        except Exception:
            return {}

    def clear(self):
        try: os.remove(self._FILE)
        except: pass

    # convenience
    def get_server(self) -> str:
        return self.load().get('server', 'http://localhost:8080')
