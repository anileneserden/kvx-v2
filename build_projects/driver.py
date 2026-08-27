import os
import subprocess
import glob
import json

def build_driver_project(path, *args, **kwargs):
    # Proje adını dizin adından veya kvx.json'dan dinamik olarak alalım
    project_name = os.path.basename(os.path.abspath(path))
    kvx_json_path = os.path.join(path, "kvx.json")
    
    if os.path.exists(kvx_json_path):
        try:
            with open(kvx_json_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                project_name = cfg.get("name", project_name)
        except Exception:
            pass

    print(f"Derleme başlatılıyor ({project_name} - Sürücü)...")
    
    src_dir = os.path.join(path, "src")
    build_dir = os.path.join(path, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    # Tüm .c dosyalarını bul
    c_files = glob.glob(os.path.join(src_dir, "**/*.c"), recursive=True)
    if not c_files:
        print("Hata: Derlenecek .c dosyası bulunamadı!")
        return False
        
    sdk_inc = os.path.expanduser("~/.kuvix/sdk/include")
    obj_files = []
    
    # 1. Her bir .c dosyasını .o nesne dosyasına derle
    for c_file in c_files:
        rel_path = os.path.relpath(c_file, src_dir)
        obj_file = os.path.join(build_dir, rel_path.replace(".c", ".o"))
        os.makedirs(os.path.dirname(obj_file), exist_ok=True)
        
        gcc_cmd = [
            "i686-elf-gcc",
            "-m32", "-march=i686", "-c",
            "-ffreestanding", "-fno-pic", "-fno-pie",
            "-mno-sse", "-mno-mmx", "-mno-80387",
            "-fno-stack-protector", "-fno-builtin",
            "-fno-asynchronous-unwind-tables",
            "-ffunction-sections", "-fdata-sections",
            f"-I{sdk_inc}",
            "-O2", "-Wall", "-Wextra",
            c_file, "-o", obj_file
        ]
        
        res = subprocess.run(gcc_cmd)
        if res.returncode != 0:
            print(f"Hata: '{c_file}' derlenirken başarısız oldu!")
            return False
            
        obj_files.append(obj_file)
        
    # 2. Linker ile dinamik isimli .kdf çıktısını oluştur (örn: e1000.kdf)
    target = os.path.join(path, f"{project_name}.kdf")
    ld_script = os.path.join(path, "linker.ld")
    
    ld_cmd = [
        "i686-elf-ld",
        "-m", "elf_i386",
        "-nostdlib",
        "-T", ld_script,
        "-o", target
    ] + obj_files
    
    res = subprocess.run(ld_cmd)
    if res.returncode != 0:
        print("Hata: Sürücü linkleme (bağlama) başarısız oldu!")
        return False
        
    print(f"Başarılı: Sürücü başarıyla derlendi -> {target}")
    return True