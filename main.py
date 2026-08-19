import sys
import os
import json
import argparse
import tty
import termios
import shutil

from create_projects.de import create_new_project as create_de_project
from create_projects.app_gui import create_new_project as create_app_gui_project
from build_projects.de import build_de_project
from build_projects.app_gui import build_app_gui_project

# Sürüm Bilgisi
VERSION = "0.1.5"

GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"
CYAN = "\033[96m"

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

    project_types = ["app-cli", "app-gui", "de"]
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

    subparsers.add_parser("info", help="Araç ve SDK hakkında bilgi gösterir")

    args = parser.parse_args()

    if args.command == "init" or args.command == "create":
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
            print(f"{GREEN}Temizlik tamamlandı.{RESET}")

        if p_type == "de":
            build_de_project(target_dir, project_name)
        elif p_type == "app-gui":
            build_app_gui_project(target_dir, project_name)
        else:
            print(f"{RED}Hata: '{p_type}' tipindeki projeler için derleyici bulunamadı!{RESET}")
            
    elif args.command == "info":
        print_banner()
        print(f"{BOLD}KuvixOS Geliştirme Ortamı{RESET}")
        print(f"Versiyon: {VERSION}")
        print(f"SDK Yolu: {os.path.expanduser('~/.kuvix/sdk')}")

if __name__ == "__main__":
    main()