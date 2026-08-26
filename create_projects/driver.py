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
                    "name": "KuvixOS-Driver",
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

    # 2. linker.ld (KDF Sürücü Linker Betiği)
    linker_content = """ENTRY(driver_init)

SECTIONS
{
    . = 0x00000000;

    .text : {
        *(.text._start)
        *(.text*)
    }

    .rodata : {
        *(.rodata*)
    }

    .data : {
        *(.data*)
    }

    .bss : {
        *(.bss*)
    }
}
"""
    with open(os.path.join(target_dir, "linker.ld"), "w", encoding="utf-8") as f:
        f.write(linker_content)

    # 3. src/main.cpp (KDF yapıları ve sürücü kodunu tek dosyada barındırır)
    main_c_code = """#include <stdint.h>

#define KDF_MAGIC 0x46444B4B 

// Sürücüye teslim edilecek canlı kernel servisleri
typedef struct {
    void (*printk)(const char* fmt, ...);
    uint8_t (*inb)(uint16_t port);
    void (*outb)(uint16_t port, uint8_t data);
    void (*register_interrupt)(int irq, void (*handler)(void));
} KernelAPI;

// JENERİK SÜRÜCÜ OPERASYONLARI
typedef struct {
    int (*read)(void* buffer, uint32_t size);
    int (*write)(const void* buffer, uint32_t size);
    int (*control)(const char* command, void* arg, uint32_t arg_size);
} KDF_Operations;

typedef struct {
    uint32_t magic;           
    uint32_t driver_version;  
    char     driver_name[32]; 
    uint32_t init_offset;     
    uint32_t exit_offset;     
    uint32_t code_size;       
} __attribute__((packed)) KDF_Header;

// Kernel servislerine referans
static KernelAPI* g_kapi = 0;

static int my_driver_read(void* buffer, uint32_t size) {
    (void)buffer;
    (void)size;
    return 0;
}

static int my_driver_write(const void* buffer, uint32_t size) {
    (void)buffer;
    (void)size;
    return 0;
}

static int my_driver_control(const char* command, void* arg, uint32_t arg_size) {
    (void)command;
    (void)arg;
    (void)arg_size;
    return 0;
}

// Sürücü Giriş Noktası
extern "C" int driver_init(KernelAPI* kapi, KDF_Operations* ops) {
    g_kapi = kapi;

    if (g_kapi && g_kapi->printk) {
        g_kapi->printk("[KDF] Ornek surucu basariyla baslatildi!\\n");
    }

    if (ops) {
        ops->read = my_driver_read;
        ops->write = my_driver_write;
        ops->control = my_driver_control;
    }

    return 1; // Başarılı
}

// Sürücü Çıkış Noktası
extern "C" void driver_exit(void) {
    if (g_kapi && g_kapi->printk) {
        g_kapi->printk("[KDF] Ornek surucu kaldiriliyor...\\n");
    }
}
"""
    with open(os.path.join(src_dir, "main.cpp"), "w", encoding="utf-8") as f:
        f.write(main_c_code)

    # 4. kvx.json Manifest
    kvx_json_data = {
        "name": name,
        "type": "driver",
        "sub_type": "kdf",
        "version": version,
        "author": author,
        "compiler_flags": "-O2 -Wall -Wextra -m32 -ffreestanding -fno-pie -nostdlib",
        "linker_flags": "-m elf_i386 -nostdlib -T linker.ld"
    }
    with open(os.path.join(target_dir, "kvx.json"), "w", encoding="utf-8") as f:
        json.dump(kvx_json_data, f, indent=4, ensure_ascii=False)

    print(f"Başarılı: '{name}' KDF sürücü projesi (include klasörsüz) başarıyla oluşturuldu.")
    return True