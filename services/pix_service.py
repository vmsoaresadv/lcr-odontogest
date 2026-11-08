import io
import qrcode
from typing import Tuple, Optional
from PySide6.QtGui import QPixmap, QImage


def crc16_ccitt(data: str) -> str:
    """Calcula o CRC16-CCITT (polinômio 0x1021) conforme especificação do BACEN BR Code."""
    crc = 0xFFFF
    for char in data.encode("utf-8"):
        crc ^= (char << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def format_tlv(id_tag: str, value: str) -> str:
    """Formata tag TLV (Tag-Length-Value) do padrão EMV."""
    length = len(value.encode("utf-8"))
    return f"{id_tag}{length:02d}{value}"


def sanitize_text(text: str, max_len: int) -> str:
    """Remove caracteres especiais e trunca texto para o padrão EMV Pix."""
    import unicodedata
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    limpo = "".join(c for c in sem_acento if c.isalnum() or c in (" ", "-", "_", "."))
    return limpo.strip().upper()[:max_len]


def generate_pix_copy_paste(
    chave_pix: str,
    titular: str = "LCR CLINICA",
    cidade: str = "IRECE",
    valor: float = 0.0,
    identificador: str = "SALA2"
) -> str:
    """
    Gera a string oficial do Pix Copia e Cola (BR Code) conforme o Manual de Padrões do BACEN.
    """
    chave_limpa = chave_pix.strip()
    titular_limpo = sanitize_text(titular, 25) or "CLINICA LCR"
    cidade_limpa = sanitize_text(cidade, 15) or "IRECE"
    identificador_limpo = sanitize_text(identificador, 20) or "SALA2"

    # 00: Payload Format Indicator
    payload = format_tlv("00", "01")

    # 26: Merchant Account Information (Pix)
    gui = format_tlv("00", "br.gov.bcb.pix")
    key = format_tlv("01", chave_limpa)
    payload += format_tlv("26", gui + key)

    # 52: Merchant Category Code
    payload += format_tlv("52", "0000")

    # 53: Transaction Currency (986 = Real BRL)
    payload += format_tlv("53", "986")

    # 54: Transaction Amount (se houver valor > 0)
    if valor and valor > 0:
        val_str = f"{valor:.2f}"
        payload += format_tlv("54", val_str)

    # 58: Country Code
    payload += format_tlv("58", "BR")

    # 59: Merchant Name
    payload += format_tlv("59", titular_limpo)

    # 60: Merchant City
    payload += format_tlv("60", cidade_limpa)

    # 62: Additional Data Field (TxID)
    payload += format_tlv("62", format_tlv("05", identificador_limpo))

    # 63: CRC16 (Calculado sobre toda a string anterior + '6304')
    payload += "6304"
    crc = crc16_ccitt(payload)
    return payload + crc


def generate_pix_qr_pixmap(pix_code: str, box_size: int = 8, border: int = 2) -> QPixmap:
    """Gera um QPixmap contendo o QR Code a partir da string Pix Copia e Cola."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border
    )
    qr.add_data(pix_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff").convert("RGBA")

    # Converte PIL Image para QPixmap sem salvar em disco
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    qimg = QImage()
    qimg.loadFromData(buffer.getvalue(), "PNG")
    return QPixmap.fromImage(qimg)
