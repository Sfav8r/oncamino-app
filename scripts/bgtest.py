"""Background tracking check on the Android emulator (run by GitHub Actions).
Starts tracking in the app, sends GPS positions along the Camino while the app is in the background
with the screen off, then reports how many positions the map received while hidden."""
import json, subprocess, time, urllib.request, sys
import websocket

def sh(c, check=False):
    r = subprocess.run(c, shell=True, capture_output=True, text=True)
    return (r.stdout or '') + (r.stderr or '')

def cdp():
    for _ in range(30):
        socks = [l.split()[-1].lstrip('@') for l in sh("adb shell cat /proc/net/unix").splitlines() if 'webview_devtools_remote' in l]
        if socks:
            sh("adb forward --remove-all")
            sh("adb forward tcp:9222 localabstract:" + socks[0])
            try:
                pages = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=5))
                pages = [p for p in pages if p.get('type') == 'page']
                if pages:
                    return websocket.create_connection(pages[0]['webSocketDebuggerUrl'], timeout=20, suppress_origin=True)
            except Exception as e:
                print('waiting for WebView', e)
        time.sleep(3)
    raise SystemExit('WebView debugging socket not found')

ws = None; mid = [0]
def ev(js):
    global ws
    for attempt in range(3):
        try:
            if ws is None:
                ws = cdp()
            mid[0] += 1
            ws.send(json.dumps({'id': mid[0], 'method': 'Runtime.evaluate', 'params': {'expression': js, 'returnByValue': True, 'awaitPromise': True}}))
            while True:
                m = json.loads(ws.recv())
                if m.get('id') == mid[0]:
                    return m.get('result', {}).get('result', {}).get('value')
        except Exception as e:
            print('devtools reconnect', e); ws = None; time.sleep(3)
    return None

out = {}
print('page:', ev("location.href"))
ev("(()=>{var w=document.querySelector('#tsll-wel .wl-x');if(w)w.click();[...document.querySelectorAll('button')].filter(b=>b.offsetWidth&&/^Close$/.test(b.innerText.trim())).forEach(b=>b.click());return 1})()")
time.sleep(2)
pts = ev("(()=>{var L=(window.TSLL_M&&TSLL_M.list)?TSLL_M.list():[];var a=L.filter(x=>x.km>=111.5&&x.km<=118&&isFinite(x.la));if(a.length<2){var T=(window.TSLL_TOWNS||[]).filter(t=>t[3]>=105&&t[3]<=130);a=T.map(t=>({la:t[1],lo:t[2],km:t[3]}));}return a.map(x=>[x.la,x.lo,x.km])})()") or []
print('route points', len(pts), pts[:3])
if len(pts) < 2:
    pts = [[42.6626, -2.0220, 111.5], [42.6545, -2.0400, 113.4]]
# interpolate 20 positions between the first and last point
a, b = pts[0], pts[-1]
path = [(a[0] + (b[0] - a[0]) * i / 19.0, a[1] + (b[1] - a[1]) * i / 19.0) for i in range(20)]
def fix(p):
    sh("adb emu geo fix %.6f %.6f" % (p[1], p[0]))
fix(path[0]); time.sleep(2)
print('start:', ev("(()=>{var b=document.getElementById('tsll-track');if(!b)return 'no button';if(!b.classList.contains('on'))b.click();return b.className})()"))
for p in path[:3]:
    fix(p); time.sleep(3)
out['foreground'] = ev("JSON.stringify([window.OC_BG||null,document.getElementById('tsll-track').className,(document.getElementById('tsll-status')||{}).textContent])")
print('foreground', out['foreground'])
sh("adb exec-out screencap -p > bg-1-tracking.png")
# leave the app and switch the screen off
sh("adb shell input keyevent KEYCODE_HOME"); time.sleep(3)
sh("adb shell input keyevent KEYCODE_SLEEP"); time.sleep(3)
t0 = time.time()
for p in path[3:]:
    fix(p); time.sleep(5)
out['service'] = sh("adb shell dumpsys activity services app.oncamino | grep -iE 'ServiceRecord|isForeground|foregroundServiceType' | head -20")
print('service', out['service'])
out['notification'] = sh("adb shell dumpsys notification --noredact | grep -iE 'app.oncamino|recording' | head -10")
# back to the app
sh("adb shell input keyevent KEYCODE_WAKEUP"); time.sleep(2)
sh("adb shell wm dismiss-keyguard"); time.sleep(1)
sh("adb shell am start -n app.oncamino/.MainActivity"); time.sleep(6)
out['after'] = ev("JSON.stringify([window.OC_BG||null,document.getElementById('tsll-track').className])")
print('after', out['after'])
sh("adb exec-out screencap -p > bg-2-back.png")
bg = json.loads(out['after'] or '[null]')[0] or {}
out['result'] = 'PASS' if bg.get('hidden', 0) >= 8 else 'FAIL'
out['detail'] = 'Positions received while the app was in the background with the screen off: %s of %s sent' % (bg.get('hidden', 0), len(path) - 3)
print(out['result'], out['detail'])
open('bg-result.json', 'w').write(json.dumps(out, indent=1))
