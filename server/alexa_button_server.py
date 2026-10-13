"""
Alexa Button Box server - runs on the always-on home PC.

The ESP8266 button box sends a plain HTTP request here for each press:
    /plug/on   /plug/off   /plug/cycle   /lights/on   /lights/off   /status
The plug (Feit / Tuya) is switched locally with tinytuya - no cloud, no Alexa.
The lights (Alexa-only) are switched by opening a virtualsmarthome.xyz trigger URL,
which runs an Alexa routine.

Setup:  pip install tinytuya
        copy config.example.json to config.json and fill it in
        python alexa_button_server.py
"""
import json
import logging
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import tinytuya

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "config.json").read_text(encoding="utf-8"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout),
              logging.FileHandler(HERE / "button_server.log", encoding="utf-8")],
)
log = logging.getLogger("buttons")

PLUG = CFG["plug"]
CYCLE_SECONDS = float(CFG.get("cycle_seconds", 10))
TOKEN = CFG.get("token", "")

plug_lock = threading.Lock()
cycle_cancel = threading.Event()
cycle_thread = None


def plug_device():
    d = tinytuya.OutletDevice(
        dev_id=PLUG["id"],
        address=PLUG.get("ip") or "Auto",
        local_key=PLUG["local_key"],
        version=float(PLUG.get("version", 3.3)),
    )
    d.set_socketTimeout(4)
    d.set_socketRetryLimit(2)
    return d


def plug_set(on: bool):
    """Switch the plug; returns (ok, detail)."""
    with plug_lock:
        last = ""
        for attempt in (1, 2):
            try:
                d = plug_device()
                result = d.turn_on() if on else d.turn_off()
                if isinstance(result, dict) and "Error" in result:
                    raise RuntimeError(result.get("Error"))
                return True, "on" if on else "off"
            except Exception as e:  # network blip, plug rebooting, etc.
                last = str(e)
                log.warning("plug %s attempt %d failed: %s", "on" if on else "off", attempt, e)
                time.sleep(0.5)
        return False, f"plug error: {last}"


def plug_status():
    with plug_lock:
        try:
            st = plug_device().status()
            return st.get("dps", st)
        except Exception as e:
            return {"error": str(e)}


def run_cycle():
    ok, _ = plug_set(False)
    if not ok:
        log.error("power-cycle: could not turn plug off")
        return
    log.info("power-cycle: off, waiting %.0f s", CYCLE_SECONDS)
    if cycle_cancel.wait(CYCLE_SECONDS):
        log.info("power-cycle: cancelled by another button")
        return
    ok, _ = plug_set(True)
    log.info("power-cycle: back on" if ok else "power-cycle: could not turn plug back on")


def cancel_cycle():
    cycle_cancel.set()


def start_cycle():
    global cycle_thread
    if cycle_thread and cycle_thread.is_alive():
        return True, "cycle already running"
    cycle_cancel.clear()
    cycle_thread = threading.Thread(target=run_cycle, daemon=True)
    cycle_thread.start()
    return True, "cycling"


def lights(which: str):
    url = CFG.get("lights", {}).get(which, "")
    if not url or "PASTE" in url:
        return False, f"no trigger URL set for lights {which}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "alexa-button-box"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return 200 <= r.status < 400, f"lights {which} (HTTP {r.status})"
    except Exception as e:
        return False, f"lights {which} failed: {e}"


ROUTES = {
    "/plug/on": lambda: (cancel_cycle(), plug_set(True))[1],
    "/plug/off": lambda: (cancel_cycle(), plug_set(False))[1],
    "/plug/cycle": start_cycle,
    "/lights/on": lambda: lights("on"),
    "/lights/off": lambda: lights("off"),
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        token = parse_qs(u.query).get("token", [""])[0]
        if TOKEN and token != TOKEN:
            log.warning("rejected %s from %s (bad token)", u.path, self.client_address[0])
            return self._send(403, {"ok": False, "error": "bad token"})
        if u.path == "/status":
            return self._send(200, {"ok": True, "plug": plug_status()})
        action = ROUTES.get(u.path)
        if not action:
            return self._send(404, {"ok": False, "error": "unknown path", "paths": list(ROUTES) + ["/status"]})
        ok, detail = action()
        log.info("%-12s from %-15s -> %s", u.path, self.client_address[0], detail)
        self._send(200 if ok else 502, {"ok": ok, "detail": detail})

    def log_message(self, *args):  # silence default per-request logging
        pass


if __name__ == "__main__":
    port = int(CFG.get("port", 8765))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    log.info("Alexa Button Box server listening on port %d", port)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
