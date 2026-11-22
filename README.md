# OnCamino app

The OnCamino phone app: the live Camino Francés map from theslowluxurylife.com in app mode, with native GPS so tracking keeps going while the phone is locked.

- Opens `https://theslowluxurylife.com/live-camino-francais-map/?app=1` (the site's app layout).
- The site loads `native.js` (OnCamino Map plugin, oncamino-app part) only inside this app; it routes the map's location requests to the phone's background GPS.
- `www/index.html` is shown only if the very first launch has no connection.
- Route data for the app: `https://theslowluxurylife.com/wp-json/oncamino/v1/route`.

Builds: every push to `main` builds the Android test version (GitHub Actions) and publishes it under Releases → "OnCamino test version (Android)". The iPhone build needs an Apple developer account (to sign it) and runs on GitHub's Mac machines.
