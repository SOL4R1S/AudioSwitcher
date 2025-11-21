import os
import subprocess
import sys
import re
import json
import time

CONFIG_FILE = "audio_switcher_config.json"

# ========================================================
# 🌍 다국어 사전 (메뉴 복귀 메시지 추가됨)
# ========================================================
LANG = {
    "ko": {
        "title": "🔊 오디오 출력 장치 변경기",
        "ask_path": "Nircmd.exe 파일의 전체 경로를 입력해주세요\n(예: D:\\Tools\\nircmd.exe): ",
        "path_error": "❌ 파일을 찾을 수 없습니다. 올바른 경로를 입력해주세요.",
        "scan_start": "장치 목록을 불러오는 중...",
        "scan_error": "❌ 장치를 찾을 수 없습니다.",
        "menu_title": "[변경할 장치를 선택하세요]",
        "opt_lang": "[설정] 언어 변경 (Change Language)",
        "opt_path": "[설정] Nircmd 경로 변경 (Change Path)",
        "opt_exit": "종료 (Exit)",
        "input_prompt": "번호 입력",
        "invalid_input": "⚠️ 올바른 번호를 입력해주세요.",
        "switching": "🔄 변경 시도: ",
        "success": "✅ 명령 전송 완료! (소리를 확인하세요)",
        "fail": "❌ 모든 시도가 실패했습니다.",
        "return_menu": "엔터를 누르면 메뉴로 돌아갑니다...", # 추가됨
        "set_saved": "✅ 설정이 저장되었습니다! 메뉴를 새로고침합니다."
    },
    "en": {
        "title": "🔊 Audio Output Switcher",
        "ask_path": "Please enter the full path of Nircmd.exe\n(Ex: D:\\Tools\\nircmd.exe): ",
        "path_error": "❌ File not found. Please enter a valid path.",
        "scan_start": "Scanning audio devices...",
        "scan_error": "❌ No devices found.",
        "menu_title": "[Select a device to switch]",
        "opt_lang": "[Settings] Change Language",
        "opt_path": "[Settings] Change Nircmd Path",
        "opt_exit": "Exit",
        "input_prompt": "Enter Number",
        "invalid_input": "⚠️ Please enter a valid number.",
        "switching": "🔄 Switching to: ",
        "success": "✅ Command sent! (Check your audio)",
        "fail": "❌ All attempts failed.",
        "return_menu": "Press Enter to return to menu...", # Added
        "set_saved": "✅ Settings saved! Reloading menu."
    }
}

# ========================================================
# ⚙️ 설정 관리
# ========================================================
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_config(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ========================================================
# 🔧 설정 변경 함수들
# ========================================================
def set_language():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Select Language / 언어를 선택하세요")
    print("1. 한국어 (Korean)")
    print("2. English")
    while True:
        c = input("Number (1 or 2): ").strip()
        if c == "1": return "ko"
        elif c == "2": return "en"

def set_path(current_lang):
    txt = LANG[current_lang]
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"[{txt['title']}]\n")
        user_input = input(txt['ask_path']).strip()
        user_input = user_input.strip('"').strip("'")
        
        if os.path.exists(user_input) and user_input.lower().endswith("nircmd.exe"):
            return user_input
        else:
            print(f"\n{txt['path_error']}")
            input("Press Enter to retry...")

# ========================================================
# 🔊 핵심 기능
# ========================================================
def get_devices_via_powershell():
    ps_command = "Get-PnpDevice -Class AudioEndpoint | Where-Object { $_.Status -eq 'OK' } | Select-Object -ExpandProperty FriendlyName"
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        output = subprocess.check_output(["powershell", "-Command", ps_command], startupinfo=startupinfo, stderr=subprocess.DEVNULL)
        decoded = output.decode('cp949', errors='ignore')
        raw_list = decoded.strip().split('\r\n')
        devices = []
        for name in raw_list:
            name = name.strip()
            if not name: continue
            if "Microphone" not in name and "Input" not in name:
                devices.append(name)
        return devices
    except:
        return []

def try_switch_device(original_name, nircmd_path, txt):
    print(f"\n{txt['switching']}[{original_name}]")
    candidates = [original_name]
    if "(" in original_name:
        candidates.append(original_name.split("(")[0].strip())
    match = re.search(r'\((.*?)\)', original_name)
    if match:
        candidates.append(match.group(1).strip())
    
    candidates = list(set(candidates))
    success = False
    for name in candidates:
        if not name: continue
        print(f"   👉 '{name}'...", end=" ")
        try:
            subprocess.run([nircmd_path, "setdefaultsounddevice", name], check=True)
            print("OK")
            success = True
        except:
            print("Fail")
            
    print(f"\n{txt['success']}" if success else f"\n{txt['fail']}")

# ========================================================
# 🏁 메인 프로그램 (Loop)
# ========================================================
def main():
    config = load_config()
    if not config:
        lang_code = set_language()
        nircmd_path = set_path(lang_code)
        save_config({"lang": lang_code, "path": nircmd_path})
    
    while True:
        config = load_config()
        lang_code = config.get("lang", "ko")
        nircmd_path = config.get("path", "")
        txt = LANG[lang_code]

        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n" + "="*40)
        print(f"   {txt['title']}")
        print("="*40)

        # 1. 장치 스캔
        print(txt['scan_start'], end=" ")
        devices = get_devices_via_powershell()
        print("OK!")

        # 2. 메뉴 출력
        print(f"\n{txt['menu_title']}")
        
        last_index = 0
        for i, name in enumerate(devices):
            print(f" {i + 1}. {name}")
            last_index = i + 1
        
        print("-" * 20)
        menu_lang_idx = last_index + 1
        menu_path_idx = last_index + 2
        menu_exit_idx = last_index + 3

        print(f" {menu_lang_idx}. {txt['opt_lang']}")
        print(f" {menu_path_idx}. {txt['opt_path']}")
        print(f" {menu_exit_idx}. {txt['opt_exit']}")
        print("="*40)

        # 3. 입력 처리
        try:
            choice = input(f"{txt['input_prompt']} (1~{menu_exit_idx}): ")
            sel = int(choice)
            
            # A. 장치 선택 시
            if 1 <= sel <= last_index:
                target_device = devices[sel - 1]
                try_switch_device(target_device, nircmd_path, txt)
                
                # ★ 핵심 수정 부분: 종료(break) 대신 대기 후 반복(continue)
                print(f"\n{txt['return_menu']}")
                input() # 엔터키 입력 대기
                continue # 다시 while문 처음으로 돌아감 (화면 갱신)

            # B. 언어 변경
            elif sel == menu_lang_idx:
                new_lang = set_language()
                save_config({"lang": new_lang, "path": nircmd_path})
                print(f"\n{LANG[new_lang]['set_saved']}")
                time.sleep(1)
                continue

            # C. 경로 변경
            elif sel == menu_path_idx:
                new_path = set_path(lang_code)
                save_config({"lang": lang_code, "path": new_path})
                print(f"\n{txt['set_saved']}")
                time.sleep(1)
                continue

            # D. 종료 선택 시 (이때만 반복문 탈출)
            elif sel == menu_exit_idx:
                print("Bye!")
                break

            else:
                print(txt['invalid_input'])
                time.sleep(1)
                
        except ValueError:
            print(txt['invalid_input'])
            time.sleep(1)

if __name__ == "__main__":
    main()