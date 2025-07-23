import sys
import json
import time
import threading
from pathlib import Path
import psutil
import win32gui
import win32process
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtCore import pyqtSignal as Signal
QT_BINDING = "PyQt5"
    
def exec_dialog(dialog):
    return dialog.exec_() if QT_BINDING == "PyQt5" else dialog.exec()

class ClickableLabel(QLabel):
    clicked = Signal()
    
    def mousePressEvent(self, event):
        self.clicked.emit()

class StatusThread(QThread):
    status_update = Signal(str, str)
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.running = True
        
    def run(self):
        while self.running:
            try:
                if self.parent.is_roblox_focused():
                    self.status_update.emit("🎮 Roblox Focused - Macros Active", "green")
                else:
                    self.status_update.emit("❌ Focus Roblox to use macros", "red")
            except:
                pass
            time.sleep(1)
            
    def stop(self):
        self.running = False

class KeybindCaptureDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Capture Keybind")
        self.setFixedSize(350, 150)
        self.captured_key = None
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        self.info_label = QLabel("Press any key or mouse button...")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-size: 14px; color: #00d4ff;")
        layout.addWidget(self.info_label)
        
        self.current_key_label = QLabel("")
        self.current_key_label.setAlignment(Qt.AlignCenter)
        self.current_key_label.setStyleSheet("font-size: 12px; color: #ffffff; font-weight: bold;")
        layout.addWidget(self.current_key_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        self.ok_btn.setEnabled(False)
        button_layout.addWidget(self.ok_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        self.installEventFilter(self)
        self.setFocus()
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            key = event.key()
            
            if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
                return True
                
            key_sequence = QKeySequence(key)
            key_name = key_sequence.toString()
            
            key_map = {
                Qt.Key_Space: "space", Qt.Key_Tab: "tab", Qt.Key_Return: "enter",
                Qt.Key_Enter: "enter", Qt.Key_Escape: "escape", Qt.Key_Backspace: "backspace",
                Qt.Key_Delete: "delete", Qt.Key_Up: "up", Qt.Key_Down: "down",
                Qt.Key_Left: "left", Qt.Key_Right: "right"
            }
            
            if key in key_map:
                key_name = key_map[key]
            elif key_name == "":
                key_name = event.text().lower() if event.text() else f"key_{key}"
            
            self.captured_key = key_name.lower()
            self.current_key_label.setText(f"Key: {self.captured_key}")
            self.ok_btn.setEnabled(True)
            return True
            
        elif event.type() == QEvent.MouseButtonPress:
            button = event.button()
            button_map = {
                Qt.LeftButton: "mouse_left", Qt.RightButton: "mouse_right",
                Qt.MiddleButton: "mouse_middle", Qt.XButton1: "mouse_x1", Qt.XButton2: "mouse_x2"
            }
            
            if button in button_map:
                self.captured_key = button_map[button]
                self.current_key_label.setText(f"Mouse: {self.captured_key.replace('mouse_', '').title()} Button")
                self.ok_btn.setEnabled(True)
                return True
        
        return super().eventFilter(obj, event)
    
    def keyPressEvent(self, event):
        event.accept()

class MacroWidget(QWidget):
    def __init__(self, macro_key, macro_data, parent=None):
        super().__init__(parent)
        self.macro_key = macro_key
        self.macro_data = macro_data
        self.parent_gui = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("macroWidget")
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        self.name_label = QLabel(self.macro_data["name"])
        self.name_label.setObjectName("macroNameLabel")
        self.name_label.setMinimumWidth(200)
        layout.addWidget(self.name_label, 3)
        
        self.keybind_btn = QPushButton("None")
        self.keybind_btn.setObjectName("keybindButton")
        self.keybind_btn.setMinimumWidth(100)
        self.keybind_btn.setMaximumWidth(120)
        self.keybind_btn.clicked.connect(self.change_keybind)
        layout.addWidget(self.keybind_btn, 1)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.setMinimumWidth(70)
        self.clear_btn.setMaximumWidth(80)
        self.clear_btn.clicked.connect(self.clear_keybind)
        layout.addWidget(self.clear_btn, 1)
        
        self.setLayout(layout)
        self.update_display()
        
    def update_display(self):
        keybind = self.macro_data.get("keybind")
        if keybind:
            display_name = keybind.replace("mouse_", "Mouse ").replace("_", " ").title()
            self.keybind_btn.setText(display_name)
        else:
            self.keybind_btn.setText("None")
        
    def change_keybind(self):
        dialog = KeybindCaptureDialog(self)
        if exec_dialog(dialog) == QDialog.Accepted and dialog.captured_key:
            for macro_key, macro_data in self.parent_gui.macros.items():
                if macro_key != self.macro_key and macro_data.get("keybind") == dialog.captured_key:
                    QMessageBox.warning(self, "Keybind In Use", 
                                      f"This keybind is already assigned to {macro_data['name']}.\n"
                                      f"Please choose a different key.")
                    return
            
            self.macro_data["keybind"] = dialog.captured_key
            self.update_display()
            if self.parent_gui:
                self.parent_gui.save_settings()
                self.parent_gui.setup_hotkeys()
                
    def clear_keybind(self):
        self.macro_data["keybind"] = None
        self.update_display()
        if self.parent_gui:
            self.parent_gui.save_settings()
            self.parent_gui.setup_hotkeys()

class ItemSettingWidget(QWidget):
    def __init__(self, item_name, item_key, parent=None):
        super().__init__(parent)
        self.item_name = item_name
        self.item_key = item_key
        self.parent_gui = parent
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("itemWidget")
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(15)
        
        name_label = QLabel(self.item_name)
        name_label.setObjectName("itemNameLabel")
        name_label.setMinimumWidth(150)
        layout.addWidget(name_label, 2)
        
        self.key_input = QLineEdit()
        self.key_input.setObjectName("keyInput")
        self.key_input.setMaximumWidth(80)
        self.key_input.setAlignment(Qt.AlignCenter)
        self.key_input.textChanged.connect(self.on_key_changed)
        layout.addWidget(self.key_input, 1)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def on_key_changed(self, text):
        if self.parent_gui:
            self.parent_gui.item_keys[self.item_key] = text
            self.parent_gui.save_settings()
            
    def set_value(self, value):
        self.key_input.setText(str(value))

class MM2MacroGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Seven's MM2 Macro v2.1")
        
        self.kb_controller = pynput_keyboard.Controller()
        self.mouse_controller = pynput_mouse.Controller()

        
        self.settings_dir = Path("C:/Seven's Scripts/Seven's mm2 Macro")
        self.settings_file = self.settings_dir / "settings.json"
        
        self.settings = {
            "window": {"width": 650, "height": 550, "x": None, "y": None},
            "ui": {"always_on_top": False, "macros_enabled": True},
            "keybinds": {},
            "item_keys": {"gg_sign": "6", "prank_bomb": "7"}
        }
        
        self.macros = {
            "quick_setup": {"name": "Quick Setup", "keybind": None, "active": False},
            "gg_sign_clip": {"name": "GG Sign Clip", "keybind": None, "active": False},
            "bouncy_twirl": {"name": "Bouncy Twirl Clip", "keybind": None, "active": False},
            "flex_walk": {"name": "Flex Walk Clip", "keybind": None, "active": False},
            "bomb_jump": {"name": "Bomb Jump", "keybind": None, "active": False},
            "bouncy_twirl_speed_glitch": {"name": "Bouncy Twirl Speed Glitch", "keybind": None, "active": False},
            "flex_walk_speed_glitch": {"name": "Flex Walk Speed Glitch", "keybind": None, "active": False}
        }
        
        self.item_keys = {"gg_sign": "6", "prank_bomb": "7"}
        self.gg_sign_thread = None
        self.gg_sign_running = False
        self.active_listeners = []
        self.macros_enabled = True
        
        self.load_settings()
        
        self.resize(self.settings["window"]["width"], self.settings["window"]["height"])
        self.setMinimumSize(600, 450)
        
        if self.settings["window"]["x"] is not None and self.settings["window"]["y"] is not None:
            self.move(self.settings["window"]["x"], self.settings["window"]["y"])
        
        self.macros_enabled = self.settings["ui"]["macros_enabled"]
        
        self.setup_ui()
        self.setup_style()
        self.apply_loaded_settings()
        
        QTimer.singleShot(100, self.setup_hotkeys)
        
        self.status_thread = StatusThread(self)
        self.status_thread.status_update.connect(self.update_focus_status)
        self.status_thread.start()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 15, 20, 15)
        
        title_label = QLabel("Seven's MM2 Macro")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(8)
        
        self.always_on_top_cb = QCheckBox("Always On Top")
        self.always_on_top_cb.setObjectName("alwaysOnTopCb")
        self.always_on_top_cb.toggled.connect(self.toggle_always_on_top)
        controls_layout.addWidget(self.always_on_top_cb)
        
        self.toggle_macros_btn = QPushButton("Disable Macros")
        self.toggle_macros_btn.setObjectName("toggleButton")
        self.toggle_macros_btn.clicked.connect(self.toggle_macros)
        controls_layout.addWidget(self.toggle_macros_btn)
        
        header_layout.addLayout(controls_layout)
        main_layout.addWidget(header_frame)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("tabWidget")
        
        self.setup_macros_tab()
        self.setup_settings_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        status_frame = QFrame()
        status_frame.setObjectName("statusFrame")
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 12, 15, 12)
        
        self.status_label = QLabel("Macros Enabled")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        self.focus_label = QLabel("Checking focus...")
        self.focus_label.setObjectName("focusLabel")
        self.focus_label.setAlignment(Qt.AlignCenter)
        
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.focus_label)
        
        main_layout.addWidget(status_frame)
        
        credits_label = ClickableLabel("Made by Seven | Click for GitHub")
        credits_label.setObjectName("creditsLabel")
        credits_label.setAlignment(Qt.AlignCenter)
        credits_label.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com")))
        main_layout.addWidget(credits_label)
        
    def setup_macros_tab(self):
        macros_widget = QWidget()
        macros_layout = QVBoxLayout(macros_widget)
        macros_layout.setContentsMargins(15, 15, 15, 15)
        
        headers_frame = QFrame()
        headers_frame.setObjectName("headersFrame")
        headers_layout = QHBoxLayout(headers_frame)
        headers_layout.setContentsMargins(15, 12, 15, 12)
        headers_layout.setSpacing(15)
        
        macro_header = QLabel("Macro")
        macro_header.setObjectName("headerLabel")
        macro_header.setMinimumWidth(200)
        
        keybind_header = QLabel("Keybind")
        keybind_header.setObjectName("headerLabel")
        keybind_header.setMinimumWidth(100)
        
        action_header = QLabel("Action")
        action_header.setObjectName("headerLabel")
        action_header.setMinimumWidth(70)
        
        headers_layout.addWidget(macro_header, 3)
        headers_layout.addWidget(keybind_header, 1)
        headers_layout.addWidget(action_header, 1)
        
        macros_layout.addWidget(headers_frame)
        
        scroll_area = QScrollArea()
        scroll_area.setObjectName("scrollArea")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        scroll_content.setObjectName("scrollContent")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(2)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        
        self.macro_widgets = {}
        for macro_key, macro_data in self.macros.items():
            macro_widget = MacroWidget(macro_key, macro_data, self)
            self.macro_widgets[macro_key] = macro_widget
            scroll_layout.addWidget(macro_widget)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        macros_layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(macros_widget, "Macros")
        
    def setup_settings_tab(self):
        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        settings_layout.setSpacing(20)
        
        items_group = QGroupBox("Item Slot Configuration")
        items_group.setObjectName("settingsGroup")
        items_layout = QVBoxLayout(items_group)
        items_layout.setSpacing(10)
        
        description_label = QLabel("Configure which number keys correspond to your items:")
        description_label.setObjectName("descriptionLabel")
        description_label.setWordWrap(True)
        items_layout.addWidget(description_label)
        
        self.item_widgets = {}
        
        gg_sign_widget = ItemSettingWidget("GG Sign", "gg_sign", self)
        self.item_widgets["gg_sign"] = gg_sign_widget
        items_layout.addWidget(gg_sign_widget)
        
        prank_bomb_widget = ItemSettingWidget("Prank Bomb", "prank_bomb", self)
        self.item_widgets["prank_bomb"] = prank_bomb_widget
        items_layout.addWidget(prank_bomb_widget)
        
        items_layout.addStretch()
        settings_layout.addWidget(items_group)
        
        info_group = QGroupBox("Information")
        info_group.setObjectName("settingsGroup")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QLabel("• Quick Setup uses GG Sign and Prank Bomb\n"
                          "• Make sure your items are in the correct slots\n"
                          "• Changes are saved automatically\n"
                          "• Run as Administrator if hotkeys don't work\n"
                          "• Install required modules: pip install keyboard mouse pywin32")
        info_text.setObjectName("infoLabel")
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        settings_layout.addWidget(info_group)
        settings_layout.addStretch()
        
        self.tab_widget.addTab(settings_widget, "Settings")
        
    def setup_style(self):
        style = """
        QMainWindow {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        
        #headerFrame {
            background-color: #2a2a2a;
            border-radius: 10px;
            border: 1px solid #3a3a3a;
        }
        
        #titleLabel {
            font-size: 20px;
            font-weight: bold;
            color: #00d4ff;
        }
        
        #alwaysOnTopCb {
            color: #ffffff;
            font-size: 12px;
        }
        
        #alwaysOnTopCb::indicator {
            width: 16px;
            height: 16px;
        }
        
        #alwaysOnTopCb::indicator:unchecked {
            background-color: #4a4a4a;
            border: 2px solid #5a5a5a;
            border-radius: 4px;
        }
        
        #alwaysOnTopCb::indicator:checked {
            background-color: #00d4ff;
            border: 2px solid #00d4ff;
            border-radius: 4px;
        }
        
        #toggleButton {
            background-color: #ff4444;
            color: #ffffff;
            border: 1px solid #ff5555;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 11px;
            font-weight: bold;
            min-height: 30px;
        }
        
        #toggleButton:hover {
            background-color: #ff5555;
        }
        
        #toggleButton:pressed {
            background-color: #cc3333;
        }
        
        #tabWidget {
            background-color: #2a2a2a;
            border-radius: 10px;
            border: 1px solid #3a3a3a;
        }
        
        #tabWidget::pane {
            background-color: #2a2a2a;
            border: 1px solid #3a3a3a;
            border-radius: 8px;
        }
        
        #tabWidget::tab-bar {
            alignment: center;
        }
        
        QTabBar::tab {
            background-color: #3a3a3a;
            color: #cccccc;
            padding: 12px 30px;
            margin: 2px;
            border-radius: 6px;
            font-weight: bold;
            min-width: 80px;
        }
        
        QTabBar::tab:selected {
            background-color: #00d4ff;
            color: #000000;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #4a4a4a;
            color: #ffffff;
        }
        
        #headersFrame {
            background-color: #333333;
            border-radius: 6px;
            border: 1px solid #4a4a4a;
        }
        
        #scrollArea {
            background-color: transparent;
            border: none;
        }
        
        #scrollContent {
            background-color: transparent;
        }
        
        #macroWidget, #itemWidget {
            background-color: #333333;
            border-radius: 8px;
            border: 1px solid #4a4a4a;
            margin: 1px 0px;
        }
        
        #macroWidget:hover, #itemWidget:hover {
            background-color: #3a3a3a;
            border-color: #5a5a5a;
        }
        
        #headerLabel {
            font-size: 13px;
            font-weight: bold;
            color: #00d4ff;
        }
        
        #macroNameLabel, #itemNameLabel {
            font-size: 12px;
            color: #ffffff;
            font-weight: 500;
        }
        
        #keybindButton {
            background-color: #4a4a4a;
            color: #ffffff;
            border: 2px solid #5a5a5a;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: bold;
            min-height: 32px;
        }
        
        #keybindButton:hover {
            background-color: #5a5a5a;
            border-color: #6a6a6a;
        }
        
        #keybindButton:pressed {
            background-color: #3a3a3a;
            border-color: #4a4a4a;
        }
        
        #clearButton {
            background-color: #ff4444;
            color: #ffffff;
            border: 2px solid #ff5555;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
            font-weight: bold;
            min-height: 32px;
        }
        
        #clearButton:hover {
            background-color: #ff5555;
            border-color: #ff6666;
        }
        
        #clearButton:pressed {
            background-color: #cc3333;
            border-color: #dd4444;
        }
        
        #keyInput {
            background-color: #4a4a4a;
            color: #ffffff;
            border: 2px solid #5a5a5a;
            border-radius: 6px;
            padding: 8px;
            font-size: 12px;
            font-weight: bold;
        }
        
        #keyInput:focus {
            border-color: #00d4ff;
        }
        
        #settingsGroup {
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            border: 2px solid #4a4a4a;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        #settingsGroup::title {
            color: #00d4ff;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
        }
        
        #descriptionLabel, #infoLabel {
            color: #cccccc;
            font-size: 12px;
            font-weight: normal;
        }
        
        #statusFrame {
            background-color: #2a2a2a;
            border-radius: 10px;
            border: 1px solid #3a3a3a;
        }
        
        #statusLabel {
            font-size: 13px;
            font-weight: bold;
            color: #00ff00;
        }
        
        #focusLabel {
            font-size: 12px;
            color: #cccccc;
        }
        
        #creditsLabel {
            font-size: 10px;
            color: #888888;
            padding: 5px;
        }
        
        #creditsLabel:hover {
            color: #00d4ff;
        }
        
        QScrollBar:vertical {
            background-color: #2a2a2a;
            width: 12px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #4a4a4a;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #5a5a5a;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QDialog {
            background-color: #1a1a1a;
            color: #ffffff;
        }
        
        QPushButton {
            background-color: #4a4a4a;
            color: #ffffff;
            border: 2px solid #5a5a5a;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 12px;
            font-weight: bold;
            min-height: 30px;
        }
        
        QPushButton:hover {
            background-color: #5a5a5a;
            border-color: #6a6a6a;
        }
        
        QPushButton:pressed {
            background-color: #3a3a3a;
            border-color: #4a4a4a;
        }
        
        QPushButton:disabled {
            background-color: #2a2a2a;
            color: #666666;
            border-color: #3a3a3a;
        }
        """
        self.setStyleSheet(style)
        
    def apply_loaded_settings(self):
        self.always_on_top_cb.setChecked(self.settings["ui"]["always_on_top"])
        if self.settings["ui"]["always_on_top"]:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
        
        self.macros_enabled = self.settings["ui"]["macros_enabled"]
        self.update_toggle_button()
        
        for macro_key, keybind in self.settings["keybinds"].items():
            if macro_key in self.macros:
                self.macros[macro_key]["keybind"] = keybind
                if macro_key in self.macro_widgets:
                    self.macro_widgets[macro_key].update_display()
        
        self.item_keys.update(self.settings.get("item_keys", {}))
        for item_key, widget in self.item_widgets.items():
            widget.set_value(self.item_keys.get(item_key, ""))
        
    def update_toggle_button(self):
        if self.macros_enabled:
            self.toggle_macros_btn.setText("Disable Macros")
            self.toggle_macros_btn.setStyleSheet("""
                background-color: #ff4444;
                color: #ffffff;
                border: 1px solid #ff5555;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                min-height: 30px;
            """)
            self.status_label.setText("Macros Enabled")
            self.status_label.setStyleSheet("color: #00ff00;")
        else:
            self.toggle_macros_btn.setText("Enable Macros")
            self.toggle_macros_btn.setStyleSheet("""
                background-color: #00ff00;
                color: #000000;
                border: 1px solid #00dd00;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 11px;
                font-weight: bold;
                min-height: 30px;
            """)
            self.status_label.setText("Macros Disabled")
            self.status_label.setStyleSheet("color: #ff4444;")
        
    def toggle_macros(self):
        self.macros_enabled = not self.macros_enabled
        self.settings["ui"]["macros_enabled"] = self.macros_enabled
        self.update_toggle_button()
        
        if not self.macros_enabled:
            self.stop_gg_clip()
            
        self.save_settings()
    
    def toggle_always_on_top(self, checked):
        self.settings["ui"]["always_on_top"] = checked
        if checked:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()
        self.save_settings()
        
    def update_focus_status(self, text, color):
        self.focus_label.setText(text)
        self.focus_label.setStyleSheet(f"color: {color};")
        
    def is_roblox_focused(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().lower()
            return 'roblox' in process_name or 'robloxplayerbeta' in process_name
        except:
            return False
            
    def setup_hotkeys(self):
        self.gg_sign_running = False

        try:
            for listener in self.active_listeners:
                listener.stop()
            self.active_listeners.clear()

            for macro_key, macro_data in self.macros.items():
                keybind = macro_data.get("keybind")
                if not keybind:
                    continue

                if keybind.startswith("mouse_"):
                    mouse_button = keybind.replace("mouse_", "")
                    if macro_key == "gg_sign_clip":
                        self.setup_mouse_hold_macro(macro_key, mouse_button)
                    else:
                        self.setup_mouse_click_macro(macro_key, mouse_button)
                else:
                    if macro_key == "gg_sign_clip":
                        self.setup_keyboard_hold_macro(macro_key, keybind)
                    else:
                        self.setup_keyboard_click_macro(macro_key, keybind)
        except:
            pass

    def setup_mouse_hold_macro(self, macro_key, mouse_button):
        is_pressed = [False]

        def on_click(x, y, button, pressed):
            try:
                btn_map = {
                    "left": pynput_mouse.Button.left,
                    "right": pynput_mouse.Button.right,
                    "middle": pynput_mouse.Button.middle
                }
                if button == btn_map.get(mouse_button):
                    if pressed and self.is_roblox_focused() and self.macros_enabled:
                        if not is_pressed[0]:
                            is_pressed[0] = True
                            self.start_gg_clip()
                    elif not pressed and is_pressed[0]:
                        is_pressed[0] = False
                        self.stop_gg_clip()
            except:
                pass

        listener = pynput_mouse.Listener(on_click=on_click)
        listener.start()
        self.active_listeners.append(listener)

    def setup_mouse_click_macro(self, macro_key, mouse_button):
        def on_click(x, y, button, pressed):
            try:
                btn_map = {
                    "left": pynput_mouse.Button.left,
                    "right": pynput_mouse.Button.right,
                    "middle": pynput_mouse.Button.middle
                }
                if button == btn_map.get(mouse_button) and pressed:
                    if self.is_roblox_focused() and self.macros_enabled:
                        self.execute_macro(macro_key)
            except:
                pass

        listener = pynput_mouse.Listener(on_click=on_click)
        listener.start()
        self.active_listeners.append(listener)
    
    def setup_keyboard_hold_macro(self, macro_key, keybind):
        is_pressed = [False]

        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char == keybind:
                    if self.is_roblox_focused() and self.macros_enabled and not is_pressed[0]:
                        is_pressed[0] = True
                        self.start_gg_clip()
            except:
                pass

        def on_release(key):
            try:
                if hasattr(key, 'char') and key.char == keybind and is_pressed[0]:
                    is_pressed[0] = False
                    self.stop_gg_clip()
            except:
                pass

        listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        self.active_listeners.append(listener)
    
    def setup_keyboard_click_macro(self, macro_key, keybind):
        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char == keybind:
                    if self.is_roblox_focused() and self.macros_enabled:
                        self.execute_macro(macro_key)
            except:
                pass

        listener = pynput_keyboard.Listener(on_press=on_press)
        listener.start()
        self.active_listeners.append(listener)
        
    def start_gg_clip(self):
        if not self.gg_sign_running:
            self.gg_sign_running = True
            self.gg_sign_thread = threading.Thread(target=self.gg_clip_loop, daemon=True)
            self.gg_sign_thread.start()
            
    def stop_gg_clip(self):
        self.gg_sign_running = False
        
    def gg_clip_loop(self):
        while self.gg_sign_running:
            if not self.is_roblox_focused() or not self.macros_enabled:
                time.sleep(0.1)
                continue
            self.kb_controller.press('3')
            self.kb_controller.release('3')
            time.sleep(0.005)
            
    def execute_macro(self, macro_key):
        if not self.is_roblox_focused() or not self.macros_enabled:
            return
            
        macro_functions = {
            "quick_setup": self.quick_setup_macro,
            "bouncy_twirl": self.bouncy_twirl_macro,
            "flex_walk": self.flex_walk_macro,
            "bomb_jump": self.bomb_jump_macro,
            "bouncy_twirl_speed_glitch": self.bouncy_twirl_speed_glitch_macro,
            "flex_walk_speed_glitch": self.flex_walk_speed_glitch_macro
        }
        
        if macro_key in macro_functions:
            threading.Thread(target=macro_functions[macro_key], daemon=True).start()
    
    def quick_setup_macro(self):
        self.kb_controller.press('2')
        self.kb_controller.release('2')
        time.sleep(0.2)
        self.kb_controller.press(self.item_keys.get("gg_sign", "6"))
        self.kb_controller.release(self.item_keys.get("gg_sign", "6"))
        time.sleep(0.2)
        self.kb_controller.press('2')
        self.kb_controller.release('2')
        time.sleep(0.2)
        self.kb_controller.press(self.item_keys.get("prank_bomb", "7"))
        self.kb_controller.release(self.item_keys.get("prank_bomb", "7"))
        time.sleep(0.35)
        self.kb_controller.press('3')
        self.kb_controller.release('3')
        time.sleep(0.1)
        self.kb_controller.press('3')
        self.kb_controller.release('3')
        
    def bouncy_twirl_macro(self):
        self.kb_controller.press('.')
        self.kb_controller.release('.')
        time.sleep(0.035)
        self.kb_controller.press('1')
        self.kb_controller.release('1')
        time.sleep(1.0)
        self.kb_controller.press(pynput_keyboard.Key.shift)
        self.kb_controller.release(pynput_keyboard.Key.shift)
        time.sleep(0.05)
        self.kb_controller.press('w')
        self.kb_controller.press('3')
        self.kb_controller.release('3')
        time.sleep(0.015)
        self.kb_controller.release('w')
        time.sleep(0.075)
        self.kb_controller.press('3')
        self.kb_controller.release('3')
        
    def flex_walk_macro(self):
        self.kb_controller.press('.')
        self.kb_controller.release('.')
        time.sleep(0.035)
        self.kb_controller.press('3')
        self.kb_controller.release('3')
        time.sleep(1.75)
        self.kb_controller.press(pynput_keyboard.Key.shift)
        self.kb_controller.release(pynput_keyboard.Key.shift)
        time.sleep(0.05)
        self.kb_controller.press('w')
        self.kb_controller.press('3')
        self.kb_controller.release('3')
        time.sleep(0.015)
        self.kb_controller.release('w')
        time.sleep(0.075)
        self.kb_controller.press('3')
        self.kb_controller.release('3')

    def bomb_jump_macro(self):
        self.kb_controller.press(pynput_keyboard.Key.space)
        time.sleep(0.3)
        self.kb_controller.press('4')
        self.kb_controller.release('4')
        time.sleep(0.03)
        self.mouse_controller.click(pynput_mouse.Button.left)
        time.sleep(0.03)
        self.kb_controller.press('4')
        self.kb_controller.release('4')
        time.sleep(0.5)
        self.kb_controller.release(pynput_keyboard.Key.space)
        
    def bouncy_twirl_speed_glitch_macro(self):
        self.kb_controller.press('.')
        self.kb_controller.release('.')
        time.sleep(0.035)
        self.kb_controller.press('1')
        self.kb_controller.release('1')
        time.sleep(2.7)
        self.kb_controller.press('4')
        self.kb_controller.release('4')
        time.sleep(0.05)
        self.kb_controller.press('w')
        time.sleep(0.05)
        self.kb_controller.press('4')
        self.kb_controller.release('4')
        time.sleep(0.025)
        self.kb_controller.release('w')
        
    def flex_walk_speed_glitch_macro(self):
        self.kb_controller.press('.')
        self.kb_controller.release('.')
        time.sleep(0.035)
        self.kb_controller.press('3')
        self.kb_controller.release('3')
        time.sleep(1.75)
        self.kb_controller.press('4')
        self.kb_controller.release('4')
        time.sleep(0.05)
        self.kb_controller.press('w')
        time.sleep(0.05)
        self.kb_controller.press('4')
        self.kb_controller.release('4')
        time.sleep(0.025)
        self.kb_controller.release('w')

    def load_settings(self):
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    
                    if "window" in saved_settings:
                        self.settings["window"].update(saved_settings["window"])
                    if "ui" in saved_settings:
                        self.settings["ui"].update(saved_settings["ui"])
                    if "keybinds" in saved_settings:
                        self.settings["keybinds"] = saved_settings["keybinds"]
                    if "item_keys" in saved_settings:
                        self.settings["item_keys"].update(saved_settings["item_keys"])
        except:
            pass
            
    def save_settings(self):
        try:
            self.settings_dir.mkdir(parents=True, exist_ok=True)
            
            self.settings["keybinds"] = {key: data["keybind"] for key, data in self.macros.items() if data["keybind"] is not None}
            self.settings["item_keys"] = self.item_keys.copy()
            
            self.settings["window"]["width"] = self.width()
            self.settings["window"]["height"] = self.height()
            self.settings["window"]["x"] = self.x()
            self.settings["window"]["y"] = self.y()
            
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(500, self.save_settings)
        
    def moveEvent(self, event):
        super().moveEvent(event)
        QTimer.singleShot(500, self.save_settings)
            
    def closeEvent(self, event):
        try:
            self.save_settings()
            self.gg_sign_running = False

            if hasattr(self, 'status_thread') and self.status_thread:
                self.status_thread.stop()
                self.status_thread.wait(1000)

            for listener in self.active_listeners:
                listener.stop()
            self.active_listeners.clear()

            if hasattr(self, 'gg_sign_thread') and self.gg_sign_thread:
                if self.gg_sign_thread.is_alive():
                    self.gg_sign_thread.join(timeout=1.0)
        except:
            pass

        event.accept()
        QApplication.quit()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = MM2MacroGUI()
    window.show()
    
    try:
        if hasattr(app, 'exec'):
            result = app.exec()
        else:
            result = app.exec_()
        return result
    except:
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        pass
    except:
        sys.exit(1)