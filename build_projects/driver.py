import os
import subprocess

def build_driver_project(project_path, name, target_arch="i686", custom_cflags="", custom_ldflags="", run_make=True):
    target_dir = os.path.abspath(project_path)
    
    if not os.path.exists(target_dir):
        print(f"Hata: '{target_dir}' dizini bulunamadı!")
        return False

    # Sürücüler için varsayılan linker bayrakları (konumdan bağımsız binary çıktı için)
    ldflags = custom_ldflags if custom_ldflags else "-m elf_i386 -nostdlib -T linker.ld"
    
    makefile_content = f"""TARGET = {name}.kdf
KUVIX_SDK_INC = $(HOME)/.kuvix/sdk/include
CXX = i686-elf-g++
LD = i686-elf-ld

CXXFLAGS = -m32 -march={target_arch} -c -ffreestanding -fno-pic -fno-pie -mno-sse -mno-mmx -mno-80387 \\
           -fno-stack-protector -fno-builtin -fno-asynchronous-unwind-tables \\
           -ffunction-sections -fdata-sections -I$(KUVIX_SDK_INC) \\
           -fno-rtti -fno-exceptions -O2 -Wall -Wextra {custom_cflags}

LDFLAGS = {ldflags}

CPP_SRCS = $(shell find src -type f -name '*.cpp' 2>/dev/null)
CPP_OBJS = $(patsubst src/%.cpp, build/%.o, $(CPP_SRCS))

OBJS = $(CPP_OBJS)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
\t$(LD) $(LDFLAGS) $(OBJS) -o $(TARGET)

build/%.o: src/%.cpp
\t@mkdir -p $(dir $@)
\t$(CXX) $(CXXFLAGS) $< -o $@

clean:
\trm -rf build {name}.kdf
"""

    makefile_path = os.path.join(target_dir, "Makefile")
    with open(makefile_path, "w", encoding="utf-8") as f:
        f.write(makefile_content)

    print(f"Başarılı: '{name}' sürücüsü için Makefile oluşturuldu.")

    if run_make:
        print(f"Derleme başlatılıyor ({name} - Sürücü)...")
        result = subprocess.run(["make"], cwd=target_dir)
        if result.returncode != 0:
            print("Hata: Sürücü derlemesi başarısız oldu!")
            return False
        print(f"Başarılı: '{name}.kdf' başarıyla derlendi.")

    return True