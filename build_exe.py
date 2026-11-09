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

    # 1. Encerra qualquer instância em execução do aplicativo para liberar arquivos bloqueados
    try:
        subprocess.run(["taskkill", "/f", "/im", "LCR-OdontoGest.exe"], capture_output=True)
    except Exception:
        pass

    if not ICON_PATH.exists():
        print(f"[ERRO] Ícone não encontrado em: {ICON_PATH}")
        sys.exit(1)

    dist_dir = BASE_DIR / "dist"
    exe_dir = dist_dir / "LCR-OdontoGest"

    # 2. Preserva os dados do usuário (banco de dados e uploads) antes da limpeza
    temp_backup_dir = BASE_DIR / "build" / "temp_data_backup"
    temp_backup_dir.mkdir(parents=True, exist_ok=True)

    dist_data = exe_dir / "data"
    dist_uploads = exe_dir / "uploads"

    if dist_data.exists():
        shutil.copytree(dist_data, temp_backup_dir / "data", dirs_exist_ok=True)
    elif (BASE_DIR / "data").exists():
        shutil.copytree(BASE_DIR / "data", temp_backup_dir / "data", dirs_exist_ok=True)

    if dist_uploads.exists():
        shutil.copytree(dist_uploads, temp_backup_dir / "uploads", dirs_exist_ok=True)
    elif (BASE_DIR / "uploads").exists():
        shutil.copytree(BASE_DIR / "uploads", temp_backup_dir / "uploads", dirs_exist_ok=True)

    # 3. Comando PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LCR-OdontoGest",
        "--windowed",
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
        exe_path = exe_dir / "LCR-OdontoGest.exe"

        # Garante cópia da pasta assets junto ao executável
        dest_assets = exe_dir / "assets"
        if not dest_assets.exists():
            shutil.copytree(ASSETS_DIR, dest_assets)

        # Restaura os dados e uploads do usuário
        saved_data = temp_backup_dir / "data"
        if saved_data.exists():
            dest_data = exe_dir / "data"
            shutil.copytree(saved_data, dest_data, dirs_exist_ok=True)

        saved_uploads = temp_backup_dir / "uploads"
        if saved_uploads.exists():
            dest_uploads = exe_dir / "uploads"
            shutil.copytree(saved_uploads, dest_uploads, dirs_exist_ok=True)

        # Remove backup temporário
        shutil.rmtree(temp_backup_dir, ignore_errors=True)

        # Desbloqueia o arquivo executável no Windows
        try:
            subprocess.run(["powershell", "-Command", f"Unblock-File -Path '{exe_path}'"], capture_output=True)
        except Exception:
            pass

        print("\n" + "=" * 60)
        print("[SUCESSO] COMPILACAO CONCLUIDA COM SUCESSO!")
        print(f"Executavel gerado em:\n{exe_path}")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print(f"[ERRO] Erro durante a compilacao (codigo {resultado.returncode})")
        print("=" * 60)
        sys.exit(resultado.returncode)


if __name__ == "__main__":
    compilar()
