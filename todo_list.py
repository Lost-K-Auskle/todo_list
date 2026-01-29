import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QLineEdit, QPushButton, 
                             QCheckBox, QSystemTrayIcon, QMenu, QMessageBox, 
                             QListWidgetItem, QStyle, QDialog, QLabel, 
                             QFormLayout, QComboBox, QFileDialog, QSlider, QGroupBox,
                             QAbstractItemView, QSpinBox, QLCDNumber)
from PyQt6.QtCore import Qt, QSettings, QTimer, QUrl, QSize, QTime
from PyQt6.QtGui import QAction, QFont, QColor, QPalette, QBrush, QPixmap, QMovie

# --- 计时器小组件 ---
class TimerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 0
        self.is_running = False
        self.is_countdown = False
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        self.time_display = QLabel("00:00:00")
        self.time_display.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_display.setFixedWidth(100)
        
        self.min_input = QSpinBox()
        self.min_input.setRange(0, 180)
        self.min_input.setSuffix(" 分")
        self.min_input.setToolTip("设置倒计时分钟数，0为正向计时")
        self.min_input.valueChanged.connect(self.reset_timer_mode)
        
        self.btn_start = QPushButton("▶")
        self.btn_start.setFixedWidth(30)
        self.btn_start.clicked.connect(self.toggle_timer)
        
        self.btn_reset = QPushButton("↺")
        self.btn_reset.setFixedWidth(30)
        self.btn_reset.clicked.connect(self.reset_timer)
        
        layout.addStretch()
        layout.addWidget(QLabel("⏱️"))
        layout.addWidget(self.time_display)
        layout.addWidget(self.min_input)
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_reset)
        layout.addStretch()
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)

    def reset_timer_mode(self):
        self.stop()
        mins = self.min_input.value()
        if mins > 0:
            self.total_seconds = mins * 60
            self.is_countdown = True
        else:
            self.total_seconds = 0
            self.is_countdown = False
        self.update_display()

    def toggle_timer(self):
        if self.is_running:
            self.stop()
        else:
            self.start()

    def start(self):
        self.is_running = True
        self.btn_start.setText("⏸")
        self.min_input.setEnabled(False)
        self.timer.start(1000)

    def stop(self):
        self.is_running = False
        self.btn_start.setText("▶")
        self.min_input.setEnabled(True)
        self.timer.stop()

    def reset_timer(self):
        self.stop()
        self.reset_timer_mode()

    def update_timer(self):
        if self.is_countdown:
            if self.total_seconds > 0:
                self.total_seconds -= 1
            else:
                self.stop()
                self.time_up_signal()
        else:
            self.total_seconds += 1
        self.update_display()

    def update_display(self):
        hrs = self.total_seconds // 3600
        mins = (self.total_seconds % 3600) // 60
        secs = self.total_seconds % 60
        self.time_display.setText(f"{hrs:02}:{mins:02}:{secs:02}")

    def time_up_signal(self):
        parent = self.window()
        if isinstance(parent, QMainWindow):
            QMessageBox.information(parent, "计时结束", "专注时间结束！休息一下吧。")

# --- 预览窗口 (Lite版：无视频) ---
class PreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 350)
        self.current_settings = {"mode": 0, "opacity": 1.0, "bg_path": "", "style": 0, "confirm": True}
        self.is_processing = True 

        # GIF 层
        self.gif_label = QLabel(self)
        self.gif_label.setScaledContents(True)
        self.gif_label.resize(self.size())
        self.gif_label.hide()
        self.movie = None

        # UI层
        self.ui_container = QWidget(self)
        self.ui_container.setGeometry(0, 0, 220, 350)
        self.ui_container.setObjectName("preview_container")
        layout = QVBoxLayout(self.ui_container)
        
        top_spacer = QWidget()
        top_spacer.setFixedHeight(10)
        layout.addWidget(top_spacer)
        
        self.fake_list = QListWidget()
        self.fake_list.addItem("1. 学习 Python") 
        self.fake_list.addItem("2. 喝一杯咖啡")   
        self.fake_list.addItem("3. 健身运动")
        
        self.fake_list.itemChanged.connect(self.on_item_changed)
        self.fake_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.fake_list)
        
        input_layout = QHBoxLayout()
        self.input_fake = QLineEdit()
        self.input_fake.setPlaceholderText("预览输入...")
        self.input_fake.returnPressed.connect(self.add_task)
        btn_add = QPushButton("+")
        btn_add.clicked.connect(self.add_task)
        input_layout.addWidget(self.input_fake)
        input_layout.addWidget(btn_add)
        layout.addLayout(input_layout)
        
        self.fake_list.item(0).setCheckState(Qt.CheckState.Unchecked)
        self.fake_list.item(1).setCheckState(Qt.CheckState.Checked) 
        self.fake_list.item(2).setCheckState(Qt.CheckState.Unchecked)
        self.is_processing = False

    def add_task(self):
        text = self.input_fake.text().strip()
        if text:
            item = QListWidgetItem(text)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.fake_list.addItem(item)
            self.input_fake.clear()
            self.refresh_visuals() 

    def on_item_double_clicked(self, item):
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.Checked)
        else:
            item.setCheckState(Qt.CheckState.Unchecked)

    def on_item_changed(self, item):
        if self.is_processing: return
        self.is_processing = True

        if item.checkState() == Qt.CheckState.Checked:
            confirmed = True
            if self.current_settings["confirm"]:
                action = "移除" if self.current_settings["style"] == 0 else "完成"
                reply = QMessageBox.question(self, '预览确认', f"确定要{action}吗？", 
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                           QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No:
                    confirmed = False
            
            if confirmed:
                if self.current_settings["style"] == 0:
                    self.fake_list.takeItem(self.fake_list.row(item))
                else:
                    font = item.font()
                    font.setStrikeOut(True)
                    item.setFont(font)
                    item.setForeground(Qt.GlobalColor.gray)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
        else:
            font = item.font()
            font.setStrikeOut(False)
            item.setFont(font)
            is_dark = (self.current_settings["mode"] == 1)
            item.setForeground(Qt.GlobalColor.white if is_dark else Qt.GlobalColor.black)

        self.is_processing = False

    def update_preview(self, mode, opacity_val, bg_path, completion_style, confirm_bool):
        self.is_processing = True 
        self.current_settings = {"mode": mode, "opacity": opacity_val, "bg_path": bg_path, "style": completion_style, "confirm": confirm_bool}

        if self.movie: self.movie.stop()
        self.gif_label.hide()
        self.ui_container.setStyleSheet("") 

        alpha = int(255 * (opacity_val / 100))
        
        # 基础样式模拟
        if mode == 0: # Light
            self.setStyleSheet(f"background-color: rgba(240, 240, 240, {alpha});")
            self.fake_list.setStyleSheet(f"QListWidget {{ background-color: rgba(255, 255, 255, {alpha}); color: black; }}")
        elif mode == 1: # Dark
            self.setStyleSheet(f"background-color: rgba(43, 43, 43, {alpha});")
            self.fake_list.setStyleSheet(f"QListWidget {{ background-color: rgba(51, 51, 51, {alpha}); color: white; border: 1px solid #777; }}")
        elif mode == 2: # Custom
            self.setStyleSheet(f"background-color: rgba(240, 240, 240, {alpha});")
            self.fake_list.setStyleSheet(f"QListWidget {{ background-color: rgba(255, 255, 255, 120); color: black; }}")
            
            ext = os.path.splitext(bg_path)[1].lower()
            if ext == '.gif':
                self.movie = QMovie(bg_path)
                self.gif_label.setMovie(self.movie)
                self.movie.start()
                self.gif_label.show()
                self.gif_label.lower()
            elif ext in ['.jpg', '.png', '.jpeg']:
                path = bg_path.replace('\\', '/')
                self.ui_container.setStyleSheet(f"QWidget#preview_container {{ border-image: url(\"{path}\") 0 0 0 0 stretch stretch; }}")

        self.refresh_visuals()
        self.is_processing = False

    def refresh_visuals(self):
        is_dark = (self.current_settings["mode"] == 1)
        normal_color = Qt.GlobalColor.white if is_dark else Qt.GlobalColor.black
        
        for i in range(self.fake_list.count()):
            item = self.fake_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                if self.current_settings["style"] == 0:
                    self.fake_list.blockSignals(True) 
                    item.setCheckState(Qt.CheckState.Unchecked)
                    self.fake_list.blockSignals(False)
                    font = item.font()
                    font.setStrikeOut(False)
                    item.setFont(font)
                    item.setForeground(normal_color)
                else:
                    font = item.font()
                    font.setStrikeOut(True)
                    item.setFont(font)
                    item.setForeground(Qt.GlobalColor.gray)
            else:
                font = item.font()
                font.setStrikeOut(False)
                item.setFont(font)
                item.setForeground(normal_color)

# --- 设置对话框 ---
class SettingsDialog(QDialog):
    def __init__(self, parent=None, current_data=None):
        super().__init__(parent)
        self.setWindowTitle("设置 (实时预览)")
        self.resize(650, 450)
        self.data = current_data
        
        main_layout = QHBoxLayout()
        left_panel = QWidget()
        form_layout = QFormLayout(left_panel)
        
        self.confirm_delete_cb = QCheckBox("删除/完成需确认")
        self.confirm_delete_cb.setChecked(self.data["confirm_delete"])
        self.confirm_delete_cb.stateChanged.connect(self.trigger_preview)
        
        self.show_clock_cb = QCheckBox("显示当前时间 (顶部)")
        self.show_clock_cb.setChecked(self.data.get("show_clock", False))
        
        self.enable_timer_cb = QCheckBox("启用计时器/倒计时")
        self.enable_timer_cb.setChecked(self.data.get("enable_timer", False))

        self.style_combo = QComboBox()
        self.style_combo.addItems(["样式 1: 直接移除", "样式 2: 划线保留"])
        self.style_combo.setCurrentIndex(self.data["completion_style"])
        self.style_combo.currentIndexChanged.connect(self.trigger_preview)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["1. 明亮模式", "2. 暗黑模式", "3. 自定义背景"])
        self.theme_combo.setCurrentIndex(min(self.data["theme_mode"], 2))
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.data["opacity"] * 100))
        self.opacity_label = QLabel(f"{self.opacity_slider.value()}%")
        self.opacity_slider.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v}%"))
        self.opacity_slider.valueChanged.connect(self.trigger_preview)
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        
        self.file_container = QWidget()
        fp_layout = QHBoxLayout(self.file_container)
        fp_layout.setContentsMargins(0,0,0,0)
        self.path_edit = QLineEdit(self.data["bg_path"])
        btn_browse = QPushButton("...")
        btn_browse.clicked.connect(self.browse_file)
        fp_layout.addWidget(self.path_edit)
        fp_layout.addWidget(btn_browse)
        self.path_edit.textChanged.connect(self.trigger_preview)
        
        form_layout.addRow(QLabel("<b>逻辑设置:</b>"))
        form_layout.addRow("任务样式:", self.style_combo)
        form_layout.addRow(self.confirm_delete_cb)
        form_layout.addRow(QLabel("<b>功能扩展:</b>"))
        form_layout.addRow(self.show_clock_cb)
        form_layout.addRow(self.enable_timer_cb)
        form_layout.addRow(QLabel("<b>外观设置:</b>"))
        form_layout.addRow("主题风格:", self.theme_combo)
        form_layout.addRow("不透明度:", opacity_layout)
        form_layout.addRow("背景文件:", self.file_container)
        
        right_panel = QGroupBox("效果预览")
        right_layout = QVBoxLayout(right_panel)
        self.preview_widget = PreviewWidget()
        right_layout.addWidget(self.preview_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(left_panel, stretch=3)
        main_layout.addWidget(right_panel, stretch=2)
        
        final_layout = QVBoxLayout()
        final_layout.addLayout(main_layout)
        btn_box = QHBoxLayout()
        btn_save = QPushButton("保存生效")
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(btn_save)
        btn_box.addWidget(btn_cancel)
        final_layout.addLayout(btn_box)
        
        self.setLayout(final_layout)
        self.on_theme_changed(self.theme_combo.currentIndex())

    def on_theme_changed(self, index):
        self.file_container.setVisible(index == 2)
        self.trigger_preview()

    def browse_file(self):
        # 移除视频格式支持，只保留图片和GIF
        path, _ = QFileDialog.getOpenFileName(self, "选择背景", "", "Images (*.png *.jpg *.jpeg *.gif);;All (*)")
        if path: self.path_edit.setText(path)

    def trigger_preview(self):
        mode = self.theme_combo.currentIndex()
        opacity = self.opacity_slider.value()
        path = self.path_edit.text()
        style = self.style_combo.currentIndex()
        confirm = self.confirm_delete_cb.isChecked()
        self.preview_widget.update_preview(mode, opacity, path, style, confirm)

    def get_data(self):
        return {
            "theme_mode": self.theme_combo.currentIndex(),
            "bg_path": self.path_edit.text(),
            "confirm_delete": self.confirm_delete_cb.isChecked(),
            "completion_style": self.style_combo.currentIndex(),
            "opacity": self.opacity_slider.value() / 100.0,
            "show_clock": self.show_clock_cb.isChecked(),
            "enable_timer": self.enable_timer_cb.isChecked()
        }

# --- 主程序 (Lite版) ---
class TodoListApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.is_processing_check = False 
        self.is_undoing = False 
        self.undo_stack = []
        self.redo_stack = []
        self.current_snapshot = []

        self.settings = QSettings("MyPersonalTools", "SimpleTodoList_Lite")
        self.theme_mode = min(self.settings.value("theme_mode", 0, type=int), 2)
        self.bg_path = self.settings.value("bg_path", "", type=str)
        self.need_confirm_delete = self.settings.value("confirm_delete", True, type=bool)
        self.completion_style = self.settings.value("completion_style", 0, type=int) 
        self.window_opacity = self.settings.value("opacity", 0.95, type=float)
        self.show_clock = self.settings.value("show_clock", False, type=bool)
        self.enable_timer = self.settings.value("enable_timer", False, type=bool)

        self.movie = None

        self.setWindowTitle("我的 To-Do List")
        self.resize(400, 600)
        self.init_ui()
        self.init_tray()
        
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self.update_clock)
        self.clock_timer.start(1000)
        
        self.current_snapshot = self.get_state_snapshot()
        self.update_undo_redo_buttons()
        QTimer.singleShot(100, self.apply_theme)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setObjectName("central_widget")
        
        self.gif_bg_label = QLabel(self.central_widget)
        self.gif_bg_label.setScaledContents(True)
        self.gif_bg_label.hide()

        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        top_bar = QHBoxLayout()
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedWidth(30)
        settings_btn.clicked.connect(self.open_settings)
        self.btn_undo = QPushButton("↩️")
        self.btn_undo.setFixedWidth(30)
        self.btn_undo.clicked.connect(self.undo_action)
        self.btn_redo = QPushButton("↪️")
        self.btn_redo.setFixedWidth(30)
        self.btn_redo.clicked.connect(self.redo_action)
        
        self.clock_label = QLabel("--:--:--")
        self.clock_label.setStyleSheet("font-weight: bold; margin-right: 10px;")
        self.clock_label.hide()

        self.always_on_top_cb = QCheckBox("置顶")
        self.always_on_top_cb.stateChanged.connect(self.toggle_always_on_top)
        
        top_bar.addWidget(settings_btn)
        top_bar.addWidget(self.btn_undo)
        top_bar.addWidget(self.btn_redo)
        top_bar.addStretch() 
        top_bar.addWidget(self.clock_label)
        top_bar.addWidget(self.always_on_top_cb)
        self.main_layout.addLayout(top_bar)

        self.timer_widget = TimerWidget(self)
        self.timer_widget.hide()
        self.main_layout.addWidget(self.timer_widget)

        self.task_list = QListWidget()
        self.task_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.task_list.itemChanged.connect(self.on_item_check_state_changed)
        self.task_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.task_list.model().rowsMoved.connect(self.on_rows_moved)
        self.main_layout.addWidget(self.task_list)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入任务...")
        self.input_field.returnPressed.connect(self.add_task) 
        add_btn = QPushButton("+")
        add_btn.clicked.connect(self.add_task)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(add_btn)
        self.main_layout.addLayout(input_layout)

    def update_clock(self):
        if self.show_clock:
            self.clock_label.setText(QTime.currentTime().toString("HH:mm:ss"))

    def on_rows_moved(self, parent, start, end, destination, row):
        self.commit_action()
        self.update_snapshot_after_action()

    def get_state_snapshot(self):
        snapshot = []
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            snapshot.append({'text': item.text(), 'checked': item.checkState() == Qt.CheckState.Checked})
        return snapshot

    def commit_action(self):
        if self.is_undoing: return
        self.undo_stack.append(self.current_snapshot)
        self.redo_stack.clear()
        self.update_undo_redo_buttons()

    def update_snapshot_after_action(self):
        self.current_snapshot = self.get_state_snapshot()

    def restore_state(self, snapshot):
        self.is_undoing = True
        self.task_list.blockSignals(True)
        self.task_list.clear()
        for data in snapshot:
            item = QListWidgetItem(data['text'])
            item.setCheckState(Qt.CheckState.Checked if data['checked'] else Qt.CheckState.Unchecked)
            self.task_list.addItem(item)
            self.set_item_style(item, item.checkState() == Qt.CheckState.Checked)
        self.task_list.blockSignals(False)
        self.current_snapshot = snapshot
        self.is_undoing = False

    def undo_action(self):
        if not self.undo_stack: return
        self.redo_stack.append(self.current_snapshot)
        self.restore_state(self.undo_stack.pop())
        self.update_undo_redo_buttons()

    def redo_action(self):
        if not self.redo_stack: return
        self.undo_stack.append(self.current_snapshot)
        self.restore_state(self.redo_stack.pop())
        self.update_undo_redo_buttons()

    def update_undo_redo_buttons(self):
        self.btn_undo.setEnabled(len(self.undo_stack) > 0)
        self.btn_redo.setEnabled(len(self.redo_stack) > 0)

    def add_task(self):
        text = self.input_field.text().strip()
        if text:
            self.commit_action()
            item = QListWidgetItem(text)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.task_list.addItem(item)
            self.input_field.clear()
            self.update_snapshot_after_action()

    def on_item_double_clicked(self, item):
        if item.checkState() == Qt.CheckState.Unchecked:
            item.setCheckState(Qt.CheckState.Checked)
        else:
            item.setCheckState(Qt.CheckState.Unchecked)

    def on_item_check_state_changed(self, item):
        if self.is_processing_check or self.is_undoing: return
        self.is_processing_check = True
        is_checked = (item.checkState() == Qt.CheckState.Checked)
        if is_checked:
            confirmed = True
            if self.need_confirm_delete:
                action_text = "移除" if self.completion_style == 0 else "标记为完成"
                reply = QMessageBox.question(self, '确认', f"确定要{action_text}任务：\n'{item.text()}' 吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No: confirmed = False
            if confirmed:
                self.commit_action()
                if self.completion_style == 0:
                    self.safe_remove_item(item, record_history=False)
                elif self.completion_style == 1:
                    self.task_list.blockSignals(True)
                    item.setCheckState(Qt.CheckState.Checked) 
                    self.task_list.blockSignals(False)
                    self.set_item_style(item, True)
                self.update_snapshot_after_action()
            else:
                self.task_list.blockSignals(True)
                item.setCheckState(Qt.CheckState.Unchecked)
                self.task_list.blockSignals(False)
        else:
            self.commit_action()
            self.set_item_style(item, False)
            self.update_snapshot_after_action()
        self.is_processing_check = False

    def safe_remove_item(self, item, record_history=True):
        if record_history: self.commit_action()
        row = self.task_list.row(item)
        if row >= 0: self.task_list.takeItem(row)
        if record_history: self.update_snapshot_after_action()

    def set_item_style(self, item, is_done):
        font = item.font()
        font.setStrikeOut(is_done)
        item.setFont(font)
        color = Qt.GlobalColor.gray if is_done else (Qt.GlobalColor.white if self.theme_mode == 1 else Qt.GlobalColor.black)
        item.setForeground(color)

    def refresh_list_styles(self):
        for i in range(self.task_list.count()):
            item = self.task_list.item(i)
            self.set_item_style(item, item.checkState() == Qt.CheckState.Checked)

    def resizeEvent(self, event):
        if self.gif_bg_label:
            self.gif_bg_label.resize(self.size())
            self.gif_bg_label.lower()
        super().resizeEvent(event)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        tray_menu = QMenu()
        tray_menu.addAction(QAction("显示", self, triggered=self.show_window))
        tray_menu.addAction(QAction("退出", self, triggered=self.quit_app))
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def open_settings(self):
        current_data = {
            "theme_mode": self.theme_mode,
            "bg_path": self.bg_path,
            "confirm_delete": self.need_confirm_delete,
            "completion_style": self.completion_style,
            "opacity": self.window_opacity,
            "show_clock": self.show_clock,
            "enable_timer": self.enable_timer
        }
        dialog = SettingsDialog(self, current_data)
        if dialog.exec():
            data = dialog.get_data()
            self.theme_mode = data["theme_mode"]
            self.bg_path = data["bg_path"]
            self.need_confirm_delete = data["confirm_delete"]
            self.completion_style = data["completion_style"]
            self.window_opacity = data["opacity"]
            self.show_clock = data["show_clock"]
            self.enable_timer = data["enable_timer"]
            
            self.settings.setValue("theme_mode", self.theme_mode)
            self.settings.setValue("bg_path", self.bg_path)
            self.settings.setValue("confirm_delete", self.need_confirm_delete)
            self.settings.setValue("completion_style", self.completion_style)
            self.settings.setValue("opacity", self.window_opacity)
            self.settings.setValue("show_clock", self.show_clock)
            self.settings.setValue("enable_timer", self.enable_timer)
            
            self.apply_theme()
            self.refresh_list_styles()

    def apply_theme(self):
        self.setWindowOpacity(self.window_opacity)
        self.central_widget.setStyleSheet("")
        
        if self.movie: self.movie.stop()
        self.gif_bg_label.hide()

        self.clock_label.setVisible(self.show_clock)
        self.timer_widget.setVisible(self.enable_timer)

        list_style = "border: none; background-color: rgba(255,255,255,150); border-radius: 5px;"
        input_style = "border: 1px solid #ccc; background-color: rgba(255,255,255,180); border-radius: 3px;"
        
        dark_popup = """
            QMessageBox { background-color: #2b2b2b; color: white; }
            QMessageBox QLabel { color: white; }
            QMessageBox QPushButton { background-color: #444; color: white; border: 1px solid #555; padding: 5px; }
        """

        def get_checkbox_style(is_dark):
            border = "#999" if not is_dark else "#aaa"
            bg = "white" if not is_dark else "#444"
            tick = "black" if not is_dark else "white"
            return f"""
                QCheckBox {{ spacing: 5px; color: {tick}; }}
                QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {border}; background: {bg}; border-radius: 3px; }}
                QCheckBox::indicator:checked {{ background-color: #0078d7; border-color: #0078d7; image: url(none); }} 
            """

        if self.theme_mode == 0: 
            style = f"""
                QMainWindow {{ background-color: #f0f0f0; }}
                QListWidget {{ {list_style} background-color: rgba(255,255,255,200); }}
                QLineEdit {{ {input_style} }}
                QLabel {{ color: black; }}
                {get_checkbox_style(False)}
            """
            self.setStyleSheet(style)
            
        elif self.theme_mode == 1:
            style = f"""
                QMainWindow {{ background-color: #2b2b2b; }}
                QListWidget {{ background-color: rgba(50,50,50,200); color: white; border: 1px solid #555; }}
                QLineEdit {{ background-color: rgba(50,50,50,200); color: white; border: 1px solid #555; }}
                QLabel, QCheckBox {{ color: white; }} 
                QPushButton {{ color: white; }}
                {dark_popup}
                {get_checkbox_style(True)}
            """
            self.setStyleSheet(style)
            
        elif self.theme_mode == 2:
            style = f"""
                QMainWindow {{ background-color: #f0f0f0; }}
                QListWidget {{ {list_style} }}
                QLineEdit {{ {input_style} }}
                QLabel, QCheckBox {{ font-weight: bold; }}
                QCheckBox {{ background: rgba(255,255,255,0.4); border-radius: 3px; padding: 2px; }}
                {get_checkbox_style(False)}
            """
            self.setStyleSheet(style)
            
            ext = os.path.splitext(self.bg_path)[1].lower()
            if ext == '.gif':
                self.movie = QMovie(self.bg_path)
                self.gif_bg_label.setMovie(self.movie)
                self.movie.start()
                self.gif_bg_label.resize(self.size())
                self.gif_bg_label.show()
                self.gif_bg_label.lower()
            elif ext in ['.jpg', '.png', '.jpeg']:
                path = self.bg_path.replace('\\', '/')
                self.central_widget.setStyleSheet(self.central_widget.styleSheet() + f"QWidget#central_widget {{ border-image: url(\"{path}\") 0 0 0 0 stretch stretch; }}")

    def toggle_always_on_top(self, state):
        if state == 2: self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        else: self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def closeEvent(self, event):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("关闭")
        msg_box.setText("选择关闭方式")
        msg_box.setIcon(QMessageBox.Icon.Question)
        btn_min = msg_box.addButton("最小化", QMessageBox.ButtonRole.ActionRole)
        btn_quit = msg_box.addButton("退出", QMessageBox.ButtonRole.DestructiveRole)
        msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.exec()
        if msg_box.clickedButton() == btn_min:
            self.hide()
            self.tray_icon.showMessage("提示", "已最小化", QSystemTrayIcon.MessageIcon.Information, 1000)
            event.ignore()
        elif msg_box.clickedButton() == btn_quit:
            self.tray_icon.hide()
            event.accept()
        else:
            event.ignore()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: self.show_window()
    def show_window(self): self.showNormal(); self.activateWindow()
    def quit_app(self): self.tray_icon.hide(); QApplication.quit()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TodoListApp()
    window.show()
    sys.exit(app.exec())