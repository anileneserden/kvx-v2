import os
import subprocess

def build_app_gui_project(target_dir, project_name):
    print(f"Derleme başlatılıyor (app-gui: {project_name})...")
    
    build_dir = os.path.join(target_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    main_obj = os.path.join(build_dir, "main.o")
    src_main = os.path.join(target_dir, "src", "main.cpp")
    output_kef = os.path.join(target_dir, f"{project_name}.kef")
    
    cmd = [
        "i686-elf-g++", "-m32", "-c", src_main, "-o", main_obj,
        "-I", os.path.join(target_dir, "include"),
        "-I", os.path.expanduser("~/.kuvix/sdk/include"),
        "-fno-rtti", "-fno-exceptions"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        link_cmd = [
            "i686-elf-ld", "-m", "elf_i386", "-r", main_obj, 
            "-o", output_kef
        ]
        subprocess.run(link_cmd, check=True)
        print(f"Başarılı: '{project_name}.kef' dosyası doğrudan oluşturuldu.")
    except subprocess.CalledProcessError:
        print("Hata: Derleme sırasında bir sorun oluştu.")