import os
import json

def create_new_project(base_path, name, version, author):
    proj_path = os.path.join(base_path, name)
    os.makedirs(os.path.join(proj_path, "src"), exist_ok=True)
    os.makedirs(os.path.join(proj_path, "include"), exist_ok=True)

    # 1. kuvix.json yapılandırması
    config = {
        "name": name,
        "version": version,
        "author": author,
        "type": "app-gui"
    }
    with open(os.path.join(proj_path, "kvx.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

    # 2. Güncel dizi ve nesne yapısına uygun layout.json
    layout = {
        "window": {
            "title": name,
            "width": 800,
            "height": 600
        },
        "elements": [
            {
                "type": "label",
                "text": "Kuvix App GUI - Etiket",
                "x": 50,
                "y": 60
            },
            {
                "type": "button",
                "text": "Tıkla",
                "x": 50,
                "y": 120,
                "width": 140,
                "height": 40
            }
        ]
    }
    with open(os.path.join(proj_path, "layout.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f, indent=4)

    # 3. kuvix.h kullanılarak örnek event bağlama yapısı içeren main.cpp
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
    
    print(f"Başarılı: '{name}' uygulaması (app-gui) güncel şablonla oluşturuldu.")