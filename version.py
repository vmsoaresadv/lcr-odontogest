import sys
from pathlib import Path

# LCR OdontoGest - Versao Oficial
__version__ = "1.2.0"
APP_NAME = "LCR OdontoGest"
CLINICA_NOME = "LCR Odontologia"
RESPONSAVEL_NOME = "Dra. Lara Camila"
RESPONSAVEL_CRO = "CRO-BA 15247"
CIDADE_ESTADO = "Irecê - Bahia"
GITHUB_REPO = "vmsoaresadv/lcr-odontogest"  # Repositorio oficial


def get_app_dir() -> Path:
    """Retorna o diretório base da aplicação (suporta modo normal e executável congelado)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_asset_path(filename: str) -> Path:
    """Localiza arquivos de assets tanto em desenvolvimento quanto no executável PyInstaller."""
    # 1. Se estiver rodando como executável PyInstaller
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            c1 = Path(sys._MEIPASS) / "assets" / filename
            if c1.exists():
                return c1
        exe_dir = Path(sys.executable).resolve().parent
        c2 = exe_dir / "assets" / filename
        if c2.exists():
            return c2
        c3 = exe_dir / "_internal" / "assets" / filename
        if c3.exists():
            return c3

    # 2. Modo desenvolvimento normal
    base = Path(__file__).resolve().parent
    c4 = base / "assets" / filename
    if c4.exists():
        return c4
    return base / "assets" / filename
