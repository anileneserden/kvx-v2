import os
import json

def create_new_project(path, name, version, author):
    target_dir = os.path.abspath(os.path.join(path, name))

    if os.path.exists(target_dir):
        print(f"Hata: '{target_dir}' dizini zaten mevcut!")
        return False

    src_dir = os.path.join(target_dir, "src")
    include_dir = os.path.join(target_dir, "include")
    runtime_dir = os.path.join(src_dir, "runtime")
    lib_dir = os.path.join(src_dir, "lib")
    vscode_dir = os.path.join(target_dir, ".vscode")

    os.makedirs(runtime_dir, exist_ok=True)
    os.makedirs(include_dir, exist_ok=True)
    os.makedirs(lib_dir, exist_ok=True)
    os.makedirs(vscode_dir, exist_ok=True)

    # 1. .vscode/c_cpp_properties.json (Konfigürasyona göre dinamik oluşturma)
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
                    "name": "KuvixOS",
                    "includePath": [
                        "${workspaceFolder}/**",
                        "${workspaceFolder}/include/**",
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
    else:
        # Eğer editör ayarı "none" ise boş bırakabilir veya varsayılan bir şablon yazabilirsiniz
        pass

    # 2. linker.ld
    linker_content = """ENTRY(_start)

SECTIONS
{
    . = 0x3000000; /* 48 MB adresi (Kernel Heap'in üstünde, RAM sınırları içinde) */

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

    # 3. entry.s
    entry_s_code = """.global _start
.extern app_main

.section .text._start
_start:
    # cdecl: Loader 'call' ile çağırdıysa [esp + 4] konumundaki DE_API* pointer'ını aktar
    pushl 4(%esp)
    call app_main
    addl $4, %esp

    # app_main geri dönerse işlemciyi güvenli döngüye al (Triple Fault'u önler)
.loop:
    cli
    hlt
    jmp .loop
"""
    with open(os.path.join(runtime_dir, "entry.s"), "w", encoding="utf-8") as f:
        f.write(entry_s_code)

    # 4. Runtime.cpp
    runtime_code = """#include <stdint.h>
#include <stddef.h>

extern "C" {
    void __cxa_pure_virtual() { while (1) { asm volatile("hlt"); } }
    int __cxa_atexit(void (*destructor)(void *), void *arg, void *dso_handle) {
        (void)destructor; (void)arg; (void)dso_handle;
        return 0;
    }
    void* __dso_handle = 0;
}

void operator delete(void*, size_t) noexcept {}
void operator delete(void*) noexcept {}
"""
    with open(os.path.join(runtime_dir, "Runtime.cpp"), "w", encoding="utf-8") as f:
        f.write(runtime_code)

    # 5. include/draw_text.hpp
    hpp_draw_code = r"""#ifndef DRAW_TEXT_HPP
#define DRAW_TEXT_HPP

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

#define AUTO_STR(str_val) ({ \
    const char* __ptr; \
    asm volatile ( \
        "call 1f\n\t" \
        ".asciz \"" str_val "\"\n\t" \
        "1:\n\t" \
        "pop %0\n\t" \
        : "=r"(__ptr) \
    ); \
    __ptr; \
})

void draw_text_safe_internal(DE_API* api, int x, int y, const char* str, uint32_t color);

#define draw_text_safe(api, x, y, str, color) \
    draw_text_safe_internal(api, x, y, AUTO_STR(str), color)

#endif
"""
    with open(os.path.join(include_dir, "draw_text.hpp"), "w", encoding="utf-8") as f:
        f.write(hpp_draw_code)

    # 6. include/input.h
    hpp_input_code = """#ifndef INPUT_H
#define INPUT_H

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

enum KeyCode : uint8_t {
    KEY_NONE      = 0x00,
    KEY_ENTER     = 0x0D,
    KEY_ESCAPE    = 0x1B,
    KEY_BACKSPACE = 0x08,
    KEY_LCTRL     = 0x1D,
    KEY_LSHIFT    = 0x2A,
    KEY_RSHIFT    = 0x36,
    KEY_LALT      = 0x38,
    KEY_SUPER     = 0x5B
};

enum KeyModifier : uint8_t {
    MOD_NONE  = 0,
    MOD_SHIFT = 1 << 0,
    MOD_CTRL  = 1 << 1,
    MOD_ALT   = 1 << 2,
    MOD_SUPER = 1 << 3
};

class Input {
private:
    static uint8_t modifiers;
    static bool keys[256];

public:
    static void poll(DE_API* api);
    static bool is_key_down(uint8_t key);
    static bool is_ctrl();
    static bool is_shift();
    static bool is_alt();
    static bool is_super();
    static bool is_combo(uint8_t modifier_flags, uint8_t key);
};

#endif
"""
    with open(os.path.join(include_dir, "input.h"), "w", encoding="utf-8") as f:
        f.write(hpp_input_code)

    # 7. include/cursor.h
    hpp_cursor_code = """#ifndef LIB_CURSOR_H
#define LIB_CURSOR_H

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

typedef struct {
    int old_x;
    int old_y;
    int width;
    int height;
    uint32_t bg_color;
    const char* path;
} CursorState;

void cursor_init(CursorState* state, const char* path, int w, int h, uint32_t bg_color);
void cursor_render(DE_API* api, CursorState* state);

#endif
"""
    with open(os.path.join(include_dir, "cursor.h"), "w", encoding="utf-8") as f:
        f.write(hpp_cursor_code)

    # 8. include/window.hpp
    hpp_window_code = """#ifndef WINDOW_HPP
#define WINDOW_HPP

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

struct WindowTheme {
    uint32_t bg_color;
    uint32_t header_color;
    uint32_t active_header_color;
    uint32_t border_color;
    int border_thickness;
    int header_height;
};

class Window {
public:
    int x, y;
    int width, height;
    int dragging;
    int drag_offset_x, drag_offset_y;
    int is_open;

    WindowTheme theme;

    Window(int wx, int wy, int ww, int wh, WindowTheme custom_theme)  
        : x(wx), y(wy), width(ww), height(wh),  
          dragging(0), drag_offset_x(0), drag_offset_y(0), is_open(1),
          theme(custom_theme) {}

    void update(const de_mouse_state_t& mouse) {
        if (!is_open) return;

        if (mouse.left_button == 1) {
            if (dragging == 0) {
                if (mouse.x >= x && mouse.x <= (x + width) &&
                    mouse.y >= y && mouse.y <= (y + theme.header_height)) {
                    
                    int close_x = x + width - theme.header_height;
                    if (mouse.x >= close_x && mouse.x <= (x + width)) {
                        is_open = 0;
                        return;
                    }

                    dragging = 1;
                    drag_offset_x = mouse.x - x;
                    drag_offset_y = mouse.y - y;
                }
            } else {
                int new_x = mouse.x - drag_offset_x;
                int new_y = mouse.y - drag_offset_y;

                if (new_x < 0) new_x = 0;
                if (new_y < 0) new_y = 0;
                if (new_x > 1920 - width) new_x = 1920 - width;
                if (new_y > 1080 - height) new_y = 1080 - height;

                x = new_x;
                y = new_y;
            }
        } else {
            dragging = 0;
        }
    }

    void draw(DE_API* api) {
        if (!is_open || !api || !api->draw_rect) return;

        int t = theme.border_thickness;
        api->draw_rect(x - t, y - t, width + (t * 2), height + (t * 2), theme.border_color);
        api->draw_rect(x, y, width, height, theme.bg_color);

        uint32_t current_header = (dragging == 1) ? theme.active_header_color : theme.header_color;
        api->draw_rect(x, y, width, theme.header_height, current_header);

        int btn_size = 14;
        int btn_x = x + width - theme.header_height + (theme.header_height - btn_size) / 2;
        int btn_y = y + (theme.header_height - btn_size) / 2;
        api->draw_rect(btn_x, btn_y, btn_size, btn_size, 0x00E63946);
    }
};

#endif // WINDOW_HPP
"""
    with open(os.path.join(include_dir, "window.hpp"), "w", encoding="utf-8") as f:
        f.write(hpp_window_code)

    # 9. include/grid.hpp
    hpp_grid_code = """#ifndef GRID_HPP
#define GRID_HPP

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

void draw_grid_lines(DE_API* api, uint32_t screen_width, uint32_t screen_height, int cell_size, uint32_t grid_color);

#endif
"""
    with open(os.path.join(include_dir, "grid.hpp"), "w", encoding="utf-8") as f:
        f.write(hpp_grid_code)

    # 10. include/widget.hpp
    hpp_widget_code = """#ifndef WIDGET_HPP
#define WIDGET_HPP

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

enum WidgetType {
    WIDGET_LABEL,
    WIDGET_BUTTON
};

class Widget {
public:
    WidgetType type;
    int x, y;
    int width, height;
    uint32_t background_color;
    uint32_t color;
    int border_radius;
    char text[64];

    Widget(WidgetType t, int px, int py, int pw, int ph, uint32_t bg, uint32_t fg, int radius, const char* txt);
    virtual ~Widget() {}

    virtual void draw(DE_API* api);
};

class Label : public Widget {
public:
    Label(int px, int py, uint32_t fg, const char* txt);
    void draw(DE_API* api) override;
};

class Button : public Widget {
public:
    Button(int px, int py, int pw, int ph, uint32_t bg, uint32_t fg, int radius, const char* txt);
    void draw(DE_API* api) override;
};

#endif
"""
    with open(os.path.join(include_dir, "widget.hpp"), "w", encoding="utf-8") as f:
        f.write(hpp_widget_code)

    # 11. src/lib/draw_text.cpp
    cpp_draw_code = r"""#include "../../include/draw_text.hpp"

void draw_text_safe_internal(DE_API* api, int x, int y, const char* str, uint32_t color) {
    if (!api || !api->draw_text || !str) return;

    int len = 0;
    while (str[len] != '\0' && len < 255) {
        len++;
    }

    if (len == 0) return;

    char reversed[256];
    for (int i = 0; i < len; i++) {
        reversed[i] = str[len - 1 - i];
    }
    reversed[len] = '\0';

    api->draw_text(x, y, reversed, color);
}
"""
    with open(os.path.join(lib_dir, "draw_text.cpp"), "w", encoding="utf-8") as f:
        f.write(cpp_draw_code)

    # 12. src/lib/input.cpp
    cpp_input_code = """#include "../../include/input.h"

uint8_t Input::modifiers = MOD_NONE;
bool Input::keys[256] = { false };

void Input::poll(DE_API* api) {
    if (!api || !api->get_key) return;

    for (int i = 0; i < 16; i++) {
        char raw = api->get_key();
        uint8_t code = (uint8_t)raw;

        if (code == 0 || code == 0xFF) {
            break;
        }

        bool is_release = (code & 0x80) != 0;
        uint8_t key = code & 0x7F;

        keys[key] = !is_release;

        if (key == KEY_LCTRL) {
            if (is_release) modifiers &= ~MOD_CTRL;
            else            modifiers |= MOD_CTRL;
        }
        else if (key == KEY_LSHIFT || key == KEY_RSHIFT) {
            if (is_release) modifiers &= ~MOD_SHIFT;
            else            modifiers |= MOD_SHIFT;
        }
        else if (key == KEY_LALT) {
            if (is_release) modifiers &= ~MOD_ALT;
            else            modifiers |= MOD_ALT;
        }
        else if (key == KEY_SUPER) {
            if (is_release) modifiers &= ~MOD_SUPER;
            else            modifiers |= MOD_SUPER;
        }
    }
}

bool Input::is_key_down(uint8_t key) { return keys[key]; }
bool Input::is_ctrl()                { return (modifiers & MOD_CTRL) != 0; }
bool Input::is_shift()               { return (modifiers & MOD_SHIFT) != 0; }
bool Input::is_alt()                 { return (modifiers & MOD_ALT) != 0; }
bool Input::is_super()               { return (modifiers & MOD_SUPER) != 0; }

bool Input::is_combo(uint8_t modifier_flags, uint8_t key) {
    return (modifiers == modifier_flags) && keys[key];
}
"""
    with open(os.path.join(lib_dir, "input.cpp"), "w", encoding="utf-8") as f:
        f.write(cpp_input_code)

    # 13. src/lib/cursor.cpp
    cpp_cursor_code = """#include "../../include/cursor.h"

void cursor_init(CursorState* state, const char* path, int w, int h, uint32_t bg_color) {
    state->path = path;
    state->width = w;
    state->height = h;
    state->bg_color = bg_color;
    state->old_x = -9999;
    state->old_y = -9999;
}

void cursor_render(DE_API* api, CursorState* state) {
    de_mouse_state_t mouse;
    api->get_mouse(&mouse);

    if (mouse.x != state->old_x || mouse.y != state->old_y) {
        if (state->old_x != -9999) {
            api->draw_rect(state->old_x, state->old_y, state->width, state->height, state->bg_color);
            api->dmg_union_replace(state->old_x, state->old_y, state->old_x + state->width, state->old_y + state->height);
        }

        // 3 parametreli orijinal imza kullanıldı (w ve h parametreleri kaldırıldı)
        api->render_kbi(mouse.x, mouse.y, state->path);
        api->dmg_union_replace(mouse.x, mouse.y, mouse.x + state->width, mouse.y + state->height);

        state->old_x = mouse.x;
        state->old_y = mouse.y;
    }
}
"""
    with open(os.path.join(lib_dir, "cursor.cpp"), "w", encoding="utf-8") as f:
        f.write(cpp_cursor_code)

    # 14. src/lib/grid.cpp
    cpp_grid_code = """#include <grid.hpp>

void draw_grid_lines(DE_API* api, uint32_t screen_width, uint32_t screen_height, int cell_size, uint32_t grid_color) {
    if (!api || !api->draw_rect || cell_size <= 0) return;

    for (int x = 0; x <= screen_width; x += cell_size) {
        api->draw_rect(x, 0, 1, screen_height, grid_color);
    }

    for (int y = 0; y <= screen_height; y += cell_size) {
        api->draw_rect(0, y, screen_width, 1, grid_color);
    }
}
"""
    with open(os.path.join(lib_dir, "grid.cpp"), "w", encoding="utf-8") as f:
        f.write(cpp_grid_code)

    # 15. src/main.cpp
    main_code = r"""#include <kernel/drivers/video/de_api.h>
#include <grid.hpp>
#include <window.hpp>
#include <widget.hpp>

extern "C" void app_main(DE_API* api) {
    if (!api) return;

    if (api->get_file_count && api->get_file_name_at && api->log) {
        const char* target_dir = "/usr/share/applications";
        int file_count = api->get_file_count(target_dir);
        
        for (int i = 0; i < file_count; i++) {
            char filename[32];
            if (api->get_file_name_at(target_dir, i, filename, sizeof(filename))) {
                // Dosya işleme döngüsü
            }
        }
    }

    WindowTheme current_theme = {
        .bg_color = 0x002B2D42,
        .header_color = 0x001D1E2C,
        .active_header_color = 0x003D405B,
        .border_color = 0x004A4E69,
        .border_thickness = 2,
        .header_height = 24
    };

    uint32_t bg_color   = current_theme.bg_color;
    uint32_t grid_color = 0x003D405B;
    int cell_size       = 100;
    bool show_grid = true;

    // Window win(100, 100, 800, 500, current_theme);

    // Label my_label(30, 40, 0x00E0E0E0, "Merhaba KuvixOS");
    //Button my_button(30, 80, 160, 45, 0x003D405B, 0x00FFFFFF, 4, "Tikla");

    de_mouse_state_t mouse = {0, 0, 0, 0, 0};

    if (api->clear_screen) {
        api->clear_screen(bg_color);
    }
    if (api->update_display) {
        api->update_display();
    }

    while (true) {
        if (api->clear_screen) {
            api->clear_screen(bg_color);
        }

        if (api->get_mouse) {
            api->get_mouse(&mouse);
            // win.update(mouse);
        }

        if (api->get_key) {
            char k = api->get_key();
            if (k == 27) break; // ESC ile çıkış
            
            if (k == 'g' || k == 'G') {
                show_grid = !show_grid;
            }
        }

        if (show_grid) {
            draw_grid_lines(api, 1920, 1080, cell_size, grid_color);
        }

        //if (win.is_open) {
        //    win.draw(api);
        //
        //    my_label.x = win.x + 30;
        //    my_label.y = win.y + 40;
        //    my_label.draw(api);
        //
        //    my_button.x = win.x + 30;
        //    my_button.y = win.y + 80;
        //    my_button.draw(api);
        //}

        if (api->render_kbi) {
            api->render_kbi(mouse.x, mouse.y, "/sys/themes/arrow-cursor.kbi");
        }

        if (api->update_display) {
            api->update_display();
        }
    }
}
"""
    with open(os.path.join(src_dir, "main.cpp"), "w", encoding="utf-8") as f:
        f.write(main_code)

    # 16. src/lib/widget.cpp
    cpp_widget_code = """#include <widget.hpp>

Widget::Widget(WidgetType t, int px, int py, int pw, int ph, uint32_t bg, uint32_t fg, int radius, const char* txt)
    : type(t), x(px), y(py), width(pw), height(ph), background_color(bg), color(fg), border_radius(radius) {
    int i = 0;
    while (txt[i] != '\\0' && i < 63) {
        text[i] = txt[i];
        i++;
    }
    text[i] = '\\0';
}

void Widget::draw(DE_API*) {}

Label::Label(int px, int py, uint32_t fg, const char* txt)
    : Widget(WIDGET_LABEL, px, py, 0, 0, 0, fg, 0, txt) {}

void Label::draw(DE_API* api) {
    if (!api || !api->draw_text) return;
    api->draw_text(x, y, text, color);
}

Button::Button(int px, int py, int pw, int ph, uint32_t bg, uint32_t fg, int radius, const char* txt)
    : Widget(WIDGET_BUTTON, px, py, pw, ph, bg, fg, radius, txt) {}

void Button::draw(DE_API* api) {
    if (!api || !api->draw_rect) return;
    api->draw_rect(x, y, width, height, background_color);
    if (api->draw_text) {
        api->draw_text(x + 12, y + (height - 8) / 2, text, color);
    }
}
"""
    with open(os.path.join(lib_dir, "widget.cpp"), "w", encoding="utf-8") as f:
        f.write(cpp_widget_code)

    # kvx.json Manifest
    kvx_json_data = {
        "name": name,
        "type": "de",
        "sub_type": "kernel",
        "version": version,
        "author": author,
        "compiler_flags": "-O2 -Wall -Wextra -m32 -ffreestanding",
        "linker_flags": "-m elf_i386 -N -e _start -T linker.ld"
    }
    with open(os.path.join(target_dir, "kvx.json"), "w", encoding="utf-8") as f:
        json.dump(kvx_json_data, f, indent=4, ensure_ascii=False)

    print(f"Başarılı: '{name}' DE projesi SDK ve UI bileşenleriyle oluşturuldu.")
    return True