import os
import subprocess

def build_login_screen_project(project_path, name, target_arch="i686", custom_cflags="", custom_ldflags="", run_make=True):
    target_dir = os.path.abspath(project_path)
    
    if not os.path.exists(target_dir):
        print(f"Hata: '{target_dir}' dizini bulunamadı!")
        return False

    ldflags = custom_ldflags if custom_ldflags else "-m elf_i386 -T linker.ld --gc-sections -e _start -s"
    
    # Çıktı uzantısını .kls olarak belirliyoruz
    makefile_content = f"""TARGET = {name}.kls
KUVIX_SDK_INC = $(HOME)/.kuvix/sdk/include
AS = i686-elf-as
CXX = i686-elf-g++
LD = i686-elf-ld

CXXFLAGS = -m32 -Wa,--32 -march={target_arch} -c -ffreestanding -fno-pic -fno-pie -mno-sse -mno-mmx -mno-80387 \\
           -fno-stack-protector -fno-builtin -fno-asynchronous-unwind-tables \\
           -ffunction-sections -fdata-sections -Iinclude -I$(KUVIX_SDK_INC) \\
           -fno-rtti -fno-exceptions {custom_cflags}

LDFLAGS = {ldflags}

CPP_SRCS = $(shell find src -type f -name '*.cpp' 2>/dev/null)
CPP_OBJS = $(patsubst src/%.cpp, build/%.o, $(CPP_SRCS))

ENTRY_OBJ = build/runtime/entry.o
OBJS = $(ENTRY_OBJ) $(filter-out $(ENTRY_OBJ), $(CPP_OBJS))

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
\t$(LD) $(LDFLAGS) $(OBJS) -o $(TARGET)

build/runtime/entry.o: src/runtime/entry.s
\t@mkdir -p $(dir $@)
\t$(AS) --32 $< -o $@

build/%.o: src/%.cpp
\t@mkdir -p $(dir $@)
\t$(CXX) $(CXXFLAGS) $< -o $@

clean:
\trm -rf build {name}.kls
"""

    makefile_path = os.path.join(target_dir, "Makefile")
    with open(makefile_path, "w", encoding="utf-8") as f:
        f.write(makefile_content)

    print(f"Başarılı: '{name}' için KLS Makefile oluşturuldu[cite: 1].")

    if run_make:
        print(f"Derleme başlatılıyor ({name})...")
        result = subprocess.run(["make"], cwd=target_dir)
        if result.returncode != 0:
            print("Hata: Derleme başarısız oldu!")
            return False
        print(f"Başarılı: '{name}.kls' başarıyla derlendi.")

    return True