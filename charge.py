import os
import time
import signal
import sys
import atexit
import requests
import urllib3
from requests import Session

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_original_send = Session.send

def send_without_ssl_verify(self, request, **kwargs):
    kwargs["verify"] = False
    return _original_send(self, request, **kwargs)

Session.send = send_without_ssl_verify

from wyze_sdk import Client

client = Client(
    email=os.environ["WYZE_EMAIL"],
    password=os.environ["WYZE_PASSWORD"],
    api_key=os.environ["WYZE_API_KEY"],
    key_id=os.environ["WYZE_KEY_ID"]
)

PLUG_MAC = "80482CA70E12"
PLUG_MODEL = "WLPP1CFH"

def turn_on():
    client.plugs.turn_on(device_mac=PLUG_MAC, device_model=PLUG_MODEL)
    print("Plug ON", flush=True)

def turn_off():
    client.plugs.turn_off(device_mac=PLUG_MAC, device_model=PLUG_MODEL)
    print("Plug OFF", flush=True)

def safe_turn_off():
    try:
        turn_off()
    except Exception as err:
        print(f"Failed to turn plug off safely: {err}", flush=True)

def handle_shutdown(signum, frame):
    print("Shutdown/cancel detected. Turning plug OFF before exiting...", flush=True)
    safe_turn_off()
    sys.exit(1)

atexit.register(safe_turn_off)
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

action = os.environ.get("ACTION", "charge").lower()

if action == "off":
    print("Emergency OFF action requested.", flush=True)
    safe_turn_off()
    sys.exit(0)

hours = float(os.environ["HOURS"])
heat_breaks = os.environ["HEAT_BREAKS"].lower() == "true"
charge_block_minutes = float(os.environ.get("CHARGE_BLOCK_MINUTES", "15"))
cooldown_minutes = float(os.environ.get("COOLDOWN_MINUTES", "2"))
total_minutes = hours * 60

if charge_block_minutes <= 0:
    charge_block_minutes = 15

if cooldown_minutes < 0:
    cooldown_minutes = 0

print(f"Charge target: {hours} hours", flush=True)
print(f"Heat breaks: {heat_breaks}", flush=True)
print(f"Charge block: {charge_block_minutes} min", flush=True)
print(f"Cooldown: {cooldown_minutes} min", flush=True)

if not heat_breaks:
    turn_on()
    time.sleep(total_minutes * 60)
    turn_off()
else:
    remaining_minutes = total_minutes
    cycle = 1

    while remaining_minutes > 0:
        this_block = min(charge_block_minutes, remaining_minutes)

        print(f"Cycle {cycle}: charging for {this_block:.1f} min", flush=True)
        turn_on()
        time.sleep(this_block * 60)
        turn_off()

        remaining_minutes -= this_block

        if remaining_minutes > 0 and cooldown_minutes > 0:
            print(f"Cooldown break ({cooldown_minutes:.1f} min)...", flush=True)
            time.sleep(cooldown_minutes * 60)

        cycle += 1

print("Charging complete.", flush=True)
