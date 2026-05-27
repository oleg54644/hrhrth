"""
VoIP Server — Python WebSocket + REST
Выдаёт каждому пользователю уникальный номер вида 100-999-XXXX
Маршрутизирует звонки между клиентами через WebSocket
"""

import asyncio
import json
import random
import string
import hashlib
import uuid
import time
from aiohttp import web
import aiohttp

# ── База данных в памяти (для продакшена замени на SQLite/PostgreSQL) ──────
users   = {}   # {username: {password_hash, number, token}}
numbers = {}   # {number: username}
tokens  = {}   # {token: username}
sockets = {}   # {username: WebSocket}  — активные подключения


def gen_number():
    """Генерирует уникальный 7-значный номер вида 100-XXXX"""
    while True:
        n = f"1{random.randint(0,9)}{random.randint(0,9)}-{random.randint(1000,9999)}"
        if n not in numbers:
            return n


def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


def new_token() -> str:
    return str(uuid.uuid4())


# ═══════════════════════════════════════════════════════════════════════════
#  REST API
# ═══════════════════════════════════════════════════════════════════════════

async def api_register(request):
    try:
        data = await request.json()
        username = data.get('username', '').strip().lower()
        password = data.get('password', '').strip()
    except Exception:
        return web.json_response({'ok': False, 'error': 'bad_json'}, status=400)

    if not username or not password:
        return web.json_response({'ok': False, 'error': 'Заполните все поля'}, status=400)
    if len(username) < 3:
        return web.json_response({'ok': False, 'error': 'Логин минимум 3 символа'}, status=400)
    if len(password) < 4:
        return web.json_response({'ok': False, 'error': 'Пароль минимум 4 символа'}, status=400)
    if username in users:
        return web.json_response({'ok': False, 'error': 'Логин уже занят'}, status=409)

    number = gen_number()
    token  = new_token()

    users[username] = {
        'password_hash': hash_password(password),
        'number': number,
        'token': token,
        'registered_at': time.time(),
    }
    numbers[number]  = username
    tokens[token]    = username

    return web.json_response({
        'ok': True,
        'username': username,
        'number': number,
        'token': token,
    })


async def api_login(request):
    try:
        data = await request.json()
        username = data.get('username', '').strip().lower()
        password = data.get('password', '').strip()
    except Exception:
        return web.json_response({'ok': False, 'error': 'bad_json'}, status=400)

    user = users.get(username)
    if not user or user['password_hash'] != hash_password(password):
        return web.json_response({'ok': False, 'error': 'Неверный логин или пароль'}, status=401)

    token = new_token()
    user['token'] = token
    tokens[token] = username

    return web.json_response({
        'ok': True,
        'username': username,
        'number': user['number'],
        'token': token,
    })


async def api_whoami(request):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    username = tokens.get(token)
    if not username:
        return web.json_response({'ok': False, 'error': 'not_authorized'}, status=401)
    return web.json_response({
        'ok': True,
        'username': username,
        'number': users[username]['number'],
        'online': username in sockets,
    })


async def api_resolve(request):
    """Найти пользователя по номеру"""
    number = request.match_info.get('number', '')
    username = numbers.get(number)
    if not username:
        return web.json_response({'ok': False, 'error': 'Номер не найден'}, status=404)
    return web.json_response({'ok': True, 'username': username,
                              'online': username in sockets})


# ═══════════════════════════════════════════════════════════════════════════
#  WebSocket — сигнальный сервер для звонков
# ═══════════════════════════════════════════════════════════════════════════

async def ws_handler(request):
    token = request.rel_url.query.get('token', '')
    username = tokens.get(token)
    if not username:
        return web.Response(status=401, text='Unauthorized')

    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    sockets[username] = ws
    print(f'[WS] {username} подключился')

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                await handle_ws_message(username, msg.data)
            elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                break
    finally:
        sockets.pop(username, None)
        print(f'[WS] {username} отключился')

    return ws


async def handle_ws_message(sender: str, raw: str):
    try:
        msg = json.loads(raw)
    except Exception:
        return

    kind = msg.get('type')

    # ── Звонок ────────────────────────────────────────────────────────────
    if kind == 'call':
        target_number = msg.get('to')
        target_user   = numbers.get(target_number)

        if not target_user:
            await send(sender, {'type': 'error', 'code': 'not_found',
                                'message': f'Номер {target_number} не найден'})
            return

        if target_user not in sockets:
            await send(sender, {'type': 'error', 'code': 'offline',
                                'message': 'Абонент недоступен'})
            return

        # Переслать входящий звонок адресату
        await send(target_user, {
            'type': 'incoming_call',
            'from': users[sender]['number'],
            'from_user': sender,
            'call_id': msg.get('call_id', str(uuid.uuid4())),
        })

        # Подтвердить отправителю — звонок отправлен
        await send(sender, {'type': 'calling',
                            'to': target_number,
                            'call_id': msg.get('call_id')})

    # ── Принять ───────────────────────────────────────────────────────────
    elif kind == 'answer':
        caller_user = msg.get('caller_user')
        if caller_user in sockets:
            await send(caller_user, {'type': 'answered',
                                     'call_id': msg.get('call_id')})

    # ── Отклонить / завершить ─────────────────────────────────────────────
    elif kind in ('reject', 'hangup'):
        other = msg.get('other_user')
        if other in sockets:
            await send(other, {'type': 'hangup',
                                'call_id': msg.get('call_id')})

    # ── WebRTC сигналинг (offer / answer / ICE) ───────────────────────────
    elif kind in ('offer', 'answer', 'ice'):
        target_user = msg.get('to_user')
        if target_user in sockets:
            msg['from_user'] = sender
            await send(target_user, msg)

    # ── Сообщение в чат ───────────────────────────────────────────────────
    elif kind == 'chat':
        target_number = msg.get('to')
        target_user   = numbers.get(target_number)
        if target_user and target_user in sockets:
            await send(target_user, {
                'type': 'chat',
                'from': users[sender]['number'],
                'from_user': sender,
                'text': msg.get('text', ''),
                'ts': time.time(),
            })


async def send(username: str, data: dict):
    ws = sockets.get(username)
    if ws and not ws.closed:
        await ws.send_str(json.dumps(data))


# ═══════════════════════════════════════════════════════════════════════════
#  Запуск
# ═══════════════════════════════════════════════════════════════════════════

def create_app():
    app = web.Application()
    app.router.add_post('/api/register',       api_register)
    app.router.add_post('/api/login',          api_login)
    app.router.add_get ('/api/me',             api_whoami)
    app.router.add_get ('/api/resolve/{number}', api_resolve)
    app.router.add_get ('/ws',                 ws_handler)
    # Health check
    app.router.add_get('/', lambda r: web.Response(text='VoIP Server OK'))
    return app


if __name__ == '__main__':
    print('=== VoIP Server запущен на http://0.0.0.0:8080 ===')
    web.run_app(create_app(), host='0.0.0.0', port=8080)
