import os
import json

def create_new_project(path, name, version, author):
    target_dir = os.path.abspath(os.path.join(path, name))

    if os.path.exists(target_dir):
        print(f"Hata: '{target_dir}' dizini zaten mevcut!")
        return False

    src_dir = os.path.join(target_dir, "src")
    runtime_dir = os.path.join(src_dir, "runtime")
    vscode_dir = os.path.join(target_dir, ".vscode")

    os.makedirs(runtime_dir, exist_ok=True)
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
                    "name": "KuvixOS Login",
                    "includePath": [
                        "${workspaceFolder}/**",
                        f"{sdk_path}/include/**"
                    ],
                    "defines": [],
                    "compilerPath": "/usr/bin/i686-elf-g++",
                    "cStandard": "c17",
                    "cppStandard": "c++17",
                    "intelliSenseMode": "linux-gcc-x86"
                }
            ],
            "version": 4
        }
        with open(os.path.join(vscode_dir, "c_cpp_properties.json"), "w", encoding="utf-8") as f:
            json.dump(c_cpp_properties_content, f, indent=4, ensure_ascii=False)

    # 2. linker.ld
    linker_content = """ENTRY(_start)

SECTIONS
{
    . = 0x3000000;

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

    # 3. src/runtime/entry.s
    entry_s_code = """.global _start
.extern app_main

.section .text._start
_start:
    pushl 4(%esp)
    call app_main
    addl $4, %esp

.loop:
    cli
    hlt
    jmp .loop
"""
    with open(os.path.join(runtime_dir, "entry.s"), "w", encoding="utf-8") as f:
        f.write(entry_s_code)

    # 4. src/login_runtime.cpp
    login_runtime_code = """#include <login_api.h>
#include <stddef.h>

static LoginAPI* s_login_api = nullptr;

// Freestanding ortam için gerekli new / delete tanımları
void* operator new(size_t size) {
    return nullptr;
}

void* operator new[](size_t size) {
    return nullptr;
}

void operator delete(void* ptr, size_t size) noexcept {
}

void operator delete(void* ptr) noexcept {
}

void operator delete[](void* ptr) noexcept {
}

extern "C" {
    void __login_runtime_init(LoginAPI* api) {
        s_login_api = api;
    }

    LoginAPI* get_login_api(void) {
        return s_login_api;
    }
}
"""
    with open(os.path.join(src_dir, "login_runtime.cpp"), "w", encoding="utf-8") as f:
        f.write(login_runtime_code)

    # 5. src/main.cpp
    main_code = """#include <login_api.h>
#include <widget.hpp>

extern "C" void __login_runtime_init(LoginAPI* api);

extern "C" {
    int app_main(LoginAPI* api) {
        if (api) {
            __login_runtime_init(api);
        }

        LoginAPI* current_api = get_login_api();
        if (!current_api) {
            while (1) { __asm__("hlt"); }
        }

        if (current_api->log) {
            current_api->log("[DEFAULT LOGIN] Etkilesimli giris ekrani baslatildi.\\n");
        }

        InputField username_input("username_field", 200, 150, 240, 35);

        login_mouse_state_t mouse;
        uint8_t prev_left_button = 0;

        while (1) {
            if (current_api->get_mouse) {
                current_api->get_mouse(&mouse);
            }

            if (current_api->get_key) {
                char c = current_api->get_key();
                if (c != 0) {
                    username_input.handle_key(c);
                }
            }

            username_input.update_click(mouse.x, mouse.y, mouse.left_button, prev_left_button);
            prev_left_button = mouse.left_button;

            if (current_api->clear_screen) {
                current_api->clear_screen(0x0000FF);
            }

            if (current_api->draw_text) {
                current_api->draw_text(200, 100, "KuvixOS Oturum Acma", 0xFFFFFF);
            }

            username_input.draw_login(current_api);

            if (current_api->render_kbi) {
                current_api->render_kbi(mouse.x, mouse.y, "/sys/themes/arrow-cursor.kbi");
            }

            if (current_api->update_display) {
                current_api->update_display();
            }

            for (volatile int i = 0; i < 5000; i++);
        }
        
        return 0;
    }
}
"""
    with open(os.path.join(src_dir, "main.cpp"), "w", encoding="utf-8") as f:
        f.write(main_code)

    # 6. kvx.json Manifest
    kvx_json_data = {
        "name": name,
        "type": "login_screen",
        "sub_type": "kernel",
        "version": version,
        "author": author,
        "compiler_flags": "-O2 -Wall -Wextra -m32 -ffreestanding",
        "linker_flags": "-m elf_i386 -N -e _start -T linker.ld"
    }
    with open(os.path.join(target_dir, "kvx.json"), "w", encoding="utf-8") as f:
        json.dump(kvx_json_data, f, indent=4, ensure_ascii=False)

    print(f"Başarılı: '{name}' login_screen projesi istenen yapıda oluşturuldu.")
    return True