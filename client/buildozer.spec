[app]
title = VoIP Phone
package.name = voipphone
package.domain = org.voipphone

source.dir = .
source.include_exts = py,png,jpg,json,atlas

version = 1.0.0

requirements = python3,kivy==2.3.0,websocket-client,certifi,requests,pyjnius,android

orientation = portrait

# Разрешения
android.permissions = INTERNET, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS, WAKE_LOCK, FOREGROUND_SERVICE, VIBRATE, RECEIVE_BOOT_COMPLETED

# Версии API и NDK
android.api = 33
android.minapi = 24
android.ndk = 25b
android.ndk_api = 24
android.archs = arm64-v8a, armeabi-v7a

# КЛЮЧЕВАЯ СТРОКА ДЛЯ ЛИЦЕНЗИЙ
android.accept_sdk_license = True

# Фиксируем версию build-tools, чтобы не лезть в 37
android.sdk_build_tools = 34.0.0

# Отключаем автоматическое обновление SDK (чтобы не качал лишнего)
android.update_sdk = False

# Если нет фонового сервиса — закомментируйте или удалите
android.service = VoIPKeepAlive:utils/bg_service.py:foreground

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1
