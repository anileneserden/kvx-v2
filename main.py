import sys
import os
import json
import argparse
import tty
import termios
from create_projects.de import create_new_project
from build_projects.de import build_de_project

GREEN = "\033[92m"
BOLD = "\033[1m"
RESET = "\033[0m"
RED = "\033[91m"

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
                    output += f"{GREEN}{BOLD}> [x] {opt}{RESET}   "
                else:
                    output += f"  [ ] {opt}   "
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
    project_types = ["DE (Desktop Environment)"]
    selected_type_label = interactive_menu("Proje Tipini Seçin:", project_types)
    
    p_type = "de" if "DE" in selected_type_label else "de"

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
        create_new_project(".", name, version, author)
    else:
        print(f"{RED}Hata: Bilinmeyen proje tipi!{RESET}")

def main():
    parser = argparse.ArgumentParser(description="KuvixOS V2 Geliştirme Aracı (DE)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Yeni bir DE projesini interaktif olarak başlatır")

    create_parser = subparsers.add_parser("create", help="Yeni bir DE projesi oluşturur")
    create_parser.add_argument("name", nargs="?", help="Proje adı")

    build_parser = subparsers.add_parser("build", help="DE projesini derler")
    build_parser.add_argument("dir", nargs="?", default=".", help="Proje dizini")
    build_parser.add_argument("-c", "--clean", action="store_true", help="Derlemeden önce eski çıktıları temizler")

    args = parser.parse_args()

    if args.command == "init" or args.command == "create":
        run_create_flow(args.name if args.command == "create" else None)
    elif args.command == "build":
        target_dir = args.dir
        config_path = os.path.join(target_dir, "kvx.json")
        
        # Proje tipini kvx.json üzerinden dinamik olarak okuyoruz
        p_type = "de"  # Varsayılan
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
            import shutil
            if os.path.exists(build_dir):
                shutil.rmtree(build_dir)
            
            # Proje tipine göre temizlenecek özel çıktı dosyaları
            if p_type == "de":
                kde_file = os.path.join(target_dir, f"{project_name}.kde")
                if os.path.exists(kde_file):
                    os.remove(kde_file)
            print(f"{GREEN}Temizlik tamamlandı.{RESET}")

        # Proje tipine göre ilgili build modülünü tetikle
        if p_type == "de":
            build_de_project(target_dir, project_name)
        else:
            print(f"{RED}Hata: '{p_type}' tipindeki projeler için derleyici bulunamadı!{RESET}")

if __name__ == "__main__":
    main()