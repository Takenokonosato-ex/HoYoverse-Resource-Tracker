import requests
import time
import hashlib
import random
import string
import json
import customtkinter as ctk
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    ltoken: str
    ltuid: str
    uid: str  # Genshin Impact UID
    hsr_uid: Optional[str] = None  # HSR UID（オプション）

def load_config(path: str) -> Config:
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            # HSR UIDが設定されていない場合は、Genshin UIDを使用
            hsr_uid = data.get("hsr_uid", data.get("uid"))
            return Config(
                ltoken=data["ltoken_v2"],
                ltuid=data["ltuid_v2"],
                uid=data["uid"],
                hsr_uid=hsr_uid
            )
    except FileNotFoundError:
        print(f"Config file not found: {path}")
        raise
    except json.JSONDecodeError:
        print(f"Invalid JSON in config file: {path}")
        raise
    except KeyError as e:
        print(f"Missing required key in config: {e}")
        raise

class HoyoClient:
    GENSHIN_URL = "https://bbs-api-os.hoyolab.com/game_record/genshin/api/dailyNote"
    HSR_URL = "https://bbs-api-os.hoyolab.com/game_record/hkrpg/api/note"
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self):
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-G973U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/14.2 Chrome/87.0.4280.141 Mobile Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "x-rpc-client_type": "5",
            "x-rpc-app_version": "1.5.0",
            "x-rpc-language": "en-us",
            "Origin": "https://act.hoyolab.com",
            "Connection": "keep-alive",
            "Referer": "https://act.hoyolab.com/",
            "Cookie": f"ltoken_v2={self.config.ltoken}; ltuid_v2={self.config.ltuid}"
        })

    def _generate_ds(self) -> str:
        salt = "6s25p5ox5y14umn1p61aqyyvbvvl3lrt"
        t = int(time.time())
        r = ''.join(random.choices(string.ascii_letters, k=6))
        
        h = hashlib.md5(f"salt={salt}&t={t}&r={r}".encode()).hexdigest()
        return f"{t},{r},{h}"

    def get_genshin_notes(self) -> dict:
        server = self._get_genshin_server(self.config.uid[0])
        
        params = {
            "server": server,
            "role_id": self.config.uid
        }
        
        self.session.headers["DS"] = self._generate_ds()
        response = self.session.get(self.GENSHIN_URL, params=params)
        response.raise_for_status()
        
        return response.json()

    def get_hsr_notes(self) -> dict:
        if not self.config.hsr_uid:
            return {"retcode": -1, "message": "HSR UID not configured", "data": None}
            
        server = self._get_hsr_server(self.config.hsr_uid[0])
        
        params = {
            "server": server,
            "role_id": self.config.hsr_uid
        }
        
        self.session.headers["DS"] = self._generate_ds()
        response = self.session.get(self.HSR_URL, params=params)
        response.raise_for_status()
        
        return response.json()

    def _get_genshin_server(self, uid_first_char: str) -> str:
        servers = {
            "1": "cn_gf01",
            "2": "cn_gf01",
            "5": "cn_qd01",
            "6": "os_usa",
            "7": "os_euro",
            "8": "os_asia",
            "9": "os_cht"
        }
        return servers.get(uid_first_char, "os_usa")

    def _get_hsr_server(self, uid_first_char: str) -> str:
        servers = {
            "1": "prod_gf_cn",
            "2": "prod_gf_cn",
            "5": "prod_qd_cn",
            "6": "prod_official_usa",
            "7": "prod_official_eur",
            "8": "prod_official_asia",
            "9": "prod_official_cht"
        }
        return servers.get(uid_first_char, "prod_official_usa")

def update_resources_in_gui(root, genshin_frame, hsr_frame, resource_data):
    # Update Genshin Impact frame
    if resource_data.get('resin'):
        genshin_frame.progress_bar.set(resource_data['resin']['current'] / resource_data['resin']['max'])
        genshin_frame.resource_label.configure(text=f"樹脂: {resource_data['resin']['current']}/{resource_data['resin']['max']}")
        genshin_frame.time_label.configure(text=f"回復まで: {resource_data['resin']['recovery_time']}")
    
    # Update HSR frame
    if resource_data.get('stamina'):
        hsr_frame.progress_bar.set(resource_data['stamina']['current'] / resource_data['stamina']['max'])
        hsr_frame.resource_label.configure(text=f"スタミナ: {resource_data['stamina']['current']}/{resource_data['stamina']['max']}")
        hsr_frame.time_label.configure(text=f"回復まで: {resource_data['stamina']['recovery_time']}")
    
    root.after(30000, fetch_and_update, root, genshin_frame, hsr_frame)

class GameFrame(ctk.CTkFrame):
    def __init__(self, master, title):
        super().__init__(master)
        
        self.title_label = ctk.CTkLabel(self, text=title, font=("Arial", 16, "bold"))
        self.title_label.pack(pady=5)
        
        self.resource_label = ctk.CTkLabel(self, text="読み込み中...", font=("Arial", 14))
        self.resource_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self, width=250, height=15)
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)
        
        self.time_label = ctk.CTkLabel(self, text="読み込み中...", font=("Arial", 14))
        self.time_label.pack(pady=5)

def fetch_and_update(root, genshin_frame, hsr_frame):
    try:
        config = load_config("config.json")
        client = HoyoClient(config)
        
        resource_data = {}
        
        # Fetch Genshin Impact data
        try:
            genshin_response = client.get_genshin_notes()
            if genshin_response["retcode"] == 0:
                genshin_data = genshin_response["data"]
                current_resin = genshin_data["current_resin"]
                max_resin = genshin_data["max_resin"]
                resin_recovery_time = int(genshin_data["resin_recovery_time"])
                
                resin_hours, resin_remainder = divmod(resin_recovery_time, 3600)
                resin_minutes, _ = divmod(resin_remainder, 60)
                resin_time_str = f"{resin_hours}h {resin_minutes}m"
                
                resource_data["resin"] = {
                    "current": current_resin,
                    "max": max_resin,
                    "recovery_time": resin_time_str
                }
            else:
                print(f"Genshin API Error: {genshin_response.get('message')}")
                genshin_frame.resource_label.configure(text="データが取得できません")
                genshin_frame.time_label.configure(text="HoYoLABの公開設定を確認してください")
        except Exception as e:
            print(f"Error fetching Genshin data: {e}")
            genshin_frame.resource_label.configure(text="エラーが発生しました")
            genshin_frame.time_label.configure(text="コンソールを確認してください")
        
        # Fetch HSR data
        try:
            hsr_response = client.get_hsr_notes()
            if hsr_response["retcode"] == 0:
                hsr_data = hsr_response["data"]
                current_stamina = hsr_data["current_stamina"]
                max_stamina = hsr_data["max_stamina"]
                stamina_recovery_time = int(hsr_data["stamina_recover_time"])
                
                stamina_hours, stamina_remainder = divmod(stamina_recovery_time, 3600)
                stamina_minutes, _ = divmod(stamina_remainder, 60)
                stamina_time_str = f"{stamina_hours}h {stamina_minutes}m"
                
                resource_data["stamina"] = {
                    "current": current_stamina,
                    "max": max_stamina,
                    "recovery_time": stamina_time_str
                }
            else:
                error_msg = hsr_response.get('message', '')
                print(f"HSR API Error: {error_msg}")
                if "Data is not public" in error_msg:
                    hsr_frame.resource_label.configure(text="データが非公開です")
                    hsr_frame.time_label.configure(
                        text="HoYoLABでスターレイルの\nリアルタイムノートを公開に設定してください"
                    )
                else:
                    hsr_frame.resource_label.configure(text="APIエラー")
                    hsr_frame.time_label.configure(text="設定を確認してください")
        except Exception as e:
            print(f"Error fetching HSR data: {e}")
            hsr_frame.resource_label.configure(text="エラーが発生しました")
            hsr_frame.time_label.configure(text="コンソールを確認してください")
            
        if resource_data:
            update_resources_in_gui(root, genshin_frame, hsr_frame, resource_data)
            
    except Exception as e:
        print(f"General error: {e}")
        genshin_frame.resource_label.configure(text="エラーが発生しました")
        genshin_frame.time_label.configure(text="コンソールを確認してください")
        hsr_frame.resource_label.configure(text="エラーが発生しました")
        hsr_frame.time_label.configure(text="コンソールを確認してください")

def show_resources_in_gui():
    root = ctk.CTk()
    root.title("HoYoverse Resource Tracker")
    
    # Create frames for each game
    genshin_frame = GameFrame(root, "原神")
    genshin_frame.pack(padx=20, pady=10, fill="x")
    
    separator = ctk.CTkFrame(root, height=2)
    separator.pack(fill="x", padx=20, pady=10)
    
    hsr_frame = GameFrame(root, "崩壊：スターレイル")
    hsr_frame.pack(padx=20, pady=10, fill="x")
    
    fetch_and_update(root, genshin_frame, hsr_frame)
    
    root.mainloop()

if __name__ == "__main__":
    show_resources_in_gui()