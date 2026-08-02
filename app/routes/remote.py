
import json
import os
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# ADB Shell Hardware control utilities
from adb_shell.auth.keygen import keygen
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner


remote_router = APIRouter(prefix='/remote')

DB_FILE = "saved_devices.json"



# Pydantic Schemas (Data Validation)
class TVDevice(BaseModel):
    username: str
    name: str
    ip: str

class ControlRequest(BaseModel):
    ip: str
    command: str

class LoadDevicesRequest(BaseModel):
    username: str


ANDROID_KEY_MAP = {
    "POWER": "26",
    "MUTE": "164",
    "UP": "19",
    "DOWN": "20",
    "LEFT": "21",
    "RIGHT": "22",
    "SELECT": "66",  
    "BACK": "4",
    "HOME": "3",
    "VOL_UP": "24",   
    "VOL_DOWN": "25"  
}


def load_stored_devices(username: str) -> List[dict]:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                all_devices = json.load(f)
                user_devices = [d for d in all_devices if d.get('username') == username]
                return user_devices
            except json.JSONDecodeError:
                return []
    return []


def save_stored_devices(tvs_list: List[dict]):
    with open(DB_FILE, "w") as f:
        json.dump(tvs_list, f, indent=4)


def removeDevice(ip: str, username: str):
    devices = load_stored_devices()
    updated_devices = [d for d in devices if d.get("ip") != ip]
    save_stored_devices(updated_devices)
    
    user_devices = [d for d in updated_devices if d.get("username") == username]
    return user_devices





# Routes
@remote_router.post("/devices", response_model=List[TVDevice])
async def get_all_devices(req: LoadDevicesRequest):
    return load_stored_devices(req.username)


@remote_router.post("/add-device") 
async def register_new_tv(new_device: TVDevice):
    # 1. Load ALL global records from the file to check for absolute duplicates
    global_devices = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                global_devices = json.load(f)
            except json.JSONDecodeError:
                global_devices = []

    # 2. Check for duplicate IPs globally across the system
    if not any(device["ip"] == new_device.ip for device in global_devices):
        global_devices.append({
            "username": new_device.username, 
            "name": new_device.name, 
            "ip": new_device.ip
        })
        save_stored_devices(global_devices)

    # 3. Always fetch and return this specific user's updated clean list
    user_devices = load_stored_devices(new_device.username)
    return {"status": "success", "data": user_devices}



@remote_router.post("/control")
async def control_tv_node(req: ControlRequest):
    is_app_shortcut = req.command in ["YOUTUBE"]
    
    if not is_app_shortcut and req.command not in ANDROID_KEY_MAP:
        return {"status": "error", "message": f"Unknown command: {req.command}"}

    # Locate or generate internal security RSA pairing keys
    private_key_path = "adbkey"
    public_key_path = "adbkey.pub"
    if not os.path.exists(private_key_path):
        keygen(private_key_path)

    with open(private_key_path, 'r') as f: priv = f.read()
    with open(public_key_path, 'r') as f: pub = f.read()
    signer = PythonRSASigner(pub, priv)

    try:
        device = AdbDeviceTcp(req.ip, 5555, default_transport_timeout_s=6.0)
        device.connect(rsa_keys=[signer], auth_timeout_s=4.0)
        
      
        if req.command == "YOUTUBE":
            print(f"📺 LAUNCH APPLICATION: YouTube executing on {req.ip}")
            device.shell("monkey -p com.amazon.firetv.youtube -c android.intent.category.LAUNCHER 1")
        else:
            keycode = ANDROID_KEY_MAP[req.command]
            print(f"🔌 REMOTE TRIGGER: Sending keycode {keycode} ({req.command}) to {req.ip}")
            device.shell(f"input keyevent {keycode}")
        
        device.close()
        return {"status": "success"}
    except Exception as e:
        print(f"❌ ADB PIPELINE FAILURE: Connection failure on target {req.ip}. Details: {e}")
        return {"status": "error", "message": str(e)}
