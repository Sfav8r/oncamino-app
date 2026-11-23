#!/bin/bash
# Background tracking check on the emulator (see bgtest.py)
adb install -r OnCamino-test.apk
adb shell pm grant app.oncamino android.permission.ACCESS_FINE_LOCATION || true
adb shell pm grant app.oncamino android.permission.ACCESS_COARSE_LOCATION || true
adb shell pm grant app.oncamino android.permission.POST_NOTIFICATIONS || true
adb shell settings put global window_animation_scale 0
adb shell am start -n app.oncamino/.MainActivity
sleep 45
pip install --quiet websocket-client || pip3 install --quiet --break-system-packages websocket-client
python3 scripts/bgtest.py 2>&1 | tee bg-log.txt
adb logcat -d | grep -iE "BackgroundGeolocation|Capacitor|ForegroundService|AndroidRuntime" | tail -300 > bg-logcat.txt || true
