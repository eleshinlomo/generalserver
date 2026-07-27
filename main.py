import json
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# ADB Shell Hardware control utilities
from adb_shell.auth.keygen import keygen
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner

DB_FILE = "shared_tvs.json"

app = FastAPI(title="Smart Home Hub Server")

# Enable CORS for communication with Vite React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas (Data Validation)
class TVDevice(BaseModel):
    name: str
    ip: str

class ControlRequest(BaseModel):
    ip: str
    command: str


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

def load_stored_tvs() -> List[dict]:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_stored_tvs(tvs_list: List[dict]):
    with open(DB_FILE, "w") as f:
        json.dump(tvs_list, f, indent=4)

@app.get("/api/tvs", response_model=List[TVDevice])
async def get_all_household_tvs():
    return load_stored_tvs()

@app.post("/api/tvs")
async def register_new_tv(new_tv: TVDevice):
    current_tvs = load_stored_tvs()
    if not any(tv["ip"] == new_tv.ip for tv in current_tvs):
        current_tvs.append({"name": new_tv.name, "ip": new_tv.ip})
        save_stored_tvs(current_tvs)
    return {"status": "success"}

@app.post("/api/tv/control")
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
