import os
import sys
import shutil
import subprocess
from pathlib import Path

from version import __version__, APP_NAME

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "app_icon.ico"


def compilar():
    print("=" * 60)
    print(f"Iniciando compilação do {APP_NAME} v{__version__}")
    print("=" * 60)

    if not ICON_PATH.exists():
        print(f"[ERRO] Ícone não encontrado em: {ICON_PATH}")
        sys.exit(1)

    dist_dir = BASE_DIR / "dist"
    build_dir = BASE_DIR / "build"

    # Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LCR-OdontoGest",
        "--windowed",           # Sem tela preta de terminal do DOS
        "--clean",
        "--noconfirm",
        f"--icon={ICON_PATH}",
        f"--add-data={ASSETS_DIR};assets",
        "--collect-all=PySide6",
        str(BASE_DIR / "main.py")
    ]

    print(f"Executando comando:\n{' '.join(cmd)}\n")
    resultado = subprocess.run(cmd)

    if resultado.returncode == 0:
        exe_dir = dist_dir / "LCR-OdontoGest"
        exe_path = exe_dir / "LCR-OdontoGest.exe"

        # Garante cópia da pasta assets junto ao executável
        dest_assets = exe_dir / "assets"
        if not dest_assets.exists():
            shutil.copytree(ASSETS_DIR, dest_assets)

        # Copia a pasta data com o banco de dados atual
        src_data = BASE_DIR / "data"
        dest_data = exe_dir / "data"
        if src_data.exists() and not dest_data.exists():
            shutil.copytree(src_data, dest_data)

        print("\n" + "=" * 60)
        print("[SUCESSO] COMPILACAO CONCLUIDA COM SUCESSO!")
        print(f"Executavel gerado em:\n{exe_path}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print(f"[ERRO] Erro durante a compilacao (codigo {resultado.returncode})")
        print("=" * 60)


if __name__ == "__main__":
    compilar()
