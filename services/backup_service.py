import os
import json
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

from database.connection import DB_PATH, DATA_DIR, get_db_connection
from services.audit_service import log_action
from version import __version__, APP_NAME


BACKUPS_DIR = DATA_DIR / "backups"
ANEXOS_DIR = DATA_DIR / "anexos"


def criar_backup_completo(destino_zip_path: Optional[str] = None, user_info: Optional[dict] = None) -> Tuple[bool, str]:
    """
    Cria um arquivo compactado .zip contendo:
    - Cópia segura em tempo real do banco SQLite (clinica.db)
    - Todos os exames e documentos anexados (data/anexos)
    - Manifesto com data/hora, versão e estatísticas
    """
    try:
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        ANEXOS_DIR.mkdir(parents=True, exist_ok=True)

        agora = datetime.now()
        timestamp_str = agora.strftime("%Y%m%d_%H%M%S")

        if not destino_zip_path:
            destino_zip_path = str(BACKUPS_DIR / f"backup_lcrodontogest_{timestamp_str}.zip")

        # 1. Cria cópia segura do banco usando a SQLite Online Backup API
        temp_db_path = BACKUPS_DIR / f"temp_backup_{timestamp_str}.db"
        with get_db_connection() as conn_src:
            dest_conn = sqlite3.connect(temp_db_path)
            conn_src.backup(dest_conn)
            dest_conn.close()

        # 2. Monta manifesto de metadados
        qtd_anexos = len([f for f in ANEXOS_DIR.rglob("*") if f.is_file()])
        manifesto = {
            "app_name": APP_NAME,
            "version": __version__,
            "data_criacao": agora.isoformat(),
            "data_formatada": agora.strftime("%d/%m/%Y às %H:%M:%S"),
            "criado_por": user_info.get("nome", "Sistema") if user_info else "Sistema",
            "qtd_anexos": qtd_anexos
        }

        # 3. Empacota tudo em um único arquivo .zip
        with zipfile.ZipFile(destino_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # Adiciona o banco de dados
            zipf.write(temp_db_path, arcname="clinica.db")

            # Adiciona o manifesto
            zipf.writestr("manifesto.json", json.dumps(manifesto, indent=2, ensure_ascii=False))

            # Adiciona todos os anexos de exames/documentos
            for arquivo in ANEXOS_DIR.rglob("*"):
                if arquivo.is_file():
                    arcname = Path("anexos") / arquivo.relative_to(ANEXOS_DIR)
                    zipf.write(arquivo, arcname=str(arcname))

        # Remove o arquivo temporário do banco
        if temp_db_path.exists():
            temp_db_path.unlink()

        # Registra log de auditoria
        if user_info:
            log_action(
                user_id=user_info.get("id", 1),
                user_nome=user_info.get("nome", "Admin"),
                acao="Backup do Sistema",
                detalhes=f"Backup completo gerado em: {Path(destino_zip_path).name} ({qtd_anexos} anexos salvos)"
            )

        return True, str(destino_zip_path)

    except Exception as e:
        return False, f"Falha ao gerar backup: {str(e)}"


def restaurar_backup_completo(arquivo_zip_path: str, user_info: Optional[dict] = None) -> Tuple[bool, str]:
    """
    Restaura um backup compactado .zip:
    - Valida se o arquivo contém o clinica.db e estrutura válida
    - Cria um backup emergencial automático do estado atual antes da substituição
    - Extrai clinica.db e restaura a pasta data/anexos
    """
    try:
        zip_path = Path(arquivo_zip_path)
        if not zip_path.exists() or not zipfile.is_zipfile(zip_path):
            return False, "O arquivo selecionado não é um arquivo ZIP válido."

        with zipfile.ZipFile(zip_path, "r") as zipf:
            nomes = zipf.namelist()
            if "clinica.db" not in nomes:
                return False, "O arquivo ZIP selecionado não contém um banco de dados válido do sistema (clinica.db ausente)."

            # 1. Faz backup emergencial do estado atual antes de substituir
            criar_backup_completo(user_info=user_info)

            # 2. Extrai clinica.db substituindo o atual
            zipf.extract("clinica.db", path=DATA_DIR)

            # 3. Extrai anexos
            for item in nomes:
                if item.startswith("anexos/") and not item.endswith("/"):
                    # Extrai preservando o arquivo
                    sub_caminho = item[len("anexos/"):]
                    alvo = ANEXOS_DIR / sub_caminho
                    alvo.parent.mkdir(parents=True, exist_ok=True)
                    with zipf.open(item) as src, open(alvo, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        # Registra auditoria
        if user_info:
            log_action(
                user_id=user_info.get("id", 1),
                user_nome=user_info.get("nome", "Admin"),
                acao="Restauração de Backup",
                detalhes=f"Banco de dados e anexos restaurados a partir de {zip_path.name}"
            )

        return True, "Backup restaurado com sucesso! As alterações foram aplicadas."

    except Exception as e:
        return False, f"Falha na restauração do backup: {str(e)}"


def listar_backups_locais() -> list:
    """Retorna lista dos backups gerados na pasta padrão de backups."""
    if not BACKUPS_DIR.exists():
        return []
    
    lista = []
    for f in BACKUPS_DIR.glob("backup_lcrodontogest_*.zip"):
        tam_mb = round(f.stat().st_size / (1024 * 1024), 2)
        dt_mod = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m/%Y %H:%M")
        lista.append({
            "caminho": str(f),
            "nome": f.name,
            "tamanho_mb": tam_mb,
            "data": dt_mod
        })
    lista.sort(key=lambda x: x["nome"], reverse=True)
    return lista
