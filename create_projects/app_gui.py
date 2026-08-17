import os
import json

def create_new_project(base_path, name, version, author):
    proj_path = os.path.join(base_path, name)
    os.makedirs(os.path.join(proj_path, "src"), exist_ok=True)
    os.makedirs(os.path.join(proj_path, "include"), exist_ok=True)

    config = {
        "name": name,
        "version": version,
        "author": author,
        "type": "app-gui"
    }
    with open(os.path.join(proj_path, "kvx.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    layout = {
        "title": name,
        "elements": {
            "label": {"x": 20, "y": 50, "text": "Kuvix App GUI"},
            "button": {"x": 20, "y": 100, "width": 120, "height": 30, "text": "Tıkla"}
        }
    }
    with open(os.path.join(proj_path, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=4)

    # kuvix.h kullanarak örnek event bağlama yapısı
    main_cpp = """#include <kuvix.h>

void on_button_click() {
    setElementText("label", "Butona tıklandı!");
}

int main() {
    loadUI("layout.json");
    
    // Elementi seçip event bağlama örneği
    getElementByName("button").event("click", on_button_click);

    runApp();
    return 0;
}
"""
    with open(os.path.join(proj_path, "src", "main.cpp"), "w", encoding="utf-8") as f:
        f.write(main_cpp)
    
    print(f"Başarılı: '{name}' uygulaması (app-gui) oluşturuldu.")