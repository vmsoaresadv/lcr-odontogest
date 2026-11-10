"""
Compilador do Instalador Oficial LCR OdontoGest
Gera o executável único leve Instalador-LCR-OdontoGest.exe em dist/
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "app_icon.ico"
SCRIPT_PATH = BASE_DIR / "installer" / "setup_gui.py"
DIST_DIR = BASE_DIR / "dist"

def build():
    print("=" * 60)
    print("Compilando Instalador-LCR-OdontoGest.exe...")
    print("=" * 60)

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Instalador-LCR-OdontoGest",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--icon={ICON_PATH}",
        f"--add-data={ICON_PATH};assets",
        f"--distpath={DIST_DIR}",
        str(SCRIPT_PATH)
    ]

    print(f"Executando comando:\n{' '.join(cmd)}\n")
    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe = DIST_DIR / "Instalador-LCR-OdontoGest.exe"
        size_mb = exe.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print(f"[SUCESSO] Instalador gerado com sucesso!")
        print(f"Arquivo: {exe}")
        print(f"Tamanho: {size_mb:.2f} MB")
        print("=" * 60)
    else:
        print("\n[ERRO] Falha ao compilar instalador.")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
