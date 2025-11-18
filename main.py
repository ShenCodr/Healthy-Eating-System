"""HealthMonitor dashboard-style diet tracker (PyQt5)."""

import json
import sys
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QStackedWidget,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

DATA_FILE = Path(__file__).with_name("data.json")
CONFIG_FILE = Path(__file__).with_name("config.json")
BG_COLOR = "#F3F0EB"
SIDEBAR_BG = "#FFFFFF"
ACCENT_DARK = "#2D2D2D"
ACCENT_HONEY = "#FFD166"
TEXT_COLOR = "#333333"
DEFAULT_CREDENTIALS = {"username": "超大王", "password": "123456", "height": 170, "weight": 65}


class DataManager:
    """Lightweight JSON persistence helper."""

    @staticmethod
    def load_records() -> List[dict]:
        if not DATA_FILE.exists():
            return []
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    @staticmethod
    def save_records(records: List[dict]) -> None:
        DATA_FILE.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class ConfigManager:
    """Manage simple credential persistence."""

    @staticmethod
    def load_credentials() -> dict:
        if not CONFIG_FILE.exists():
            ConfigManager.save_credentials(DEFAULT_CREDENTIALS)
            return DEFAULT_CREDENTIALS.copy()
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        merged = DEFAULT_CREDENTIALS.copy()
        merged.update({k: v for k, v in data.items() if k in {"username", "password", "height", "weight"}})
        return merged

    @staticmethod
    def save_credentials(credentials: dict) -> None:
        payload = DEFAULT_CREDENTIALS.copy()
        payload.update({k: v for k, v in credentials.items() if k in {"username", "password", "height", "weight"}})
        CONFIG_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class AlertDialog(QDialog):
    """Rounded alert dialog with custom buttons."""

    def __init__(
        self,
        title: str,
        message: str,
        parent: Optional[QWidget] = None,
        buttons: Optional[List[Tuple[str, int]]] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setObjectName("alertDialog")
        self.setFixedWidth(360)

        layout = QVBoxLayout()
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setObjectName("alertTitle")
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setObjectName("alertMessage")

        layout.addWidget(title_label)
        layout.addWidget(message_label)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        buttons = buttons or [("确 定", QDialog.Accepted)]
        for text, code in buttons:
            button = QPushButton(text)
            button.setObjectName("alertButton")
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(partial(self.done, code))
            button_row.addWidget(button)
        layout.addLayout(button_row)

        self.setLayout(layout)
        self.setStyleSheet(
            """
            QDialog#alertDialog {
                background-color: #ffffff;
                border-radius: 18px;
            }
            QLabel#alertTitle {
                font-size: 18px;
                font-weight: 600;
                color: #1f1f1f;
            }
            QLabel#alertMessage {
                font-size: 14px;
                color: #555555;
            }
            QPushButton#alertButton {
                min-width: 88px;
                padding: 8px 16px;
                border-radius: 16px;
                border: none;
                background-color: #2D2D2D;
                color: white;
                font-weight: 600;
            }
            QPushButton#alertButton:hover {
                background-color: #454545;
            }
            QPushButton#alertButton:pressed {
                background-color: #1a1a1a;
            }
            """
        )


class LoginWindow(QDialog):
    """Minimal login window."""

    def __init__(self, credentials: Optional[dict] = None) -> None:
        super().__init__()
        self.credentials = credentials or ConfigManager.load_credentials()
        self.setWindowTitle("HealthMonitor · 登录")
        self.setFixedSize(920, 1040)
        self.setModal(True)
        self.authenticated_user = self.credentials.get("username", "admin")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(28)

        title = QLabel("HealthMonitor")
        title.setStyleSheet(
            f"color: {ACCENT_DARK}; font-size: 48px; font-weight: 600;"
        )
        subtitle = QLabel("记录专属于你的清新饮食日记")
        subtitle.setStyleSheet("color: #6b6f6e; font-size: 22px;")

        self.username_edit = QLineEdit(self.credentials.get("username", "admin"))
        self.username_edit.setPlaceholderText("请输入用户名")
        self.username_edit.setMinimumHeight(68)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("请输入密码")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setMinimumHeight(68)

        self.login_button = QPushButton("进入健康看板")
        self.login_button.setMinimumHeight(68)
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.clicked.connect(self.validate_login)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(12)
        layout.addWidget(self.username_edit)
        layout.addWidget(self.password_edit)
        layout.addStretch(1)
        layout.addWidget(self.login_button)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setLayout(layout)

        root = QVBoxLayout()
        root.setContentsMargins(32, 32, 32, 32)
        root.addStretch(1)
        root.addWidget(card)
        root.addStretch(1)
        self.setLayout(root)

        self.setStyleSheet(
            f"""
            QDialog {{ background-color: {BG_COLOR}; }}
            QFrame#loginCard {{
                background-color: #ffffff;
                border-radius: 28px;
                padding: 16px;
            }}
            QLineEdit {{
                border: 1px solid #d8d5cf;
                border-radius: 18px;
                padding: 12px 16px;
                font-size: 20px;
            }}
            QLineEdit:focus {{ border: 1px solid {ACCENT_HONEY}; }}
            QPushButton {{
                background-color: {ACCENT_DARK};
                color: white;
                border-radius: 20px;
                font-size: 20px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: #454545; }}
            QPushButton:pressed {{ background-color: #1a1a1a; }}
            """
        )

    def validate_login(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        expected_user = self.credentials.get("username", "admin")
        expected_pass = self.credentials.get("password", "123456")
        if username != expected_user:
            AlertDialog("认证失败", "用户名不正确，请重试。", self).exec_()
            return
        if password != expected_pass:
            AlertDialog("认证失败", "密码错误，请检查后再试。", self).exec_()
            return
        self.authenticated_user = username or "健康达人"
        self.accept()

    def get_username(self) -> str:
        return self.authenticated_user


class RecordDialog(QDialog):
    """Dialog for adding or editing a record."""

    def __init__(self, parent: Optional[QWidget] = None, record: Optional[dict] = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("饮食记录")
        self.setMinimumWidth(480)
        self.record = record or {}
        self.result_data: Optional[dict] = None
        self._build_ui()

    def _build_ui(self) -> None:
        form = QFormLayout()
        form.setSpacing(18)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())

        self.meal_combo = QComboBox()
        self.meal_combo.addItems(["早餐", "午餐", "晚餐"])

        self.food_edit = QLineEdit()
        self.food_edit.setPlaceholderText("如：牛油果沙拉")
        self.food_edit.setMinimumHeight(46)

        self.calorie_edit = QLineEdit()
        self.calorie_edit.setPlaceholderText("热量（大卡）")
        self.calorie_edit.setMinimumHeight(46)

        self.note_edit = QLineEdit()
        self.note_edit.setPlaceholderText("备注（可选）")
        self.note_edit.setMinimumHeight(46)

        form.addRow("日期", self.date_edit)
        form.addRow("餐别", self.meal_combo)
        form.addRow("食物", self.food_edit)
        form.addRow("热量", self.calorie_edit)
        form.addRow("备注", self.note_edit)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        cancel_btn = QPushButton("取 消")
        ok_btn = QPushButton("确 定")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.handle_accept)
        button_row.addWidget(cancel_btn)
        button_row.addWidget(ok_btn)

        wrapper = QVBoxLayout()
        wrapper.setContentsMargins(28, 28, 28, 28)
        wrapper.setSpacing(16)
        wrapper.addLayout(form)
        wrapper.addSpacing(12)
        wrapper.addLayout(button_row)
        self.setLayout(wrapper)

        if self.record:
            date_str = self.record.get("date")
            if date_str:
                date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
                if date_obj.isValid():
                    self.date_edit.setDate(date_obj)
            self.meal_combo.setCurrentText(self.record.get("meal", "早餐"))
            self.food_edit.setText(self.record.get("food", ""))
            self.calorie_edit.setText(str(self.record.get("calories", "")))
            self.note_edit.setText(self.record.get("note", ""))

        self.setStyleSheet(
            f"""
            QDialog {{ background-color: #fffdf9; border-radius: 28px; }}
            QLineEdit, QComboBox, QDateEdit {{
                border: 1px solid #dad3c8;
                border-radius: 16px;
                padding: 10px 14px;
                font-size: 15px;
            }}
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 1px solid {ACCENT_HONEY};
            }}
            QPushButton {{
                min-width: 96px;
                border-radius: 18px;
                padding: 10px 16px;
            }}
            QPushButton:last-child {{ background-color: {ACCENT_DARK}; color: white; }}
            QPushButton:first-child {{ background-color: #f1ece4; color: #555555; }}
            """
        )

    def handle_accept(self) -> None:
        food = self.food_edit.text().strip()
        calorie_text = self.calorie_edit.text().strip()

        if not food:
            AlertDialog("数据缺失", "请填写食物名称。", self).exec_()
            return

        if not calorie_text.isdigit():
            AlertDialog("格式错误", "热量需为数字，请重新输入。", self).exec_()
            return

        self.result_data = {
            "date": self.date_edit.date().toString("yyyy-MM-dd"),
            "meal": self.meal_combo.currentText(),
            "food": food,
            "calories": int(calorie_text),
            "note": self.note_edit.text().strip(),
        }
        self.accept()



class MainWindow(QMainWindow):
    """Dashboard style main window with sidebar navigation."""

    def __init__(self, username: str = "健康达人", credentials: Optional[dict] = None) -> None:
        super().__init__()
        self.username = username or "健康达人"
        self.records: List[dict] = DataManager.load_records()
        self.target_calories = 2000
        self.credentials = credentials or ConfigManager.load_credentials()

        self.setWindowTitle("HealthMonitor Dashboard")
        self.resize(1700, 1100)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.nav_buttons: List[QPushButton] = []
        self.stack: Optional[QStackedWidget] = None
        self.table: Optional[QTableWidget] = None
        self.recent_table: Optional[QTableWidget] = None
        self.calorie_progress: Optional[QProgressBar] = None
        self.calorie_label: Optional[QLabel] = None
        self.body_label: Optional[QLabel] = None
        self.greeting_label: Optional[QLabel] = None
        self.tip_label: Optional[QLabel] = None
        self.calorie_delta_label: Optional[QLabel] = None
        self.name_input: Optional[QLineEdit] = None
        self.target_spin: Optional[QSpinBox] = None
        self.height_spin: Optional[QSpinBox] = None
        self.weight_spin: Optional[QSpinBox] = None
        self.old_password_input: Optional[QLineEdit] = None
        self.new_password_input: Optional[QLineEdit] = None
        self.confirm_password_input: Optional[QLineEdit] = None
        self.highlight_labels: Dict[str, QLabel] = {}
        self.pref_stat_labels: Dict[str, QLabel] = {}

        self._build_ui()
        self.apply_style()
        self.refresh_all()

    def _build_ui(self) -> None:
        container = QWidget()
        root = QHBoxLayout()
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_dashboard_page())
        self.stack.addWidget(self._build_diet_page())
        self.stack.addWidget(self._build_settings_page())
        root.addWidget(self.stack, 1)

        container.setLayout(root)
        self.setCentralWidget(container)
        self.switch_page(0)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(16)

        logo = QLabel("HealthMonitor")
        logo.setObjectName("sidebarLogo")
        layout.addWidget(logo)
        layout.addSpacing(12)

        nav_items = [
            ("🏠 概览", 0),
            ("🍽️ 饮食记录", 1),
            ("⚙️ 设置", 2),
        ]
        for text, index in nav_items:
            button = QPushButton(text)
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            button.setObjectName("navButton")
            button.clicked.connect(partial(self.switch_page, index))
            self.nav_buttons.append(button)
            layout.addWidget(button)

        layout.addStretch(1)

        logout_btn = QPushButton("🚪 退出登录")
        logout_btn.setObjectName("logoutButton")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self.handle_logout)
        layout.addWidget(logout_btn)

        sidebar.setLayout(layout)
        return sidebar

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        layout.addWidget(self._build_dashboard_header())
        layout.addWidget(self._build_highlight_row())

        cards = QGridLayout()
        cards.setSpacing(20)
        cards.addWidget(self._build_calorie_card(), 0, 0)
        cards.addWidget(self._build_recent_card(), 0, 1)
        cards.addWidget(self._build_body_card(), 1, 0, 1, 2)
        layout.addLayout(cards)

        page.setLayout(layout)
        return page

    def _build_dashboard_header(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("headerCard")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(24, 24, 24, 24)

        text_block = QVBoxLayout()
        self.greeting_label = QLabel(f"Hi, {self.username}! 今天感觉如何？")
        self.greeting_label.setObjectName("headline")
        note_label = QLabel("小步慢行，也能收获闪闪发光的自己。")
        note_label.setObjectName("subline")
        text_block.addWidget(self.greeting_label)
        text_block.addWidget(note_label)
        header_layout.addLayout(text_block)

        header_layout.addStretch(1)

        hero_visual = QLabel("🥗")
        hero_visual.setObjectName("heroEmoji")
        hero_visual.setFixedSize(160, 160)
        hero_visual.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(hero_visual)

        add_btn = QPushButton("＋ 记一笔")
        add_btn.setObjectName("primaryCta")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setMinimumSize(150, 60)
        add_btn.clicked.connect(self.add_record)
        header_layout.addWidget(add_btn)

        frame.setLayout(header_layout)
        self._apply_card_shadow(frame)
        return frame

    def _build_highlight_row(self) -> QWidget:
        wrapper = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        chips = [
            ("本周打卡天数", "week", "📅"),
            ("今日餐次", "today", "🍱"),
            ("累计记录", "total", "📓"),
        ]
        for title, key, emoji in chips:
            card = self._create_highlight_card(title, key, emoji)
            layout.addWidget(card, 1)

        wrapper.setLayout(layout)
        return wrapper

    def _create_highlight_card(self, title: str, key: str, emoji: str) -> QWidget:
        frame = QFrame()
        frame.setObjectName("miniCard")
        box = QVBoxLayout()
        box.setContentsMargins(20, 18, 20, 18)
        box.setSpacing(4)

        emoji_label = QLabel(emoji)
        emoji_label.setObjectName("chipEmoji")
        emoji_label.setAlignment(Qt.AlignLeft)
        text_label = QLabel(title)
        text_label.setObjectName("chipTitle")
        value_label = QLabel("--")
        value_label.setObjectName("chipValue")

        box.addWidget(emoji_label)
        box.addWidget(text_label)
        box.addWidget(value_label)

        frame.setLayout(box)
        self.highlight_labels[key] = value_label
        self._apply_card_shadow(frame)
        return frame

    def _create_pref_chip(self, title: str, key: str) -> QWidget:
        frame = QFrame()
        frame.setObjectName("prefChip")
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        label = QLabel(title)
        label.setObjectName("chipTitle")
        value = QLabel("--")
        value.setObjectName("chipValue")

        layout.addWidget(label)
        layout.addWidget(value)
        frame.setLayout(layout)
        self.pref_stat_labels[key] = value
        return frame

    def _build_calorie_card(self) -> QWidget:
        card = self._card_frame()
        layout = card.layout()

        title = QLabel("今日热量概览")
        title.setObjectName("cardTitle")
        self.calorie_label = QLabel("已摄入 0 kcal / 目标 2000 kcal")
        self.calorie_label.setObjectName("cardValue")

        self.calorie_progress = QProgressBar()
        self.calorie_progress.setRange(0, self.target_calories)
        self.calorie_progress.setTextVisible(False)
        self.calorie_progress.setFixedHeight(20)

        self.calorie_delta_label = QLabel("距离目标还剩 0 kcal")
        self.calorie_delta_label.setObjectName("cardSubtitle")

        layout.addWidget(title)
        layout.addSpacing(8)
        layout.addWidget(self.calorie_label)
        layout.addWidget(self.calorie_delta_label)
        layout.addSpacing(12)
        layout.addWidget(self.calorie_progress)

        return card

    def _build_recent_card(self) -> QWidget:
        card = self._card_frame()
        layout = card.layout()

        header = QHBoxLayout()
        title = QLabel("最近记录")
        title.setObjectName("cardTitle")
        header.addWidget(title)
        header.addStretch(1)
        layout.addLayout(header)

        self.recent_table = QTableWidget(0, 5)
        self.recent_table.setHorizontalHeaderLabels(
            ["日期", "餐别", "食物", "热量", "操作"]
        )
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setFixedHeight(240)
        self.recent_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.recent_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.recent_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.recent_table)
        return card

    def _build_body_card(self) -> QWidget:
        card = self._card_frame()
        layout = card.layout()

        title = QLabel("身体数据 / 轻盈计划")
        title.setObjectName("cardTitle")
        self.body_label = QLabel("体重 65kg · BMI 22.5 · 状态平稳")
        self.body_label.setObjectName("bodyText")
        self.tip_label = QLabel("坚持记录，让健康在日常里慢慢生长。")
        self.tip_label.setObjectName("cardSubtitle")

        layout.addWidget(title)
        layout.addSpacing(6)
        layout.addWidget(self.body_label)
        layout.addSpacing(4)
        layout.addWidget(self.tip_label)
        return card

    def _build_diet_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)

        header = QHBoxLayout()
        title = QLabel("饮食记录列表")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch(1)
        add_btn = QPushButton("＋ 记一笔")
        add_btn.setObjectName("ghostButton")
        add_btn.clicked.connect(self.add_record)
        header.addWidget(add_btn)
        layout.addLayout(header)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "日期",
            "餐别",
            "食物",
            "热量 (kcal)",
            "备注",
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemDoubleClicked.connect(self.edit_selected_record)
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        edit_btn = QPushButton("编辑选中")
        edit_btn.setObjectName("ghostButton")
        edit_btn.clicked.connect(self.edit_selected_record)
        delete_btn = QPushButton("删除选中")
        delete_btn.setObjectName("ghostDanger")
        delete_btn.clicked.connect(self.delete_selected_record)
        action_row.addWidget(edit_btn)
        action_row.addWidget(delete_btn)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        page.setLayout(layout)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        layout.addWidget(self._build_preferences_card())
        layout.addWidget(self._build_password_card())
        page.setLayout(layout)
        return page

    def _build_preferences_card(self) -> QWidget:
        card = self._card_frame()
        layout = card.layout()
        layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(16)

        title = QLabel("个性化偏好")
        title.setObjectName("cardTitle")
        subtitle = QLabel("更新昵称、每日热量目标，并查看你的健康里程。")
        subtitle.setObjectName("cardSubtitle")

        self.name_input = QLineEdit(self.username)
        self.name_input.setPlaceholderText("展示名称")

        self.target_spin = QSpinBox()
        self.target_spin.setRange(1000, 4000)
        self.target_spin.setSingleStep(100)
        self.target_spin.setValue(self.target_calories)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 250)
        self.height_spin.setSingleStep(1)
        self.height_spin.setSuffix(" cm")
        self.height_spin.setValue(self.credentials.get("height", 170))

        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(30, 200)
        self.weight_spin.setSingleStep(1)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.setValue(self.credentials.get("weight", 65))

        form_layout.addRow("昵称", self.name_input)
        form_layout.addRow("每日热量目标", self.target_spin)
        form_layout.addRow("身高", self.height_spin)
        form_layout.addRow("体重", self.weight_spin)

        save_btn = QPushButton("保存设置")
        save_btn.setObjectName("primaryCta")
        save_btn.clicked.connect(self.save_settings)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        stats = [
            ("累计记录", "pref_total"),
            ("本周打卡", "pref_week"),
            ("今日热量", "pref_today"),
        ]
        for label, key in stats:
            chip = self._create_pref_chip(label, key)
            stats_row.addWidget(chip, 1)

        tips_box = QVBoxLayout()
        tips_box.setSpacing(6)
        tips_title = QLabel("健康提示")
        tips_title.setObjectName("chipTitle")
        tips_box.addWidget(tips_title)
        for tip in [
            "保持饮水量 ≥ 1500ml",
            "晚间控制精制碳水",
            "进餐前先记录有助于坚持",
        ]:
            lbl = QLabel(f"• {tip}")
            lbl.setObjectName("cardSubtitle")
            tips_box.addWidget(lbl)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(6)
        layout.addLayout(stats_row)
        layout.addSpacing(10)
        layout.addLayout(form_layout)
        layout.addWidget(save_btn, alignment=Qt.AlignRight)
        layout.addSpacing(8)
        layout.addLayout(tips_box)
        return card

    def _build_password_card(self) -> QWidget:
        card = self._card_frame()
        layout = card.layout()

        title = QLabel("修改密码")
        title.setObjectName("cardTitle")
        layout.addWidget(title)
        layout.addSpacing(4)
        helper = QLabel("新密码至少 6 位，且需不同于旧密码。")
        helper.setObjectName("subline")
        layout.addWidget(helper)

        form = QFormLayout()
        form.setSpacing(16)

        self.old_password_input = QLineEdit()
        self.old_password_input.setEchoMode(QLineEdit.Password)
        self.old_password_input.setPlaceholderText("请输入旧密码")

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("请输入新密码，不少于6位")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("请再次输入新密码")

        form.addRow("旧密码", self.old_password_input)
        form.addRow("新密码", self.new_password_input)
        form.addRow("确认新密码", self.confirm_password_input)
        layout.addLayout(form)

        change_btn = QPushButton("更新密码")
        change_btn.setObjectName("ghostButton")
        change_btn.clicked.connect(self.handle_password_change)
        layout.addSpacing(8)
        layout.addWidget(change_btn, alignment=Qt.AlignRight)
        return card

    def _card_frame(self) -> QFrame:
        card = QFrame()
        card.setObjectName("dashboardCard")
        card.setLayout(QVBoxLayout())
        card.layout().setContentsMargins(24, 24, 24, 24)
        card.layout().setSpacing(8)
        self._apply_card_shadow(card)
        return card

    @staticmethod
    def _apply_card_shadow(widget: QWidget) -> None:
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setOffset(0, 18)
        shadow.setColor(QColor(0, 0, 0, 30))
        widget.setGraphicsEffect(shadow)

    def switch_page(self, index: int) -> None:
        if not self.stack:
            return
        self.stack.setCurrentIndex(index)
        for idx, btn in enumerate(self.nav_buttons):
            btn.setChecked(idx == index)

    def add_record(self) -> None:
        dialog = RecordDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            self.records.append(dialog.result_data)
            DataManager.save_records(self.records)
            self.refresh_all()

    def current_row(self) -> int:
        if not self.table:
            return -1
        return self.table.currentRow()

    def edit_record_by_index(self, index: int) -> None:
        if index < 0 or index >= len(self.records):
            return
        dialog = RecordDialog(self, self.records[index])
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            self.records[index] = dialog.result_data
            DataManager.save_records(self.records)
            self.refresh_all()

    def delete_record_by_index(self, index: int) -> None:
        if index < 0 or index >= len(self.records):
            return
        confirm = AlertDialog(
            "确认删除",
            "确定要删除这条饮食记录吗？",
            self,
            buttons=[("取 消", QDialog.Rejected), ("删 除", QDialog.Accepted)],
        )
        if confirm.exec_() == QDialog.Accepted:
            self.records.pop(index)
            DataManager.save_records(self.records)
            self.refresh_all()

    def edit_selected_record(self) -> None:
        row = self.current_row()
        if row < 0:
            AlertDialog("温馨提示", "请选择一条记录进行编辑。", self).exec_()
            return
        self.edit_record_by_index(row)

    def delete_selected_record(self) -> None:
        row = self.current_row()
        if row < 0:
            AlertDialog("温馨提示", "请选择要删除的记录。", self).exec_()
            return
        self.delete_record_by_index(row)

    def populate_table(self) -> None:
        if not self.table:
            return
        self.table.setRowCount(len(self.records))
        for row, record in enumerate(self.records):
            self.table.setItem(row, 0, QTableWidgetItem(record.get("date", "")))
            self.table.setItem(row, 1, QTableWidgetItem(record.get("meal", "")))
            self.table.setItem(row, 2, QTableWidgetItem(record.get("food", "")))
            self.table.setItem(row, 3, QTableWidgetItem(str(record.get("calories", ""))))
            self.table.setItem(row, 4, QTableWidgetItem(record.get("note", "")))
        self.table.resizeColumnsToContents()
        self.status_bar.showMessage(f"共 {len(self.records)} 条记录", 4000)

    def refresh_recent_records(self) -> None:
        if not self.recent_table:
            return
        indexed = list(enumerate(self.records))
        latest = list(reversed(indexed[-4:]))
        self.recent_table.setRowCount(len(latest))
        for row, (idx, record) in enumerate(latest):
            self.recent_table.setItem(row, 0, QTableWidgetItem(record.get("date", "")))
            self.recent_table.setItem(row, 1, QTableWidgetItem(record.get("meal", "")))
            self.recent_table.setItem(row, 2, QTableWidgetItem(record.get("food", "")))
            self.recent_table.setItem(row, 3, QTableWidgetItem(str(record.get("calories", ""))))
            self.recent_table.setCellWidget(row, 4, self._action_cell(idx))
        self.recent_table.resizeColumnsToContents()

    def _action_cell(self, index: int) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        edit_btn = QPushButton("✏️")
        edit_btn.setObjectName("miniIcon")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_record_by_index(index))

        delete_btn = QPushButton("🗑️")
        delete_btn.setObjectName("miniIcon")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_record_by_index(index))

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        layout.addStretch(1)
        widget.setLayout(layout)
        return widget

    def update_calorie_summary(self) -> None:
        if not self.calorie_progress or not self.calorie_label:
            return
        today = QDate.currentDate().toString("yyyy-MM-dd")
        today_total = sum(
            record.get("calories", 0) for record in self.records if record.get("date") == today
        )
        self.calorie_progress.setMaximum(self.target_calories)
        self.calorie_progress.setValue(min(today_total, self.target_calories))
        self.calorie_label.setText(
            f"已摄入 {today_total} kcal / 目标 {self.target_calories} kcal"
        )
        if self.calorie_delta_label:
            remaining = self.target_calories - today_total
            if remaining > 0:
                self.calorie_delta_label.setText(f"距离目标还剩 {remaining} kcal")
            else:
                extra = abs(remaining)
                self.calorie_delta_label.setText(f"已超出 {extra} kcal，记得适度运动哦")

    def update_highlights(self) -> None:
        if not self.highlight_labels:
            return
        today = QDate.currentDate()
        week_start = today.addDays(-6)
        week_days = set()
        today_meals = 0
        for record in self.records:
            date_str = record.get("date", "")
            date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
            if not date_obj.isValid():
                continue
            if week_start <= date_obj <= today:
                week_days.add(date_obj.toString("yyyy-MM-dd"))
            if date_obj == today:
                today_meals += 1
        if label := self.highlight_labels.get("week"):
            label.setText(f"{len(week_days)} 天")
        if label := self.highlight_labels.get("today"):
            label.setText(f"{today_meals} 餐")
        if label := self.highlight_labels.get("total"):
            label.setText(f"{len(self.records)} 条")

    def update_preference_summary(self) -> None:
        if not self.pref_stat_labels:
            return
        if label := self.pref_stat_labels.get("pref_total"):
            label.setText(f"{len(self.records)} 条")
        today = QDate.currentDate()
        week_start = today.addDays(-6)
        week_days = set()
        today_total = 0
        for record in self.records:
            date_str = record.get("date", "")
            date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
            if not date_obj.isValid():
                continue
            if week_start <= date_obj <= today:
                week_days.add(date_obj.toString("yyyy-MM-dd"))
            if date_obj == today:
                today_total += record.get("calories", 0)
        if label := self.pref_stat_labels.get("pref_week"):
            label.setText(f"{len(week_days)} 天")
        if label := self.pref_stat_labels.get("pref_today"):
            label.setText(f"{today_total} kcal")

    def update_body_insight(self) -> None:
        if not self.tip_label:
            return
        if not self.records:
            self.tip_label.setText("今日还没有记录，来记一笔早餐吧！")
            return
        latest = self.records[-1]
        food = latest.get("food", "美味食物")
        meal = latest.get("meal", "餐次")
        cal = latest.get("calories", 0)
        self.tip_label.setText(f"最新记录 · {meal} · {food} · {cal} kcal")

    def update_body_card(self) -> None:
        if not self.body_label:
            return
        height = self.credentials.get("height", 170)
        weight = self.credentials.get("weight", 65)
        bmi = weight / ((height / 100) ** 2)
        if bmi < 18.5:
            status = "偏瘦"
        elif bmi < 24:
            status = "正常"
        elif bmi < 28:
            status = "超重"
        else:
            status = "肥胖"
        self.body_label.setText(f"身高 {height}cm · 体重 {weight}kg · BMI {bmi:.1f} · {status}")

    def handle_logout(self) -> None:
        dialog = AlertDialog(
            "退出登录",
            "确定要退出到登录页吗？",
            self,
            buttons=[("取 消", QDialog.Rejected), ("退 出", QDialog.Accepted)],
        )
        if dialog.exec_() == QDialog.Accepted:
            self.hide()
            credentials = ConfigManager.load_credentials()
            login = LoginWindow(credentials)
            if login.exec_() == QDialog.Accepted:
                self.username = login.get_username()
                self.credentials = ConfigManager.load_credentials()
                self.show()
                self._apply_user_preferences()
            else:
                QApplication.instance().quit()

    def _apply_user_preferences(self) -> None:
        if self.greeting_label:
            self.greeting_label.setText(f"Hi, {self.username}! 今天感觉如何？")
        if self.name_input:
            self.name_input.setText(self.username)
        self.switch_page(0)
        self.refresh_all()

    def save_settings(self) -> None:
        if self.name_input:
            self.username = self.name_input.text().strip() or self.username
        if self.target_spin:
            self.target_calories = self.target_spin.value()
        if self.height_spin:
            self.credentials["height"] = self.height_spin.value()
        if self.weight_spin:
            self.credentials["weight"] = self.weight_spin.value()
        ConfigManager.save_credentials(self.credentials)
        self._apply_user_preferences()
        AlertDialog("已保存", "设置已更新，继续加油！", self).exec_()

    def handle_password_change(self) -> None:
        if not all([
            self.old_password_input,
            self.new_password_input,
            self.confirm_password_input,
        ]):
            return
        old = self.old_password_input.text()
        new = self.new_password_input.text()
        confirm = self.confirm_password_input.text()
        stored = self.credentials.get("password", DEFAULT_CREDENTIALS["password"])

        if old != stored:
            AlertDialog("旧密码错误", "请输入正确的旧密码。", self).exec_()
            return
        if len(new) < 6:
            AlertDialog("新密码无效", "新密码至少需要 6 位字符。", self).exec_()
            return
        if new == stored:
            AlertDialog("新密码无效", "新密码需与旧密码不同。", self).exec_()
            return
        if new != confirm:
            AlertDialog("两次输入不一致", "请确保两次输入的新密码相同。", self).exec_()
            return

        self.credentials["password"] = new
        ConfigManager.save_credentials(self.credentials)
        AlertDialog("修改成功", "密码已更新，请牢记新密码。", self).exec_()
        self.old_password_input.clear()
        self.new_password_input.clear()
        self.confirm_password_input.clear()

    def refresh_all(self) -> None:
        self.populate_table()
        self.refresh_recent_records()
        self.update_calorie_summary()
        self.update_highlights()
        self.update_preference_summary()
        self.update_body_insight()
        self.update_body_card()

    def apply_style(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {BG_COLOR};
                color: {TEXT_COLOR};
                font-family: 'Microsoft YaHei UI';
            }}
            QFrame#sidebar {{
                background-color: {SIDEBAR_BG};
                border-top-right-radius: 32px;
                border-bottom-right-radius: 32px;
            }}
            QLabel#sidebarLogo {{
                font-size: 20px;
                font-weight: 700;
                color: {ACCENT_DARK};
            }}
            QPushButton#navButton {{
                border-radius: 18px;
                padding: 12px 18px;
                text-align: left;
                background-color: transparent;
                font-size: 15px;
            }}
            QPushButton#navButton:checked {{
                background-color: rgba(45,45,45,0.08);
                font-weight: 600;
            }}
            QPushButton#logoutButton {{
                border-radius: 18px;
                padding: 12px 18px;
                background-color: rgba(255,209,102,0.25);
                font-weight: 600;
            }}
            QFrame#headerCard {{
                background-color: {ACCENT_DARK};
                border-radius: 28px;
            }}
            QLabel#headline {{ color: #ffffff; font-size: 26px; font-weight: 600; }}
            QLabel#subline {{ color: rgba(255,255,255,0.8); font-size: 18px; }}
            QPushButton#primaryCta {{
                background-color: {ACCENT_HONEY};
                color: {ACCENT_DARK};
                border-radius: 22px;
                font-size: 16px;
                font-weight: 700;
            }}
            QPushButton#primaryCta:hover {{ background-color: #ffdd88; }}
            QFrame#dashboardCard {{
                background-color: #ffffff;
                border-radius: 28px;
            }}
            QLabel#cardTitle {{ font-weight: 600; font-size: 16px; }}
            QLabel#cardValue {{ font-size: 28px; font-weight: 700; color: {ACCENT_DARK}; }}
            QLabel#cardSubtitle {{ font-size: 14px; color: #6b6f6e; }}
            QLabel#bodyText {{ font-size: 18px; font-weight: 600; }}
            QLabel#sectionTitle {{ font-size: 22px; font-weight: 700; }}
            QLabel#heroEmoji {{ font-size: 70px; }}
            QFrame#miniCard {{
                background-color: #ffffff;
                border-radius: 24px;
            }}
            QFrame#prefChip {{
                background-color: rgba(0,0,0,0.02);
                border-radius: 20px;
            }}
            QLabel#chipTitle {{ font-size: 14px; color: #7c7f7e; }}
            QLabel#chipValue {{ font-size: 22px; font-weight: 700; color: {ACCENT_DARK}; }}
            QLabel#chipEmoji {{ font-size: 32px; }}
            QPushButton#ghostButton {{
                background-color: #ffffff;
                border: 1px solid rgba(45,45,45,0.2);
                border-radius: 18px;
                padding: 8px 16px;
            }}
            QPushButton#ghostButton:hover {{ background-color: rgba(0,0,0,0.03); }}
            QPushButton#ghostDanger {{
                background-color: #ffecec;
                border-radius: 18px;
                padding: 8px 16px;
                color: #c62828;
            }}
            QPushButton#ghostDanger:hover {{ background-color: #ffdada; }}
            QPushButton#miniIcon {{
                border: none;
                background-color: rgba(0,0,0,0.05);
                border-radius: 12px;
                padding: 4px 10px;
            }}
            QTableWidget {{
                background-color: #ffffff;
                border: none;
                border-radius: 20px;
                padding: 8px;
                gridline-color: rgba(0,0,0,0.05);
            }}
            QHeaderView::section {{
                background-color: rgba(0,0,0,0.05);
                border: none;
                padding: 10px;
                font-weight: 600;
            }}
            QProgressBar {{
                background-color: rgba(0,0,0,0.08);
                border-radius: 10px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT_HONEY};
                border-radius: 10px;
            }}
            QLineEdit {{
                border-radius: 18px;
                border: 1px solid rgba(0,0,0,0.1);
                padding: 10px 14px;
            }}
            QSpinBox {{
                border-radius: 18px;
                border: 1px solid rgba(0,0,0,0.1);
                padding: 6px 12px;
            }}
            """
        )


def main() -> None:
    app = QApplication(sys.argv)
    credentials = ConfigManager.load_credentials()
    login = LoginWindow(credentials)
    if login.exec_() == QDialog.Accepted:
        window = MainWindow(login.get_username(), ConfigManager.load_credentials())
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
