import json
import os
import subprocess
import tempfile


def resolve_project_name(target_dir, fallback_name):
    kvx_json_path = os.path.join(target_dir, "kvx.json")
    if os.path.isfile(kvx_json_path):
        try:
            with open(kvx_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            json_name = data.get("name")
            if isinstance(json_name, str) and json_name.strip():
                return json_name.strip()
        except Exception as e:
            print(f"Uyarı: kvx.json okunamadı ({e}), verilen isim kullanılacak.")
    return fallback_name.strip()


def build_de_project(project_path, name, target_arch="i686", custom_cflags="", custom_ldflags="", run_make=True):
    target_dir = os.path.abspath(project_path)

    if not os.path.exists(target_dir):
        print(f"Hata: '{target_dir}' dizini bulunamadı!")
        return False

    resolved_name = resolve_project_name(target_dir, name)
    ldflags = custom_ldflags if custom_ldflags else "-m elf_i386 -T linker.ld --gc-sections -e _start -s"

    makefile_content = f"""TARGET = {resolved_name}.kde
KUVIX_SDK_INC = $(HOME)/.kuvix/sdk/include
AS = i686-elf-as
CC = i686-elf-gcc
LD = i686-elf-ld

CFLAGS = -m32 -Wa,--32 -march={target_arch} -std=gnu11 -c -ffreestanding -fno-pic -fno-pie -mno-sse -mno-mmx -mno-80387 \\
         -fno-stack-protector -fno-builtin -fno-asynchronous-unwind-tables \\
         -ffunction-sections -fdata-sections -Wall -Wextra -Iinclude -I$(KUVIX_SDK_INC) {custom_cflags}

LDFLAGS = {ldflags}

C_SRCS = $(shell find src -type f -name '*.c' 2>/dev/null)
C_OBJS = $(patsubst src/%.c, build/%.o, $(C_SRCS))

ENTRY_OBJ = build/runtime/entry.o
OBJS = $(ENTRY_OBJ) $(filter-out $(ENTRY_OBJ), $(C_OBJS))

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
\t$(LD) $(LDFLAGS) $(OBJS) -o $(TARGET)

build/runtime/entry.o: src/runtime/entry.s
\t@mkdir -p $(dir $@)
\t$(AS) --32 $< -o $@

build/%.o: src/%.c
\t@mkdir -p $(dir $@)
\t$(CC) $(CFLAGS) $< -o $@

clean:
\trm -rf build $(TARGET)
"""

    fd, makefile_path = tempfile.mkstemp(prefix=f"Makefile_{resolved_name}_", suffix=".mk", dir="/tmp")
    os.close(fd)

    try:
        with open(makefile_path, "w", encoding="utf-8") as f:
            f.write(makefile_content)

        print(f"Başarılı: '{resolved_name}' için geçici Makefile '/tmp' dizininde oluşturuldu ({makefile_path}).")

        if run_make:
            print(f"Derleme başlatılıyor ({resolved_name})...")
            result = subprocess.run(["make", "-f", makefile_path], cwd=target_dir)
            if result.returncode != 0:
                print("Hata: Derleme başarısız oldu!")
                return False
            print(f"Başarılı: '{resolved_name}.kde' başarıyla derlendi.")

        return True
    finally:
        if run_make and os.path.exists(makefile_path):
            os.remove(makefile_path)