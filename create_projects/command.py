import os
import json

def create_new_project(path, name, version, author):
    target_dir = os.path.abspath(os.path.join(path, name))

    if os.path.exists(target_dir):
        print(f"Hata: '{target_dir}' dizini zaten mevcut!")
        return False

    src_dir = os.path.join(target_dir, "src")
    vscode_dir = os.path.join(target_dir, ".vscode")

    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(vscode_dir, exist_ok=True)

    # 1. .vscode/c_cpp_properties.json
    config_path = os.path.expanduser("~/.kuvix/config.json")
    editor_mode = "none"
    sdk_path = os.path.expanduser("~/.kuvix/sdk")

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                editor_mode = cfg.get("default_editor", "none")
                sdk_path = cfg.get("sdk_path", sdk_path)
        except Exception:
            pass

    if editor_mode in ["vscode", "code"]:
        c_cpp_properties_content = {
            "configurations": [
                {
                    "name": "KuvixOS-Command",
                    "includePath": [
                        "${workspaceFolder}/**",
                        f"{sdk_path}/include/**"
                    ],
                    "defines": [],
                    "compilerPath": "/usr/bin/i686-elf-gcc",
                    "cStandard": "c17",
                    "cppStandard": "c++17",
                    "intelliSenseMode": "linux-gcc-x86"
                }
            ],
            "version": 4
        }
        with open(os.path.join(vscode_dir, "c_cpp_properties.json"), "w", encoding="utf-8") as f:
            json.dump(c_cpp_properties_content, f, indent=4, ensure_ascii=False)

    # 2. linker.ld (Harici Komut / Binary Linker Betiği)
    linker_content = """ENTRY(main)
SECTIONS
{
    . = 0x00800000;
    .text : { *(.text) } :text
    .rodata : { *(.rodata) } :rodata
    .data : { *(.data) } :data
    .bss : { *(COMMON) *(.bss) } :bss
}

PHDRS
{
    text PT_LOAD FLAGS(5);    /* Read + Execute */
    rodata PT_LOAD FLAGS(4);  /* Read-only */
    data PT_LOAD FLAGS(6);    /* Read + Write */
    bss PT_LOAD FLAGS(6);     /* Read + Write */
}
"""
    with open(os.path.join(target_dir, "linker.ld"), "w", encoding="utf-8") as f:
        f.write(linker_content)

    # 3. Makefile
    makefile_content = f"""CC = gcc
CFLAGS = -m32 -ffreestanding -fno-pie -fno-stack-protector -I{sdk_path}/include -Wall -Wextra
LDFLAGS = -m32 -nostdlib -no-pie -T linker.ld

TARGET = {name}
SRC = src/main.c

all: $(TARGET)

$(TARGET): $(SRC) linker.ld
\t$(CC) $(CFLAGS) $(SRC) $(LDFLAGS) -o $(TARGET)

clean:
\trm -f $(TARGET)

install: $(TARGET)
\tcp $(TARGET) /sys/bin/{name}
\t@echo "{name} komutu /sys/bin/{name} konumuna yuklendi!"
"""
    with open(os.path.join(target_dir, "Makefile"), "w", encoding="utf-8") as f:
        f.write(makefile_content)

    # 4. src/main.c (Komut Şablonu)
    main_c_code = """#include <cmd_api.h>

void main(int argc, char** argv, CmdAPI* api) {
    if (!api) return;

    if (argc < 2) {
        api->print("Kullanim: cat <dosya_adi>\\n");
        return;
    }

    const char* filepath = argv[1];
    char buffer[1024];
    
    int bytes = api->read_file(filepath, buffer, sizeof(buffer) - 1);
    if (bytes < 0) {
        api->print("Hata: Dosya bulunamadi veya okunamadi!\\n");
        return;
    }

    if (bytes >= (int)sizeof(buffer)) {
        bytes = (int)sizeof(buffer) - 1;
    }
    buffer[bytes] = '\\0';

    api->print(buffer);

    // Eğer dosyanın son karakteri yeni satır (\\n) değilse otomatik ekle
    if (bytes > 0 && buffer[bytes - 1] != '\\n') {
        api->print("\\n");
    }
}
"""
    with open(os.path.join(src_dir, "main.c"), "w", encoding="utf-8") as f:
        f.write(main_c_code)

    # 5. kvx.json Manifest
    kvx_json_data = {
        "name": name,
        "type": "command",
        "sub_type": "user_bin",
        "version": version,
        "author": author,
        "compiler_flags": "-m32 -ffreestanding -fno-pie -fno-stack-protector -Wall -Wextra",
        "linker_flags": "-m32 -nostdlib -no-pie -T linker.ld"
    }
    with open(os.path.join(target_dir, "kvx.json"), "w", encoding="utf-8") as f:
        json.dump(kvx_json_data, f, indent=4, ensure_ascii=False)

    print(f"Başarılı: '{name}' harici komut projesi başarıyla oluşturuldu.")
    return True