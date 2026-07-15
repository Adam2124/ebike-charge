import os
import time
import requests
from requests import Session
_orig_request = Session.request
Session.request = lambda self, *a, **kw: _orig_request(self, *a, **{**kw, "verify": False})
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
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

hours = float(os.environ["HOURS"])
heat_breaks = os.environ["HEAT_BREAKS"].lower() == "true"
total_minutes = hours * 60

if not heat_breaks:
    turn_on()
    time.sleep(total_minutes * 60)
    turn_off()
else:
    cycles = int(total_minutes // 15)
    for i in range(cycles):
        print(f"Cycle {i + 1} of {cycles}", flush=True)
        turn_on()
        time.sleep(15 * 60)
        turn_off()
        if i < cycles - 1:
            print("Heat break (2 min)...", flush=True)
            time.sleep(2 * 60)

print("Charging complete.", flush=True)
