"""
Foreground Service — держит WebSocket открытым в фоне.
Зарегистрирован в buildozer.spec как android.service.
"""
import json, os, time, threading, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kivy.utils import platform

def _app_dir():
    if platform == 'android':
        from android.storage import app_storage_path
        return app_storage_path()
    return os.path.expanduser('~/.voipphone')


def main():
    session_file = os.path.join(_app_dir(), 'session.json')
    if not os.path.exists(session_file):
        return

    with open(session_file) as f:
        data = json.load(f)

    token  = data.get('token')
    server = data.get('server', 'http://localhost:8080')

    if not token:
        return

    try:
        import websocket

        ws_url = server.replace('http://', 'ws://').replace('https://', 'wss://')
        url    = f'{ws_url}/ws?token={token}'

        def on_message(ws, raw):
            try:
                msg = json.loads(raw)
                if msg.get('type') == 'incoming_call':
                    # Показать Android уведомление
                    _notify_incoming(msg.get('from', '???'))
            except:
                pass

        def _run():
            while True:
                try:
                    ws = websocket.WebSocketApp(url, on_message=on_message)
                    ws.run_forever(ping_interval=25)
                except Exception as e:
                    print(f'[BG] WS error: {e}')
                time.sleep(5)

        threading.Thread(target=_run, daemon=True).start()

        # Keep service alive
        while True:
            time.sleep(60)

    except ImportError:
        print('[BG] websocket-client not available')


def _notify_incoming(from_number):
    if platform != 'android':
        return
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        NotificationManager = autoclass('android.app.NotificationManager')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        String = autoclass('java.lang.String')

        ctx = PythonActivity.mActivity
        nb  = NotificationBuilder(ctx, 'voip_channel')
        nb.setContentTitle(String('Входящий звонок'))
        nb.setContentText(String(f'Звонит: {from_number}'))
        nb.setSmallIcon(ctx.getApplicationInfo().icon)
        nm = ctx.getSystemService(ctx.NOTIFICATION_SERVICE)
        nm.notify(42, nb.build())
    except Exception as e:
        print(f'[BG] notify error: {e}')


if __name__ == '__main__':
    main()
