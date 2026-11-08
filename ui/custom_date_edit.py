from datetime import datetime, date
from typing import Optional, Union

from PySide6.QtWidgets import (
    QFrame, QLineEdit, QToolButton, QHBoxLayout,
    QCalendarWidget, QDialog, QVBoxLayout, QTableView
)
from PySide6.QtCore import Qt, QDate, Signal, QPoint
from PySide6.QtGui import QKeyEvent, QIcon


CALENDAR_STYLE = """
QDialog {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
}
QCalendarWidget {
    background-color: #ffffff;
    border: none;
    font-family: 'Segoe UI', sans-serif;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
    min-height: 38px;
}
QCalendarWidget QToolButton {
    color: #0f172a;
    font-weight: bold;
    font-size: 13px;
    background: transparent;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}
QCalendarWidget QToolButton:hover {
    background-color: #e2e8f0;
}
QCalendarWidget QSpinBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 2px 4px;
    font-size: 13px;
}
QCalendarWidget QMenu {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
}
QCalendarWidget QTableView {
    alternate-background-color: #ffffff;
    background-color: #ffffff;
    selection-background-color: #2ca5a9;
    selection-color: #ffffff;
    outline: none;
}
QCalendarWidget QTableView::item {
    padding: 4px;
    border-radius: 4px;
}
QCalendarWidget QTableView::item:hover {
    background-color: #ccfbf1;
    color: #0f766e;
    font-weight: bold;
    border: 1px solid #5eead4;
}
QCalendarWidget QTableView::item:selected {
    background-color: #2ca5a9;
    color: #ffffff;
    font-weight: bold;
}
"""


class SmartDateLineEdit(QLineEdit):
    """Campo de texto que auto-insere barras '/' e permite apagar livremente."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("dd/mm/aaaa")
        self.setMaxLength(10)
        self.textEdited.connect(self._format_text)

    def _format_text(self, text: str):
        digits = "".join(c for c in text if c.isdigit())[:8]
        fmt = ""
        if len(digits) > 0:
            fmt += digits[:2]
        if len(digits) >= 2:
            fmt += "/" + digits[2:4]
        if len(digits) >= 4:
            fmt += "/" + digits[4:8]

        if fmt != text:
            pos = self.cursorPosition()
            adv = len(fmt) - len(text)
            self.setText(fmt)
            self.setCursorPosition(pos + max(0, adv))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Backspace and not self.hasSelectedText():
            pos = self.cursorPosition()
            if pos in (3, 6):
                # Se o cursor estiver logo após '/', apaga a barra e o dígito anterior
                txt = self.text()
                new_txt = txt[:pos-2] + txt[pos:]
                self.setText(new_txt)
                self.setCursorPosition(pos - 2)
                self.textEdited.emit(new_txt)
                return
        super().keyPressEvent(event)


class CustomDateEdit(QFrame):
    """
    Substituto moderno e padronizado do QDateEdit para todo o sistema.
    - Digitação manual livre com inserção automática de barras (dd/mm/aaaa)
    - Suporte completo a apagar números (Backspace, Delete, Selecionar Tudo)
    - Calendário interativo flutuante com efeito visual de hover nos dias
    """
    dateChanged = Signal(QDate)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("customDateEditFrame")
        self._current_date = QDate.currentDate()
        self._display_format = "dd/MM/yyyy"
        self._popup_dialog: Optional[QDialog] = None
        self._calendar: Optional[QCalendarWidget] = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame#customDateEditFrame {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                min-height: 24px;
            }
            QFrame#customDateEditFrame:hover {
                border-color: #94a3b8;
            }
            QFrame#customDateEditFrame:focus-within {
                border: 2px solid #2ca5a9;
            }
            QFrame#customDateEditFrame QLineEdit {
                border: none;
                background: transparent;
                padding: 4px 4px;
                font-size: 13px;
                color: #0f172a;
                qproperty-alignment: 'AlignCenter';
            }
            QFrame#customDateEditFrame QToolButton {
                border: none;
                background: transparent;
                padding: 2px 8px;
                font-size: 14px;
                color: #64748b;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
            }
            QFrame#customDateEditFrame QToolButton:hover {
                background-color: #f1f5f9;
                color: #0f766e;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 2, 0)
        layout.setSpacing(2)

        self.line_edit = SmartDateLineEdit(self)
        self.line_edit.setAlignment(Qt.AlignCenter)
        self.line_edit.setText(self._current_date.toString("dd/MM/yyyy"))
        self.line_edit.editingFinished.connect(self._on_editing_finished)
        layout.addWidget(self.line_edit)

        self.btn_cal = QToolButton(self)
        self.btn_cal.setText("📅")
        self.btn_cal.setToolTip("Abrir calendário interativo")
        self.btn_cal.setCursor(Qt.PointingHandCursor)
        self.btn_cal.clicked.connect(self.abrir_calendario)
        layout.addWidget(self.btn_cal)

    def _on_editing_finished(self):
        qd = self.date()
        if qd.isValid():
            self._current_date = qd
            self.line_edit.setText(qd.toString("dd/MM/yyyy"))
            self.dateChanged.emit(qd)
        else:
            # Se incompleto ou inválido, restaura data atual
            self.line_edit.setText(self._current_date.toString("dd/MM/yyyy"))

    def date(self) -> QDate:
        txt = self.line_edit.text().strip()
        try:
            d = datetime.strptime(txt, "%d/%m/%Y").date()
            return QDate(d.year, d.month, d.day)
        except Exception:
            return QDate()

    def setDate(self, val: Union[QDate, date, str]):
        if isinstance(val, QDate):
            if val.isValid():
                self._current_date = val
        elif isinstance(val, date):
            self._current_date = QDate(val.year, val.month, val.day)
        elif isinstance(val, str) and val:
            try:
                # Suporta tanto ISO 'YYYY-MM-DD' quanto BR 'DD/MM/YYYY'
                if "-" in val:
                    d = datetime.strptime(val[:10], "%Y-%m-%d").date()
                else:
                    d = datetime.strptime(val[:10], "%d/%m/%Y").date()
                self._current_date = QDate(d.year, d.month, d.day)
            except Exception:
                pass

        self.line_edit.setText(self._current_date.toString("dd/MM/yyyy"))
        self.dateChanged.emit(self._current_date)

    def text(self) -> str:
        return self.line_edit.text()

    def clear(self):
        self.line_edit.clear()

    def setDisplayFormat(self, fmt: str):
        self._display_format = fmt

    def setCalendarPopup(self, val: bool):
        pass

    def setReadOnly(self, val: bool):
        self.line_edit.setReadOnly(val)
        self.btn_cal.setEnabled(not val)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self.line_edit.setEnabled(enabled)
        self.btn_cal.setEnabled(enabled)

    def abrir_calendario(self):
        """Abre o calendário interativo como popup logo abaixo do campo com efeito hover nos dias."""
        if self._popup_dialog is None:
            self._popup_dialog = QDialog(self, Qt.Popup | Qt.FramelessWindowHint)
            self._popup_dialog.setStyleSheet(CALENDAR_STYLE)
            l = QVBoxLayout(self._popup_dialog)
            l.setContentsMargins(6, 6, 6, 6)

            self._calendar = QCalendarWidget(self._popup_dialog)
            self._calendar.setGridVisible(False)
            self._calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)

            # Ativa rastreamento de mouse para permitir efeito hover nos dias do calendário
            tv = self._calendar.findChild(QTableView)
            if tv:
                tv.setMouseTracking(True)
                tv.viewport().setMouseTracking(True)

            self._calendar.clicked.connect(self._on_calendar_date_clicked)
            l.addWidget(self._calendar)
            self._popup_dialog.adjustSize()

        curr = self.date()
        if curr.isValid():
            self._calendar.setSelectedDate(curr)
        else:
            self._calendar.setSelectedDate(self._current_date)

        # Posiciona logo abaixo do input
        pos_global = self.mapToGlobal(QPoint(0, self.height() + 2))
        self._popup_dialog.move(pos_global)
        self._popup_dialog.show()

    def _on_calendar_date_clicked(self, qdate: QDate):
        self.setDate(qdate)
        if self._popup_dialog:
            self._popup_dialog.hide()
