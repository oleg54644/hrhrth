# 📞 VoIP Phone

Приложение для звонков через интернет. Свой Python-сервер выдаёт каждому пользователю **уникальный случайный номер** вида `100-4857`.

```
voip2/
├── server/
│   ├── server.py          ← Python WebSocket + REST сервер
│   ├── requirements.txt
│   └── Dockerfile
├── client/
│   ├── main.py
│   ├── buildozer.spec     ← конфиг сборки APK
│   ├── screens/
│   │   ├── login_screen.py
│   │   ├── register_screen.py
│   │   ├── main_screen.py
│   │   ├── call_screen.py
│   │   └── contacts_screen.py
│   └── utils/
│       ├── api_client.py
│       ├── ws_client.py
│       ├── storage.py
│       ├── bg_service.py  ← фоновый сервис Android
│       └── ui.py
└── .github/
    └── workflows/
        └── build.yml      ← GitHub Actions → APK
```

---

## 🖥️ ЧАСТЬ 1 — Запуск сервера

### Вариант А — Локально (для теста)

```bash
cd server
pip install aiohttp
python server.py
# Сервер запустился на http://0.0.0.0:8080
```

### Вариант Б — Бесплатный хостинг на Railway

1. Зайди на **railway.app** → Sign Up (через GitHub)
2. **New Project** → **Deploy from GitHub repo**
3. Выбери свой репозиторий, директорию `server`
4. Railway автоматически найдёт `Dockerfile` и запустит сервер
5. Перейди в **Settings → Networking → Generate Domain**
6. Ты получишь ссылку вида `https://voip-server-xxxx.railway.app`
7. Эту ссылку вводишь в приложение как адрес сервера

### Вариант В — VPS (любой: Timeweb, Beget, Hetzner)

```bash
# Подключись по SSH к своему серверу
ssh user@ВАШ_IP

# Установи Python и зависимости
sudo apt update && sudo apt install -y python3 python3-pip
pip3 install aiohttp

# Скопируй server.py на сервер и запусти
python3 server.py &

# Чтобы работал постоянно — используй screen или systemd:
screen -S voip
python3 server.py
# Ctrl+A, затем D — отсоединиться (сервер продолжает работать)
```

Адрес сервера для клиента: `http://ВАШ_IP:8080`

---

## 📱 ЧАСТЬ 2 — Сборка APK через GitHub Actions

### Шаг 1 — Создай репозиторий на GitHub

1. Зайди на [github.com](https://github.com) → нажми **"+"** → **New repository**
2. Название: `voip-phone`
3. Видимость: **Public**
4. Нажми **Create repository**

### Шаг 2 — Загрузи файлы

**Способ А — через браузер (без git):**
1. В репозитории нажми **"uploading an existing file"**
2. Перетащи все файлы из папки `voip2/`
3. Нажми **Commit changes**

**Способ Б — через командную строку:**
```bash
cd voip2
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/ТВО_ИМЯ/voip-phone.git
git push -u origin main
```

### Шаг 3 — Запусти сборку

1. Перейди в репозиторий → вкладка **Actions**
2. Слева нажми **📱 Build Android APK**
3. Справа нажми **Run workflow** → **Run workflow** (зелёная кнопка)
4. ⏳ Сборка идёт **20–40 минут** (первый раз до 50 мин из-за скачивания SDK)

### Шаг 4 — Скачай APK

1. Когда появится зелёная галочка ✅ — нажми на неё
2. Прокрути вниз до раздела **Artifacts**
3. Нажми **VoIPPhone-debug-apk** — скачается ZIP
4. Распакуй — внутри будет файл `.apk`

### Шаг 5 — Установи на телефон

1. Отправь APK на телефон (через Telegram, кабель, Google Drive)
2. На Android: **Настройки → Безопасность → Разрешить установку из неизвестных источников**
3. Открой APK и установи

---

## 📲 Как пользоваться

1. **Открой приложение**
2. Нажми **"Создать аккаунт"**
3. Введи адрес сервера (напр. `https://voip-server-xxxx.railway.app`)
4. Придумай логин и пароль
5. Тебе выдастся номер, например **`142-7831`**
6. Чтобы позвонить другу — он тоже устанавливает приложение, регистрируется, получает свой номер
7. Набираешь его номер на клавиатуре → 📞

---

## 🔧 API сервера

| Метод | URL | Описание |
|---|---|---|
| POST | `/api/register` | Регистрация → выдаёт номер |
| POST | `/api/login` | Вход → возвращает токен |
| GET | `/api/me` | Инфо о себе |
| GET | `/api/resolve/{number}` | Найти пользователя по номеру |
| WS | `/ws?token=...` | WebSocket для звонков |
