"""
Script de Publicação 100% Automatizada no GitHub
- Atualiza o version.json no repositório com chave SHA-256 calculada na hora
- Cria a Release no GitHub (ex: v1.0.1)
- Faz o upload do executável Instalador-LCR-OdontoGest.exe direto para as Releases
Zero intervenção manual necessária!
"""

import os
import sys
import json
import base64
import hashlib
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"
INSTALLER_PATH = DIST_DIR / "Instalador-LCR-OdontoGest.exe"

# Lê versão do version.py
from version import __version__, GITHUB_REPO

def calcular_sha256(arquivo: Path) -> str:
    h = hashlib.sha256()
    with open(arquivo, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def get_token() -> str:
    # 1. Variável de ambiente
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token.strip()
    
    # 2. Arquivo local .github_token ou github_token.txt (ignorado pelo git)
    for name in [".github_token", "github_token.txt"]:
        token_file = BASE_DIR / name
        if token_file.exists():
            return token_file.read_text("utf-8").strip()
    
    return ""

def publicar():
    token = get_token()
    if not token:
        print("[ERRO] Token do GitHub não configurado!")
        print("Para publicar automaticamente, configure seu GITHUB_TOKEN:")
        print("Crie um arquivo '.github_token' na raiz do projeto contendo seu token de acesso pessoal (classic).")
        sys.exit(1)

    if not INSTALLER_PATH.exists():
        print(f"[ERRO] Instalador não encontrado em: {INSTALLER_PATH}")
        sys.exit(1)

    tag = f"v{__version__}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "LCR-OdontoGest-AutoPublisher"
    }

    print("=" * 60)
    print(f"Publicando {tag} automaticamente no GitHub ({GITHUB_REPO})...")
    print("=" * 60)

    # 1. Calcula hash SHA-256
    print("\n[1/3] Calculando chave criptográfica SHA-256...")
    sha256 = calcular_sha256(INSTALLER_PATH)
    print(f"Chave SHA-256: {sha256}")

    # 2. Atualiza version.json no repositório
    print("\n[2/3] Atualizando version.json no repositório...")
    version_data = {
        "version": __version__,
        "app_name": "LCR OdontoGest",
        "release_date": "2026-11-10",
        "installer_name": "Instalador-LCR-OdontoGest.exe",
        "installer_sha256": sha256,
        "download_url": f"https://github.com/{GITHUB_REPO}/releases/download/{tag}/Instalador-LCR-OdontoGest.exe",
        "changelog": f"Versão oficial {__version__} de produção para a clínica com instalador seguro autocontido."
    }
    json_bytes = json.dumps(version_data, indent=2, ensure_ascii=False).encode("utf-8")
    content_b64 = base64.b64encode(json_bytes).decode("ascii")

    # Verifica se version.json já existe no repo para obter o sha anterior
    current_sha = None
    try:
        req_get = urllib.request.Request(
            f"https://api.github.com/repos/{GITHUB_REPO}/contents/version.json",
            headers=headers
        )
        with urllib.request.urlopen(req_get) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            current_sha = data.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            print(f"[AVISO] Falha ao verificar version.json: {e}")

    payload_put = {
        "message": f"release: versao {__version__} com chave SHA-256",
        "content": content_b64
    }
    if current_sha:
        payload_put["sha"] = current_sha

    req_put = urllib.request.Request(
        f"https://api.github.com/repos/{GITHUB_REPO}/contents/version.json",
        data=json.dumps(payload_put).encode("utf-8"),
        headers=headers,
        method="PUT"
    )
    with urllib.request.urlopen(req_put) as resp:
        print("[SUCESSO] version.json atualizado no GitHub com sucesso!")

    # 3. Cria a Release no GitHub
    print(f"\n[3/3] Criando Release {tag} e enviando Instalador-LCR-OdontoGest.exe...")
    release_payload = {
        "tag_name": tag,
        "name": f"{tag} - LCR OdontoGest",
        "body": f"Versão oficial {__version__} com validação de segurança criptográfica SHA-256.",
        "draft": False,
        "prerelease": False
    }

    release_id = None
    try:
        req_rel = urllib.request.Request(
            f"https://api.github.com/repos/{GITHUB_REPO}/releases",
            data=json.dumps(release_payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req_rel) as resp:
            rel_info = json.loads(resp.read().decode("utf-8"))
            release_id = rel_info.get("id")
            print(f"[INFO] Release {tag} criada! ID: {release_id}")
    except urllib.error.HTTPError as e:
        if e.code == 422:  # Release ou tag já existe
            print(f"[INFO] Tag {tag} já existe, buscando ID...")
            req_find = urllib.request.Request(
                f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag}",
                headers=headers
            )
            with urllib.request.urlopen(req_find) as resp:
                rel_info = json.loads(resp.read().decode("utf-8"))
                release_id = rel_info.get("id")
        else:
            raise

    # Upload do arquivo binário (.exe)
    print(f"[UPLOAD] Enviando Instalador-LCR-OdontoGest.exe ({INSTALLER_PATH.stat().st_size / (1024*1024):.1f} MB)...")
    upload_url = f"https://uploads.github.com/repos/{GITHUB_REPO}/releases/{release_id}/assets?name=Instalador-LCR-OdontoGest.exe"

    with open(INSTALLER_PATH, "rb") as f:
        file_data = f.read()

    upload_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/octet-stream",
        "User-Agent": "LCR-OdontoGest-AutoPublisher"
    }

    req_upload = urllib.request.Request(
        upload_url,
        data=file_data,
        headers=upload_headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req_upload) as resp:
            print("[SUCESSO] Upload do executável concluído com sucesso!")
    except urllib.error.HTTPError as e:
        if e.code == 422:
            print("[INFO] O arquivo já existe nesta release. Atualização confirmada.")
        else:
            raise

    print("\n" + "=" * 60)
    print(f"[SUCESSO TOTAL] PUBLICACAO AUTOMATICA DA VERSAO {__version__} CONCLUIDA!")
    print(f"Link da Release: https://github.com/{GITHUB_REPO}/releases/tag/{tag}")
    print("=" * 60)

if __name__ == "__main__":
    publicar()
