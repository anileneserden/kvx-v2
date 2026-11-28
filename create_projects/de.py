import os
import json


def create_new_project(path, name, version, author, output_file=None):
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
                    "name": "KuvixOS",
                    "includePath": [
                        "${workspaceFolder}/**",
                        "${workspaceFolder}/include/**",
                        f"{sdk_path}/include/**"
                    ],
                    "defines": [],
                    "compilerPath": "/usr/bin/i686-elf-gcc",
                    "cStandard": "gnu11",
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

    # 4. include/draw_text.h
    h_draw_code = r"""#ifndef DRAW_TEXT_H
#define DRAW_TEXT_H

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

#define AUTO_STR(str_val) ({ \
    const char* __ptr; \
    __asm__ __volatile__ ( \
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
    with open(os.path.join(include_dir, "draw_text.h"), "w", encoding="utf-8") as f:
        f.write(h_draw_code)

    # 5. include/input.h
    h_input_code = """#ifndef INPUT_H
#define INPUT_H

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>
#include <stdbool.h>

typedef enum {
    KEY_NONE      = 0x00,
    KEY_ENTER     = 0x0D,
    KEY_ESCAPE    = 0x1B,
    KEY_BACKSPACE = 0x08,
    KEY_LCTRL     = 0x1D,
    KEY_LSHIFT    = 0x2A,
    KEY_RSHIFT    = 0x36,
    KEY_LALT      = 0x38,
    KEY_SUPER     = 0x5B
} KeyCode;

typedef enum {
    MOD_NONE  = 0,
    MOD_SHIFT = 1 << 0,
    MOD_CTRL  = 1 << 1,
    MOD_ALT   = 1 << 2,
    MOD_SUPER = 1 << 3
} KeyModifier;

void input_init(void);
void input_poll(DE_API* api);
bool input_is_key_down(uint8_t key);
bool input_is_ctrl(void);
bool input_is_shift(void);
bool input_is_alt(void);
bool input_is_super(void);
bool input_is_combo(uint8_t modifier_flags, uint8_t key);

#endif
"""
    with open(os.path.join(include_dir, "input.h"), "w", encoding="utf-8") as f:
        f.write(h_input_code)

    # 6. include/cursor.h
    h_cursor_code = """#ifndef LIB_CURSOR_H
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
        f.write(h_cursor_code)

    # 7. include/window.h
    h_window_code = """#ifndef WINDOW_H
#define WINDOW_H

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

typedef struct {
    uint32_t bg_color;
    uint32_t header_color;
    uint32_t active_header_color;
    uint32_t border_color;
    int border_thickness;
    int header_height;
} WindowTheme;

typedef struct {
    int x;
    int y;
    int width;
    int height;
    int dragging;
    int drag_offset_x;
    int drag_offset_y;
    int is_open;
    WindowTheme theme;
} Window;

void window_init(Window* win, int wx, int wy, int ww, int wh, WindowTheme custom_theme);
void window_update(Window* win, const de_mouse_state_t* mouse);
void window_draw(const Window* win, DE_API* api);

#endif
"""
    with open(os.path.join(include_dir, "window.h"), "w", encoding="utf-8") as f:
        f.write(h_window_code)

    # 8. include/grid.h
    h_grid_code = """#ifndef GRID_H
#define GRID_H

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

void draw_grid_lines(DE_API* api, int screen_width, int screen_height, int cell_size, uint32_t grid_color);

#endif
"""
    with open(os.path.join(include_dir, "grid.h"), "w", encoding="utf-8") as f:
        f.write(h_grid_code)

    # 9. include/widget.h
    h_widget_code = """#ifndef WIDGET_H
#define WIDGET_H

#include <kernel/drivers/video/de_api.h>
#include <stdint.h>

typedef enum {
    WIDGET_LABEL,
    WIDGET_BUTTON
} WidgetType;

typedef struct {
    WidgetType type;
    int x;
    int y;
    int width;
    int height;
    uint32_t background_color;
    uint32_t color;
    int border_radius;
    char text[64];
} Widget;

Widget widget_make_label(int px, int py, uint32_t fg, const char* txt);
Widget widget_make_button(int px, int py, int pw, int ph, uint32_t bg, uint32_t fg, int radius, const char* txt);
void widget_draw(const Widget* w, DE_API* api);

#endif
"""
    with open(os.path.join(include_dir, "widget.h"), "w", encoding="utf-8") as f:
        f.write(h_widget_code)

    # 10. src/lib/draw_text.c
    c_draw_code = r"""#include "draw_text.h"

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
    with open(os.path.join(lib_dir, "draw_text.c"), "w", encoding="utf-8") as f:
        f.write(c_draw_code)

    # 11. src/lib/input.c
    c_input_code = """#include "input.h"

static uint8_t g_modifiers = MOD_NONE;
static bool g_keys[256] = { false };

void input_init(void) {
    g_modifiers = MOD_NONE;
    for (int i = 0; i < 256; i++) {
        g_keys[i] = false;
    }
}

void input_poll(DE_API* api) {
    if (!api || !api->get_key) return;

    for (int i = 0; i < 16; i++) {
        char raw = api->get_key();
        uint8_t code = (uint8_t)raw;

        if (code == 0 || code == 0xFF) {
            break;
        }

        bool is_release = (code & 0x80) != 0;
        uint8_t key = code & 0x7F;

        g_keys[key] = !is_release;

        if (key == KEY_LCTRL) {
            if (is_release) g_modifiers &= ~MOD_CTRL;
            else            g_modifiers |= MOD_CTRL;
        } else if (key == KEY_LSHIFT || key == KEY_RSHIFT) {
            if (is_release) g_modifiers &= ~MOD_SHIFT;
            else            g_modifiers |= MOD_SHIFT;
        } else if (key == KEY_LALT) {
            if (is_release) g_modifiers &= ~MOD_ALT;
            else            g_modifiers |= MOD_ALT;
        } else if (key == KEY_SUPER) {
            if (is_release) g_modifiers &= ~MOD_SUPER;
            else            g_modifiers |= MOD_SUPER;
        }
    }
}

bool input_is_key_down(uint8_t key) { return g_keys[key]; }
bool input_is_ctrl(void)           { return (g_modifiers & MOD_CTRL) != 0; }
bool input_is_shift(void)          { return (g_modifiers & MOD_SHIFT) != 0; }
bool input_is_alt(void)            { return (g_modifiers & MOD_ALT) != 0; }
bool input_is_super(void)          { return (g_modifiers & MOD_SUPER) != 0; }

bool input_is_combo(uint8_t modifier_flags, uint8_t key) {
    return (g_modifiers == modifier_flags) && g_keys[key];
}
"""
    with open(os.path.join(lib_dir, "input.c"), "w", encoding="utf-8") as f:
        f.write(c_input_code)

    # 12. src/lib/cursor.c
    c_cursor_code = """#include "cursor.h"

void cursor_init(CursorState* state, const char* path, int w, int h, uint32_t bg_color) {
    if (!state) return;
    state->path = path;
    state->width = w;
    state->height = h;
    state->bg_color = bg_color;
    state->old_x = -9999;
    state->old_y = -9999;
}

void cursor_render(DE_API* api, CursorState* state) {
    if (!api || !state || !api->get_mouse) return;

    de_mouse_state_t mouse;
    api->get_mouse(&mouse);

    if (mouse.x != state->old_x || mouse.y != state->old_y) {
        if (state->old_x != -9999 && api->draw_rect && api->dmg_union_replace) {
            api->draw_rect(state->old_x, state->old_y, state->width, state->height, state->bg_color);
            api->dmg_union_replace(state->old_x, state->old_y, state->old_x + state->width, state->old_y + state->height);
        }

        if (api->render_kbi) {
            api->render_kbi(mouse.x, mouse.y, state->path);
        }
        if (api->dmg_union_replace) {
            api->dmg_union_replace(mouse.x, mouse.y, mouse.x + state->width, mouse.y + state->height);
        }

        state->old_x = mouse.x;
        state->old_y = mouse.y;
    }
}
"""
    with open(os.path.join(lib_dir, "cursor.c"), "w", encoding="utf-8") as f:
        f.write(c_cursor_code)

    # 13. src/lib/grid.c
    c_grid_code = """#include "grid.h"

void draw_grid_lines(DE_API* api, int screen_width, int screen_height, int cell_size, uint32_t grid_color) {
    if (!api || !api->draw_rect || cell_size <= 0) return;

    for (int x = 0; x <= screen_width; x += cell_size) {
        api->draw_rect(x, 0, 1, screen_height, grid_color);
    }

    for (int y = 0; y <= screen_height; y += cell_size) {
        api->draw_rect(0, y, screen_width, 1, grid_color);
    }
}
"""
    with open(os.path.join(lib_dir, "grid.c"), "w", encoding="utf-8") as f:
        f.write(c_grid_code)

    # 14. src/lib/window.c
    c_window_code = """#include "window.h"

void window_init(Window* win, int wx, int wy, int ww, int wh, WindowTheme custom_theme) {
    if (!win) return;
    win->x = wx;
    win->y = wy;
    win->width = ww;
    win->height = wh;
    win->dragging = 0;
    win->drag_offset_x = 0;
    win->drag_offset_y = 0;
    win->is_open = 1;
    win->theme = custom_theme;
}

void window_update(Window* win, const de_mouse_state_t* mouse) {
    if (!win || !mouse || !win->is_open) return;

    if (mouse->left_button == 1) {
        if (win->dragging == 0) {
            if (mouse->x >= win->x && mouse->x <= (win->x + win->width) &&
                mouse->y >= win->y && mouse->y <= (win->y + win->theme.header_height)) {
                int close_x = win->x + win->width - win->theme.header_height;
                if (mouse->x >= close_x && mouse->x <= (win->x + win->width)) {
                    win->is_open = 0;
                    return;
                }

                win->dragging = 1;
                win->drag_offset_x = mouse->x - win->x;
                win->drag_offset_y = mouse->y - win->y;
            }
        } else {
            int new_x = mouse->x - win->drag_offset_x;
            int new_y = mouse->y - win->drag_offset_y;

            if (new_x < 0) new_x = 0;
            if (new_y < 0) new_y = 0;
            if (new_x > 1920 - win->width) new_x = 1920 - win->width;
            if (new_y > 1080 - win->height) new_y = 1080 - win->height;

            win->x = new_x;
            win->y = new_y;
        }
    } else {
        win->dragging = 0;
    }
}

void window_draw(const Window* win, DE_API* api) {
    if (!win || !win->is_open || !api || !api->draw_rect) return;

    int t = win->theme.border_thickness;
    api->draw_rect(win->x - t, win->y - t, win->width + (t * 2), win->height + (t * 2), win->theme.border_color);
    api->draw_rect(win->x, win->y, win->width, win->height, win->theme.bg_color);

    uint32_t current_header = (win->dragging == 1) ? win->theme.active_header_color : win->theme.header_color;
    api->draw_rect(win->x, win->y, win->width, win->theme.header_height, current_header);

    int btn_size = 14;
    int btn_x = win->x + win->width - win->theme.header_height + (win->theme.header_height - btn_size) / 2;
    int btn_y = win->y + (win->theme.header_height - btn_size) / 2;
    api->draw_rect(btn_x, btn_y, btn_size, btn_size, 0x00E63946);
}
"""
    with open(os.path.join(lib_dir, "window.c"), "w", encoding="utf-8") as f:
        f.write(c_window_code)

    # 15. src/lib/widget.c
    c_widget_code = """#include "widget.h"

Widget widget_make_label(int px, int py, uint32_t fg, const char* txt) {
    Widget w;
    w.type = WIDGET_LABEL;
    w.x = px;
    w.y = py;
    w.width = 0;
    w.height = 0;
    w.background_color = 0;
    w.color = fg;
    w.border_radius = 0;

    int i = 0;
    while (txt && txt[i] != '\\0' && i < 63) {
        w.text[i] = txt[i];
        i++;
    }
    w.text[i] = '\\0';
    return w;
}

Widget widget_make_button(int px, int py, int pw, int ph, uint32_t bg, uint32_t fg, int radius, const char* txt) {
    Widget w;
    w.type = WIDGET_BUTTON;
    w.x = px;
    w.y = py;
    w.width = pw;
    w.height = ph;
    w.background_color = bg;
    w.color = fg;
    w.border_radius = radius;

    int i = 0;
    while (txt && txt[i] != '\\0' && i < 63) {
        w.text[i] = txt[i];
        i++;
    }
    w.text[i] = '\\0';
    return w;
}

void widget_draw(const Widget* w, DE_API* api) {
    if (!w || !api) return;

    if (w->type == WIDGET_LABEL) {
        if (api->draw_text) {
            api->draw_text(w->x, w->y, w->text, w->color);
        }
    } else if (w->type == WIDGET_BUTTON) {
        if (api->draw_rect) {
            api->draw_rect(w->x, w->y, w->width, w->height, w->background_color);
        }
        if (api->draw_text) {
            api->draw_text(w->x + 12, w->y + (w->height - 8) / 2, w->text, w->color);
        }
    }
}
"""
    with open(os.path.join(lib_dir, "widget.c"), "w", encoding="utf-8") as f:
        f.write(c_widget_code)

    # 16. src/main.c
    main_code = r"""#include <kernel/drivers/video/de_api.h>
#include "grid.h"
#include "window.h"
#include "widget.h"
#include <stdbool.h>

void app_main(DE_API* api) {
    if (!api) return;

    if (api->log) {
        api->log("[DE] app_main basladi");
    }

    if (api->get_file_count && api->get_file_name_at) {
        const char* target_dir = "/usr/share/applications";
        int file_count = api->get_file_count(target_dir);

        for (int i = 0; i < file_count; i++) {
            char filename[32];
            if (api->get_file_name_at(target_dir, i, filename, (int)sizeof(filename))) {
                /* Dosya işleme döngüsü */
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
    bool show_grid      = true;

    de_mouse_state_t mouse = {0, 0, 0, 0, 0};

    int w = api->screen_width > 0 ? api->screen_width : 1920;
    int h = api->screen_height > 0 ? api->screen_height : 1080;

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
        }

        if (api->get_key) {
            char k = api->get_key();
            if (k == 27) break;

            if (k == 'g' || k == 'G') {
                show_grid = !show_grid;
            }
        }

        if (show_grid) {
            draw_grid_lines(api, w, h, cell_size, grid_color);
        }

        if (api->render_kbi) {
            api->render_kbi(mouse.x, mouse.y, "/sys/themes/arrow-cursor.kbi");
        }

        if (api->update_display) {
            api->update_display();
        }
    }
}
"""
    with open(os.path.join(src_dir, "main.c"), "w", encoding="utf-8") as f:
        f.write(main_code)

    resolved_output = (
        output_file.strip()
        if isinstance(output_file, str) and output_file.strip()
        else name.strip().lower()
    )

    # 17. kvx.json Manifest
    kvx_json_data = {
        "name": name,
        "output_file": resolved_output,
        "type": "de",
        "sub_type": "kernel",
        "version": version,
        "author": author,
        "compiler_flags": "-O2 -Wall -Wextra -m32 -ffreestanding",
        "linker_flags": "-m elf_i386 -N -e _start -T linker.ld"
    }
    with open(os.path.join(target_dir, "kvx.json"), "w", encoding="utf-8") as f:
        json.dump(kvx_json_data, f, indent=4, ensure_ascii=False)

    print(f"Başarılı: '{name}' DE projesi (C) oluşturuldu.")
    return True