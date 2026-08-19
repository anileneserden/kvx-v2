import os
import subprocess
import json

def build_app_gui_project(target_dir, project_name):
    print(f"Derleme başlatılıyor (app-gui: {project_name})...")
    
    build_dir = os.path.join(target_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    main_obj = os.path.join(build_dir, "main.o")
    src_main = os.path.join(target_dir, "src", "main.cpp")
    layout_path = os.path.join(target_dir, "layout.json")
    output_kef = os.path.join(target_dir, f"{project_name}.kef")
    
    cmd = [
        "i686-elf-g++", "-m32", "-c", src_main, "-o", main_obj,
        "-I", os.path.join(target_dir, "include"),
        "-I", os.path.expanduser("~/.kuvix/sdk/include"),
        "-fno-rtti", "-fno-exceptions"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        # 1. layout.json dosyasını oku
        json_data = ""
        if os.path.exists(layout_path):
            with open(layout_path, "r", encoding="utf-8") as f:
                json_data = f.read()
                
        # 2. Derlenen binary (ELF) verisini oku
        with open(main_obj, "rb") as f:
            binary_code = f.read()
            
        # 3. KEF formatında paketle (Magic Number + JSON Boyutu + JSON + Binary)
        with open(output_kef, "wb") as f:
            f.write(b"KEF1")
            
            json_bytes = json_data.encode("utf-8")
            json_len = len(json_bytes)
            
            f.write(json_len.to_bytes(4, byteorder='little'))
            f.write(json_bytes)
            f.write(binary_code)
            
        print(f"Başarılı: '{project_name}.kef' paketi KEF1 formatında oluşturuldu.")
        
    except subprocess.CalledProcessError:
        print("Hata: Derleme sırasında bir sorun oluştu.")
    except Exception as e:
        print(f"Hata: Paketleme sırasında sorun oluştu: {e}")