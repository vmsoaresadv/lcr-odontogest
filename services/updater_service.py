import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from version import __version__, GITHUB_REPO, APP_NAME


def parse_version_tuple(v_str: str) -> tuple:
    """Converte 'v1.0.1' ou '1.0.1' para tupla de inteiros (1, 0, 1)."""
    cleaned = v_str.strip().lstrip("vV")
    partes = []
    for p in cleaned.split("."):
        try:
            partes.append(int(p))
        except ValueError:
            partes.append(0)
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes[:3])


def verificar_atualizacao(repo: str = GITHUB_REPO, timeout: int = 6) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Consulta o GitHub Releases para checar se há uma versão superior à atual.
    Retorna: (tem_atualizacao, info_versao, mensagem)
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{APP_NAME}-Updater/{__version__}",
            "Accept": "application/vnd.github.v3+json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                tag_name = data.get("tag_name", "")
                versao_remota = parse_version_tuple(tag_name)
                versao_atual = parse_version_tuple(__version__)

                if versao_remota > versao_atual:
                    # Encontrou nova versão
                    assets = data.get("assets", [])
                    download_url = None
                    file_name = None
                    for a in assets:
                        name = a.get("name", "").lower()
                        if name.endswith(".exe") or name.endswith(".zip"):
                            download_url = a.get("browser_download_url")
                            file_name = a.get("name")
                            break

                    info = {
                        "versao_tag": tag_name,
                        "versao_str": tag_name.lstrip("vV"),
                        "nome": data.get("name", f"Versão {tag_name}"),
                        "corpo": data.get("body", "Melhorias de desempenho e estabilidade."),
                        "publicado_em": data.get("published_at", ""),
                        "download_url": download_url,
                        "file_name": file_name,
                        "html_url": data.get("html_url", "")
                    }
                    return True, info, f"Nova versão {tag_name} disponível!"
                else:
                    return False, None, f"O {APP_NAME} já está na versão mais recente ({__version__})."
            else:
                return False, None, f"Servidor retornou código {response.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False, None, "Nenhuma release oficial encontrada no repositório ainda."
        return False, None, f"Erro ao consultar atualizações (HTTP {e.code})"
    except Exception as e:
        return False, None, f"Não foi possível checar atualizações: {str(e)}"


def criar_script_substituicao_windows(novo_exe_path: str, destino_exe_path: str) -> Path:
    """
    Gera um script batch temporário que aguarda o processo atual fechar,
    substitui o executável antigo pelo novo e reabre o sistema.
    """
    script_path = Path(novo_exe_path).parent / "aplicar_update.bat"
    pid = os.getpid()

    # O script espera o PID fechar, move o arquivo e inicia o novo
    script_content = f"""@echo off
chcp 65001 > nul
echo Atualizando o {APP_NAME}...
timeout /t 2 /nobreak > nul

:loop
tasklist /fi "pid eq {pid}" 2>nul | find "{pid}" >nul
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak > nul
    goto loop
)

copy /y "{novo_exe_path}" "{destino_exe_path}" > nul
del /f /q "{novo_exe_path}" > nul

start "" "{destino_exe_path}"
del "%~f0"
"""
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    return script_path
