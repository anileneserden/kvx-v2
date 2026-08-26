import sys
import os
import json
import argparse
import tty
import termios
import shutil

from create_projects.de import create_new_project as create_de_project
from create_projects.app_gui import create_new_project as create_app_gui_project
from create_projects.login_screen import create_new_project as create_login_screen_project
from create_projects.driver import create_new_project as create_driver_project

from build_projects.de import build_de_project
from build_projects.app_gui import build_app_gui_project
from build_projects.login_screen import build_login_screen_project
from build_projects.driver import build_driver_project

# Sürüm Bilgisi
VERSION = "0.1.9"

GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"
CYAN = "\033[96m"

# Yapılandırma Sabitleri ve Yardımcı Fonksiyonlar
CONFIG_DIR = os.path.expanduser("~/.kuvix")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "default_editor": "none",
    "sdk_path": os.path.expanduser("~/.kuvix/sdk")
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        ensure_config_dir()
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Varsayılan değerlerle eksik anahtarları tamamla
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config_data):
    ensure_config_dir()
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

def ensure_config_dir():
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

def print_banner():
    banner = f"""{CYAN}
    _  __    _  __
   | |/ /   | |/ /
   | ' /    | ' / 
   | . \    | . \ 
   |_|\_\   |_|\_\  v{VERSION}
{RESET}KuvixOS SDK & Build Management Tool
"""
    print(banner)

def interactive_menu(title, options):
    current_idx = 0
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    print(f"{BOLD}? {title}{RESET} (Yön tuşları ile seçin, Enter ile onaylayın)")
    try:
        tty.setraw(sys.stdin.fileno())
        while True:
            sys.stdout.write("\r\033[K")
            output = ""
            for i, opt in enumerate(options):
                if i == current_idx:
                    output += f"{GREEN}{BOLD}> [{opt}]{RESET}   "
                else:
                    output += f"  [{opt}]   "
            sys.stdout.write(output)
            sys.stdout.flush()

            ch = sys.stdin.read(1)
            if ch == '\x1b':
                sys.stdin.read(1)
                ch3 = sys.stdin.read(1)
                if ch3 == 'D':
                    current_idx = (current_idx - 1) % len(options)
                elif ch3 == 'C':
                    current_idx = (current_idx + 1) % len(options)
            elif ch == '\r' or ch == '\n':
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\n")
    return options[current_idx]

def run_create_flow(target_name=None):
    print_banner()

    project_types = ["app-cli", "app-gui", "de", "login-screen", "driver"]
    selected_type = interactive_menu("Proje Türünü Seçin:", project_types)

    p_type = selected_type

    print(f"{BOLD}Proje Detaylarını Girin:{RESET}")

    name = target_name
    if not name:
        name = input(f"{BOLD}? Proje Adı: {RESET}").strip()
    else:
        print(f"{BOLD}? Proje Adı: {RESET}{name}")

    if not name:
        print(f"{RED}Hata: Proje adı boş olamaz.{RESET}")
        return

    version = input(f"{BOLD}? Sürüm (1.0.0): {RESET}").strip() or "1.0.0"
    author = input(f"{BOLD}? Geliştirici (Anıl Enes Erden): {RESET}").strip() or "Anıl Enes Erden"

    print(f"\n{GREEN}Oluşturuluyor: {name} (Tip: {p_type}, Sürüm: {version}, Sahip: {author})...{RESET}")

    if p_type == "de":
        create_de_project(".", name, version, author)
    elif p_type == "app-gui":
        create_app_gui_project(".", name, version, author)
    elif p_type == "login-screen":
        create_login_screen_project(".", name, version, author)
    elif p_type == "driver":
        create_driver_project(".", name, version, author)
    else:
        print(f"{RED}Hata: '{p_type}' tipi için henüz proje şablonu tanımlanmadı!{RESET}")

def main():
    parser = argparse.ArgumentParser(description="KuvixOS V2 Geliştirme Aracı")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Yeni bir projeyi interaktif olarak başlatır")

    create_parser = subparsers.add_parser("create", help="Yeni bir proje oluşturur")
    create_parser.add_argument("name", nargs="?", help="Proje adı")

    build_parser = subparsers.add_parser("build", help="Projeyi derler")
    build_parser.add_argument("dir", nargs="?", default=".", help="Proje dizini")
    build_parser.add_argument("-c", "--clean", action="store_true", help="Derlemeden önce eski çıktıları temizler")

    # Settings komutu
    settings_parser = subparsers.add_parser("settings", help="SDK and araç ayarlarını yapılandırır")
    settings_parser.add_argument("--default-editor", choices=["vscode", "code", "none"], help="Varsayılan kod editörünü ayarlar")
    settings_parser.add_argument("--sdk-path", help="KuvixOS SDK dizin yolunu ayarlar")

    subparsers.add_parser("info", help="Araç ve SDK hakkında bilgi gösterir")

    args = parser.parse_args()

    if args.command in ["init", "create"]:
        run_create_flow(args.name if args.command == "create" else None)
    
    elif args.command == "build":
        target_dir = args.dir
        config_path = os.path.join(target_dir, "kvx.json")
        
        p_type = "de"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    p_type = config_data.get("type", "de")
            except Exception:
                pass

        project_name = os.path.basename(os.path.abspath(target_dir))
        
        if args.clean:
            print(f"{GREEN}Temizleniyor: {project_name}...{RESET}")
            build_dir = os.path.join(target_dir, "build")
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
            
            if p_type == "de":
                kde_file = os.path.join(target_dir, f"{project_name}.kde")
                if os.path.exists(kde_file):
                    os.remove(kde_file)
            elif p_type == "app-gui":
                kef_file = os.path.join(target_dir, f"{project_name}.kef")
                if os.path.exists(kef_file):
                    os.remove(kef_file)
            elif p_type == "login_screen":
                kls_file = os.path.join(target_dir, f"{project_name}.kls")
                if os.path.exists(kls_file):
                    os.remove(kls_file)
            elif p_type == "driver":
                kdf_file = os.path.join(target_dir, f"{project_name}.kdf")
                if os.path.exists(kdf_file):
                    os.remove(kdf_file)
            print(f"{GREEN}Temizlik tamamlandı.{RESET}")

        if p_type == "de":
            build_de_project(target_dir, project_name)
        elif p_type == "app-gui":
            build_app_gui_project(target_dir, project_name)
        elif p_type == "login_screen":
            build_login_screen_project(target_dir, project_name)
        elif p_type == "driver":
            build_driver_project(target_dir, project_name)
        else:
            print(f"{RED}Hata: '{p_type}' tipindeki projeler için derleyici bulunamadı!{RESET}")

    elif args.command == "settings":
        cfg = load_config()
        updated = False

        if args.default_editor:
            val = "vscode" if args.default_editor in ["vscode", "code"] else "none"
            cfg["default_editor"] = val
            updated = True
            print(f"{GREEN}Varsayılan editör ayarlandı: {val}{RESET}")

        if args.sdk_path:
            abs_path = os.path.abspath(os.path.expanduser(args.sdk_path))
            cfg["sdk_path"] = abs_path
            updated = True
            print(f"{GREEN}SDK yolu ayarlandı: {abs_path}{RESET}")

        if updated:
            save_config(cfg)
        else:
            print(f"{BOLD}KuvixOS Ayarları ({CONFIG_PATH}):{RESET}")
            print(f"  • Varsayılan Editör: {cfg.get('default_editor')}")
            print(f"  • SDK Yolu        : {cfg.get('sdk_path')}")

    elif args.command == "info":
        cfg = load_config()
        print_banner()
        print(f"{BOLD}KuvixOS Geliştirme Ortamı{RESET}")
        print(f"Versiyon         : {VERSION}")
        print(f"SDK Yolu         : {cfg.get('sdk_path')}")
        print(f"Varsayılan Editör: {cfg.get('default_editor')}")

if __name__ == "__main__":
    main()