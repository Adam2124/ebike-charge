import os
import time
import hashlib
import uuid
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WYZE_EMAIL = os.environ["WYZE_EMAIL"]
WYZE_PASSWORD = os.environ["WYZE_PASSWORD"]
WYZE_API_KEY = os.environ["WYZE_API_KEY"]
WYZE_KEY_ID = os.environ["WYZE_KEY_ID"]

PLUG_MAC = "80482CA70E12"
PLUG_MODEL = "WLPP1CFH"

def get_token():
    url = "https://auth-prod.api.wyze.com/api/user/login"
    payload = {
        "email": WYZE_EMAIL,
        "password": hashlib.md5(hashlib.md5(WYZE_PASSWORD.encode()).hexdigest().encode()).hexdigest()
    }
    headers = {
        "apikey": WYZE_API_KEY,
        "keyid": WYZE_KEY_ID,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers, verify=False)
    response.raise_for_status()
    data = response.json()
    if "access_token" in data:
        return data["access_token"]
    if "data" in data and "access_token" in data["data"]:
        return data["data"]["access_token"]
    raise RuntimeError(f"Could not find access token in Wyze response: {data}")

def set_plug(token, state):
    url = "https://api.wyzecam.com/app/v2/device/set_property"
    payload = {
        "access_token": token,
        "phone_id": str(uuid.uuid4()),
        "app_ver": "wyze_developer_api",
        "sc": "9f275790cab94a72bd206c8876429f3c",
        "sv": "9d74946e652647e9b6c9d59326aef104",
        "ts": int(time.time() * 1000),
        "device_mac": PLUG_MAC,
        "device_model": PLUG_MODEL,
        "pid": "P3",
        "pvalue": str(state)
    }
    response = requests.post(url, json=payload, verify=False)
    response.raise_for_status()
    return response.json()

def turn_on(token):
    set_plug(token, 1)
    print("Plug ON", flush=True)

def turn_off(token):
    set_plug(token, 0)
    print("Plug OFF", flush=True)

hours = float(os.environ["HOURS"])
heat_breaks = os.environ["HEAT_BREAKS"].lower() == "true"
total_minutes = hours * 60

print("Logging in to Wyze...", flush=True)
token = get_token()
print("Login successful.", flush=True)

if not heat_breaks:
    turn_on(token)
    time.sleep(total_minutes * 60)
    turn_off(token)
else:
    cycles = int(total_minutes // 15)

    if cycles == 0:
        turn_on(token)
        time.sleep(total_minutes * 60)
        turn_off(token)
    else:
        for i in range(cycles):
            print(f"Cycle {i + 1} of {cycles}", flush=True)
            turn_on(token)
            time.sleep(15 * 60)
            turn_off(token)
            if i < cycles - 1:
                print("Heat break (2 min)...", flush=True)
                time.sleep(2 * 60)

print("Charging complete.", flush=True)
