"""
Compilador do Instalador Autocontido (Single File Setup)
Gera Instalador-LCR-OdontoGest-Setup.exe com todos os arquivos embutidos dentro dele.
Zero necessidade de arquivo .zip externo!
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "app_icon.ico"
DIST_DIR = BASE_DIR / "dist"
PAYLOAD_ZIP = DIST_DIR / "LCR-OdontoGest.zip"
SCRIPT_PATH = BASE_DIR / "installer" / "setup_standalone.py"

def build():
    print("=" * 60)
    print("Compilando Instalador Autocontido (Zero .zip no GitHub)...")
    print("=" * 60)

    if not PAYLOAD_ZIP.exists():
        print(f"[ERRO] Pacote base {PAYLOAD_ZIP} não encontrado.")
        sys.exit(1)

    build_dir = BASE_DIR / "build" / "Instalador-LCR-OdontoGest"
    if build_dir.exists():
        try:
            subprocess.run(["attrib", "-r", "-s", "-h", str(build_dir / "*"), "/s", "/d"], capture_output=True)
            import shutil
            shutil.rmtree(build_dir, ignore_errors=True)
        except Exception:
            pass

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=Instalador-LCR-OdontoGest",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        f"--icon={ICON_PATH}",
        f"--add-data={ICON_PATH};assets",
        f"--add-data={PAYLOAD_ZIP};payload",
        f"--distpath={DIST_DIR}",
        str(SCRIPT_PATH)
    ]

    print(f"Executando comando:\n{' '.join(cmd)}\n")
    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe = DIST_DIR / "Instalador-LCR-OdontoGest.exe"
        size_mb = exe.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print(f"[SUCESSO] Instalador Autocontido gerado com sucesso!")
        print(f"Arquivo único: {exe}")
        print(f"Tamanho total: {size_mb:.2f} MB")
        print("Este executavel já contém todo o sistema embutido dentro dele!")
        print("=" * 60)
    else:
        print("\n[ERRO] Falha ao compilar.")
        sys.exit(res.returncode)

if __name__ == "__main__":
    build()
