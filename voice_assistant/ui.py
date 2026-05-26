import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QFrame, QScrollArea,
    QInputDialog,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QSize, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor

from assistant import Assistant

# ─── Palette ──────────────────────────────────────────────────────────────────
BG_DARK   = "#0d0f14"
BG_PANEL  = "#13161e"
BG_CARD   = "#1a1e2a"
ACCENT    = "#6c63ff"
ACCENT2   = "#a78bfa"
TEXT_PRI  = "#e8eaf6"
TEXT_SEC  = "#7c83a0"
SUCCESS   = "#4ade80"
DANGER    = "#f87171"
USER_BG   = "#1e1b4b"
BOT_BG    = "#13161e"
BORDER    = "#2a2d3e"


STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {BG_DARK};
    color: {TEXT_PRI};
    font-family: 'Segoe UI', 'SF Pro Display', sans-serif;
}}

/* ── Chat bubble area ── */
#chat_area {{
    background: {BG_DARK};
    border: none;
}}

/* ── Input bar ── */
#input_field {{
    background: {BG_CARD};
    color: {TEXT_PRI};
    border: 1.5px solid {BORDER};
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 14px;
}}
#input_field:focus {{
    border: 1.5px solid {ACCENT};
}}

/* ── Buttons ── */
QPushButton {{
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 20px;
}}
#send_btn {{
    background: {ACCENT};
    color: white;
    border: none;
}}
#send_btn:hover {{ background: #7c74ff; }}
#send_btn:pressed {{ background: #5a52cc; }}

#mic_btn {{
    background: {BG_CARD};
    color: {ACCENT2};
    border: 1.5px solid {BORDER};
    min-width: 46px;
    max-width: 46px;
    min-height: 46px;
    max-height: 46px;
    border-radius: 23px;
    font-size: 20px;
    padding: 0;
}}
#mic_btn:hover {{ background: #1e1b4b; border-color: {ACCENT}; }}
#mic_btn[active="true"] {{
    background: {DANGER};
    border-color: {DANGER};
    color: white;
}}

#reset_btn {{
    background: transparent;
    color: {TEXT_SEC};
    border: 1px solid {BORDER};
    padding: 6px 14px;
    font-size: 12px;
    border-radius: 8px;
}}
#reset_btn:hover {{ color: {TEXT_PRI}; border-color: {ACCENT}; }}

/* ── Status bar ── */
#status_label {{
    color: {TEXT_SEC};
    font-size: 12px;
}}

/* ── Header ── */
#header {{
    background: {BG_PANEL};
    border-bottom: 1px solid {BORDER};
}}
#title_label {{
    color: {TEXT_PRI};
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 1px;
}}
#subtitle_label {{
    color: {ACCENT2};
    font-size: 11px;
    letter-spacing: 2px;
}}

/* ── Scroll bar ── */
QScrollBar:vertical {{
    background: {BG_DARK};
    width: 6px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
"""


class BubbleWidget(QFrame):
    """A single chat bubble."""

    def __init__(self, text: str, role: str, parent=None):
        super().__init__(parent)
        self.role = role  # "user" | "assistant"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        # Role label
        role_lbl = QLabel("You" if role == "user" else "✦ Nova")
        role_lbl.setStyleSheet(
            f"color: {'#a78bfa' if role == 'user' else '#6c63ff'};"
            "font-size: 11px; font-weight: 700; letter-spacing: 1px;"
        )
        layout.addWidget(role_lbl)

        # Message text
        msg = QLabel(text)
        msg.setWordWrap(True)
        msg.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        msg.setStyleSheet(
            f"background: {USER_BG if role == 'user' else BOT_BG};"
            f"color: {TEXT_PRI};"
            "border-radius: 12px;"
            f"border: 1px solid {'#312e81' if role == 'user' else BORDER};"
            "padding: 10px 14px;"
            "font-size: 14px;"
            "line-height: 1.5;"
        )
        layout.addWidget(msg)

        # Align user bubbles to the right
        if role == "user":
            role_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            msg.setAlignment(Qt.AlignmentFlag.AlignRight)


class ChatArea(QWidget):
    """Scrollable area that holds all chat bubbles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._layout.setSpacing(6)
        self._layout.setContentsMargins(16, 16, 16, 16)

    def add_bubble(self, text: str, role: str):
        bubble = BubbleWidget(text, role)
        self._layout.addWidget(bubble)

    def clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class MainWindow(QMainWindow):
    # Signals to bridge threads → UI
    sig_user    = pyqtSignal(str)
    sig_bot     = pyqtSignal(str)
    sig_status  = pyqtSignal(str)
    sig_listen  = pyqtSignal(bool)

    def __init__(self, api_key: str):
        super().__init__()
        self.setWindowTitle("Nova — Voice Assistant")
        self.resize(780, 620)
        self.setMinimumSize(540, 480)

        # ── Assistant ──────────────────────────────────────────────────────
        self.assistant = Assistant(gemini_api_key=api_key)
        self.assistant.on_user_text       = self.sig_user.emit
        self.assistant.on_assistant_text  = self.sig_bot.emit
        self.assistant.on_status          = self.sig_status.emit
        self.assistant.on_listening_change = self.sig_listen.emit

        self.sig_user.connect(self._on_user_msg)
        self.sig_bot.connect(self._on_bot_msg)
        self.sig_status.connect(self._on_status)
        self.sig_listen.connect(self._on_listen_change)

        # ── Build UI ───────────────────────────────────────────────────────
        self._build_ui()
        self.setStyleSheet(STYLESHEET)

        # Welcome message
        QTimer.singleShot(400, lambda: self._on_bot_msg(
            "Hi! I'm Nova 👋  Ask me anything, or say 'search for…' / 'open…'"
        ))

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(64)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("NOVA")
        title.setObjectName("title_label")
        subtitle = QLabel("VOICE  ASSISTANT")
        subtitle.setObjectName("subtitle_label")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        reset_btn = QPushButton("↺  Reset")
        reset_btn.setObjectName("reset_btn")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset)

        h_layout.addLayout(title_col)
        h_layout.addStretch()
        h_layout.addWidget(reset_btn)
        root_layout.addWidget(header)

        # Chat scroll area
        self._chat_widget = ChatArea()
        scroll = QScrollArea()
        scroll.setObjectName("chat_area")
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._chat_widget)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll = scroll
        root_layout.addWidget(scroll, 1)

        # Status bar
        status_bar = QFrame()
        status_bar.setStyleSheet(f"background: {BG_PANEL}; border-top: 1px solid {BORDER};")
        status_bar.setFixedHeight(28)
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(16, 0, 16, 0)
        self._status_lbl = QLabel("Ready")
        self._status_lbl.setObjectName("status_label")
        sb_layout.addWidget(self._status_lbl)
        root_layout.addWidget(status_bar)

        # Input row
        input_frame = QFrame()
        input_frame.setStyleSheet(f"background: {BG_PANEL}; border-top: 1px solid {BORDER};")
        in_layout = QHBoxLayout(input_frame)
        in_layout.setContentsMargins(16, 12, 16, 12)
        in_layout.setSpacing(10)

        self._input = QLineEdit()
        self._input.setObjectName("input_field")
        self._input.setPlaceholderText("Type a message…")
        self._input.setFixedHeight(46)
        self._input.returnPressed.connect(self._send_text)

        self._mic_btn = QPushButton("🎙")
        self._mic_btn.setObjectName("mic_btn")
        self._mic_btn.setToolTip("Hold to speak (click to listen)")
        self._mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mic_btn.clicked.connect(self._start_listening)

        send_btn = QPushButton("Send →")
        send_btn.setObjectName("send_btn")
        send_btn.setFixedHeight(46)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._send_text)

        in_layout.addWidget(self._mic_btn)
        in_layout.addWidget(self._input, 1)
        in_layout.addWidget(send_btn)
        root_layout.addWidget(input_frame)

    # ── Slots ──────────────────────────────────────────────────────────────

    def _send_text(self):
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.assistant.process_text(text)

    def _start_listening(self):
        if not self.assistant.listening:
            self.assistant.listen_once()

    def _on_user_msg(self, text: str):
        self._chat_widget.add_bubble(text, "user")
        self._scroll_to_bottom()

    def _on_bot_msg(self, text: str):
        self._chat_widget.add_bubble(text, "assistant")
        self._scroll_to_bottom()

    def _on_status(self, msg: str):
        self._status_lbl.setText(msg)

    def _on_listen_change(self, active: bool):
        self._mic_btn.setProperty("active", "true" if active else "false")
        self._mic_btn.setStyle(self._mic_btn.style())  # force style refresh
        self._mic_btn.setText("🔴" if active else "🎙")

    def _reset(self):
        self.assistant.reset_conversation()
        self._chat_widget.clear()
        self._on_bot_msg("Conversation reset. How can I help you?")

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        ))
