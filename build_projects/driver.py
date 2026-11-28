import os
import subprocess
import glob
import json


def build_driver_project(path, *args, **kwargs):
    project_name = os.path.basename(os.path.abspath(path))
    output_file = None
    include_dirs = []
    kvx_json_path = os.path.join(path, "kvx.json")

    default_local_inc = os.path.join(path, "include")
    if os.path.isdir(default_local_inc):
        include_dirs.append(default_local_inc)

    if os.path.exists(kvx_json_path):
        try:
            with open(kvx_json_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if isinstance(cfg, dict):
                    if isinstance(cfg.get("name"), str) and cfg["name"].strip():
                        project_name = cfg["name"].strip()
                    if isinstance(cfg.get("output_file"), str) and cfg["output_file"].strip():
                        output_file = cfg["output_file"].strip()
                    if isinstance(cfg.get("includeDirs"), list):
                        for inc in cfg["includeDirs"]:
                            if isinstance(inc, str) and inc.strip():
                                inc_str = inc.strip()
                                resolved_inc = (
                                    inc_str if os.path.isabs(inc_str) else os.path.join(path, inc_str)
                                )
                                if resolved_inc not in include_dirs:
                                    include_dirs.append(resolved_inc)
        except Exception:
            pass

    resolved_output = output_file if output_file else project_name.lower()

    print(f"Derleme başlatılıyor ({project_name} - Sürücü)...")

    src_dir = os.path.join(path, "src")
    build_dir = os.path.join(path, "build")
    os.makedirs(build_dir, exist_ok=True)

    # Tüm .c dosyalarını bul (src/*.c ve alt klasörler)
    c_files = sorted(set(
        glob.glob(os.path.join(src_dir, "*.c")) +
        glob.glob(os.path.join(src_dir, "**/*.c"), recursive=True)
    ))
    if not c_files:
        print("Hata: Derlenecek .c dosyası bulunamadı!")
        return False

    sdk_inc = os.path.expanduser("~/.kuvix/sdk/include")
    inc_flags = [f"-I{d}" for d in include_dirs]
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
            *inc_flags,
            "-O2", "-Wall", "-Wextra",
            c_file, "-o", obj_file
        ]

        res = subprocess.run(gcc_cmd)
        if res.returncode != 0:
            print(f"Hata: '{c_file}' derlenirken başarısız oldu!")
            return False

        obj_files.append(obj_file)

    # 2. Linker ile çıktı dosyasını oluştur
    target = (
        resolved_output
        if os.path.isabs(resolved_output)
        else os.path.join(path, resolved_output)
    )
    os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
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