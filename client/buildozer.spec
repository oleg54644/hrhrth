[app]
title           = VoIP Phone
package.name    = voipphone
package.domain  = org.voipphone
source.dir      = .
source.include_exts = py,json,png,jpg,atlas
version         = 1.0.0

requirements = python3,kivy==2.3.1,websocket-client==1.6.1,certifi,requests,pyjnius,android

orientation = portrait

android.permissions = INTERNET,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS,\
    WAKE_LOCK,FOREGROUND_SERVICE,VIBRATE,RECEIVE_BOOT_COMPLETED

android.api     = 33
android.minapi  = 24
android.ndk     = 25b
android.ndk_api = 24
android.archs   = arm64-v8a, armeabi-v7a

# Foreground service — приём звонков в фоне
android.service = VoIPKeepAlive:utils/bg_service.py:foreground

p4a.branch = master

[buildozer]
log_level    = 2
warn_on_root = 1

