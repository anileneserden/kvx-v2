import os
import subprocess

def build_command_project(project_path, name, target_arch="i686", custom_cflags="", custom_ldflags="", run_make=True):
    target_dir = os.path.abspath(project_path)
    
    if not os.path.exists(target_dir):
        print(f"Hata: '{target_dir}' dizini bulunamadı!")
        return False

    cflags = custom_cflags if custom_cflags else "-Wall -Wextra"
    ldflags = custom_ldflags if custom_ldflags else "-m32 -nostdlib -no-pie -T linker.ld"
    
    makefile_content = f"""CC = i686-elf-gcc
CFLAGS = -m32 -ffreestanding -fno-pie -fno-stack-protector -I$(HOME)/.kuvix/sdk/include {cflags}
LDFLAGS = {ldflags}

TARGET = {name}
SRC = src/main.c

all: $(TARGET)

$(TARGET): $(SRC) linker.ld
\t$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) -o $(TARGET)
"""

    makefile_path = os.path.join(target_dir, "Makefile")
    with open(makefile_path, "w", encoding="utf-8") as f:
        f.write(makefile_content)

    print(f"Başarılı: '{name}' için Makefile oluşturuldu.")

    if run_make:
        print(f"Derleme başlatılıyor ({name})...")
        result = subprocess.run(["make"], cwd=target_dir)
        if result.returncode != 0:
            print("Hata: Derleme başarısız oldu!")
            return False
        print(f"Başarılı: '{name}' başarıyla derlendi.")

    return True