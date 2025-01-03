import browser_cookie3
import json
import os
from typing import Optional, Dict

def get_hoyolab_tokens() -> Dict[str, str]:
    """
    ブラウザからHoYoLabのクッキーを取得します
    """
    tokens = {
        "ltoken_v2": "",
        "ltuid_v2": "",
    }
    
    browsers = [
        (browser_cookie3.chrome, "Chrome"),
        (browser_cookie3.firefox, "Firefox"),
        (browser_cookie3.edge, "Edge"),
    ]
    
    for browser_func, browser_name in browsers:
        try:
            cookies = browser_func(domain_name="hoyolab.com")
            for cookie in cookies:
                if cookie.name in tokens.keys():
                    tokens[cookie.name] = cookie.value
                    print(f"{browser_name}から{cookie.name}を取得しました")
            
            if all(tokens.values()):
                print(f"\n{browser_name}から必要な情報を取得できました！")
                return tokens
                
        except Exception as e:
            print(f"{browser_name}からのクッキー取得に失敗: {e}")
    
    raise Exception("どのブラウザからもHoYoLabのクッキーを取得できませんでした。\nHoYoLabにログインしているか確認してください。")

def get_uid_input(game_name: str) -> Optional[str]:
    """
    ユーザーにUIDの入力を求めます
    """
    while True:
        uid = input(f"{game_name}のUIDを入力してください（スキップする場合は Enter）: ").strip()
        if not uid: 
            return None
        if uid.isdigit() and len(uid) >= 8:
            return uid
        print("無効なUIDです。数字のみで8文字以上入力してください。")

def create_config_file(tokens: Dict[str, str], filename: str = "config.json") -> None:
    """
    設定ファイルを作成します
    """
    config_data = tokens.copy()
    
    genshin_uid = get_uid_input("原神")
    if genshin_uid:
        config_data["uid"] = genshin_uid
    
    hsr_uid = get_uid_input("崩壊：スターレイル")
    if hsr_uid:
        config_data["hsr_uid"] = hsr_uid
    
    if os.path.exists(filename):
        backup_name = f"{filename}.backup"
        os.rename(filename, backup_name)
        print(f"既存の設定ファイルを{backup_name}にバックアップしました")
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    print(f"\n設定ファイルを{filename}に保存しました！")

def main():
    try:
        print("HoYoLab認証情報取得ツール\n")
        print("注意: このプログラムを実行する前に以下を確認してください：")
        print("1. HoYoLab (https://www.hoyolab.com) にログインしていること")
        print("2. ブラウザを開いたままにしていること\n")
        
        input("準備ができたら Enter キーを押してください...")
        print("\nクッキーを取得中...\n")
        
        tokens = get_hoyolab_tokens()
        create_config_file(tokens)
        
        print("\n完了しました！")
        print("生成された config1.json ファイルをリソーストラッカーと同じフォルダに置いてください。")
        
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
    
    input("\nEnter キーを押して終了...")

if __name__ == "__main__":
    main()