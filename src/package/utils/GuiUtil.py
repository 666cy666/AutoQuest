from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QSpinBox, QComboBox, QPushButton, QLabel, QDialog, QScrollArea, QSlider, QMessageBox, QTextEdit, QCheckBox, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices, QPixmap
from src.package.api.InitializeApi import initialize
from src.package.api.RunApi import run
from src.package.utils.StdoutUtil import StdoutRedirector
from src.package.config.paths import setting_path, OUTPUT_DIR, icon_png_path, WEIGHT_DIR, log_path, icon_path, payment_qr_path

import json
import os
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口图标
        self.setWindowIcon(QIcon(str(icon_path)))

        self.setWindowTitle("问卷星自动填写程序")
        self.setMinimumSize(700, 700)
        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 创建主布局
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # 加载配置文件
        self.config = self.load_config()

        # 创建输入区域
        self.create_input_section(layout)

        # 创建输出显示区域
        self.create_output_section(layout)

        # 创建按钮区域
        self.create_button_section(layout)

        # 设置样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 14px;
                margin-bottom: 5px;
            }
            QLineEdit, QSpinBox, QComboBox {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-height: 30px;
            }
            QPushButton {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)

        # 绑定失焦事件
        self.url_input.editingFinished.connect(self.save_config)
        self.count_input.editingFinished.connect(self.save_config)
        self.mode_select.currentIndexChanged.connect(self.save_config)
        self.browser_select.currentIndexChanged.connect(self.save_config)
        self.browser_path_input.editingFinished.connect(self.save_config)
        self.headless_checkbox.stateChanged.connect(self.save_config)

        self.run_thread = None

    def save_config(self):
        """保存配置到JSON文件"""
        try:
            # 获取当前界面的值
            new_config = self.config.copy()
            new_config["url"] = self.url_input.text()
            new_config["count"] = self.count_input.value()

            # 更新浏览器配置
            new_config["browser"]["driver_type"] = [self.browser_select.currentText()]
            new_config["browser"]["driver_path"] = self.browser_path_input.text()
            new_config["browser"]["headless"] = self.headless_checkbox.isChecked()

            # 根据下拉框选择更新mode-type
            mode_index = self.mode_select.currentIndex()
            if mode_index == 0:
                new_config["mode"]["mode-type"] = "average-mode"
            else:
                new_config["mode"]["mode-type"] = "other-mode"

            # 写入JSON文件
            with open(setting_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)

            self.config = new_config
            print("配置已保存，浏览器启动配置需重启可生效")

        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def load_config(self):
        """加载配置文件并更新界面"""
        try:
            with open(setting_path, 'r', encoding='utf-8') as f:
                setting = json.load(f)

            # 更新界面值（如果界面元素已经创建）
            if hasattr(self, 'url_input'):
                self.url_input.setText(setting.get("url", ""))
            if hasattr(self, 'count_input'):
                self.count_input.setValue(setting.get("count", 200))
            if hasattr(self, 'mode_select'):
                mode_type = setting["mode"].get("mode-type", "average-mode")
                self.mode_select.setCurrentIndex(0 if mode_type == "average-mode" else 1)
            if hasattr(self, 'browser_select'):
                self.browser_select.setCurrentText(setting["browser"]["driver_type"][0])
            if hasattr(self, 'browser_path_input'):
                self.browser_path_input.setText(setting["browser"]["driver_path"])
            if hasattr(self, 'headless_checkbox'):
                self.headless_checkbox.setChecked(setting["browser"]["headless"])

            return setting

        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}

    def create_input_section(self, layout):
        # URL输入
        url_layout = QHBoxLayout()
        url_label = QLabel("问卷URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入问卷星URL")
        if self.config.get("url"):
            self.url_input.setText(self.config["url"])
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # 运行次数输入
        count_layout = QHBoxLayout()
        count_label = QLabel("运行次数:")
        self.count_input = QSpinBox()
        self.count_input.setRange(1, 1000)
        self.count_input.setValue(self.config.get("count", 200))
        count_layout.addWidget(count_label)
        count_layout.addWidget(self.count_input)
        layout.addLayout(count_layout)

        # 浏览器选择
        browser_layout = QHBoxLayout()
        browser_label = QLabel("浏览器类型:")
        self.browser_select = QComboBox()
        self.browser_select.addItems(['chrome', 'edge'])
        current_browser = self.config["browser"]["driver_type"][0]
        self.browser_select.setCurrentText(current_browser)
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_select)
        layout.addLayout(browser_layout)

        # 浏览器路径
        browser_path_layout = QHBoxLayout()
        browser_path_label = QLabel("浏览器路径:可为空，默认使用系统默认浏览器")
        self.browser_path_input = QLineEdit()
        self.browser_path_input.setText(self.config["browser"]["driver_path"])
        self.browser_path_input.setPlaceholderText("请输入浏览器路径")
        browser_path_layout.addWidget(browser_path_label)
        browser_path_layout.addWidget(self.browser_path_input)
        layout.addLayout(browser_path_layout)

        # 无头模式选择
        headless_layout = QHBoxLayout()
        headless_label = QLabel("无头模式：浏览器隐藏可视化至后台运行")
        self.headless_checkbox = QCheckBox()
        self.headless_checkbox.setChecked(self.config["browser"]["headless"])
        headless_layout.addWidget(headless_label)
        headless_layout.addWidget(self.headless_checkbox)
        layout.addLayout(headless_layout)

        # 模式选择
        mode_layout = QHBoxLayout()
        mode_label = QLabel("运行模式:")
        self.mode_select = QComboBox()
        self.mode_select.addItem(self.config["mode"]["average-mode"])
        self.mode_select.addItem(self.config["mode"]["other-mode"])
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_select)
        layout.addLayout(mode_layout)

    def create_output_section(self, layout):
        """创建输出显示区域"""
        # 创建输出标签
        output_label = QLabel("程序输出:")
        layout.addWidget(output_label)

        # 创建文本显示区域
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(125)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 8px;
                font-family: Consolas, Monaco, monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.output_text)

        # 设置输出重定向
        self.stdout_redirector = StdoutRedirector(
            log_file=log_path,
            text_widget=self.output_text
        )
        sys.stdout = self.stdout_redirector

    def create_button_section(self, layout):
        # 创建按钮容器
        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_container.setLayout(button_layout)

        # 第一排按钮布局
        first_row_layout = QHBoxLayout()
        init_btn = QPushButton("初始化程序")
        weight_btn = QPushButton("修改权重")

        first_row_layout.addWidget(init_btn)
        first_row_layout.addWidget(weight_btn)
        button_layout.addLayout(first_row_layout)

        # 第二排按钮布局
        second_row_layout = QHBoxLayout()
        run_btn = QPushButton("运行程序")
        stop_btn = QPushButton("填写当前问卷后停止程序")

        second_row_layout.addWidget(run_btn)
        second_row_layout.addWidget(stop_btn)
        button_layout.addLayout(second_row_layout)

        # 第三排按钮布局
        third_row_layout = QHBoxLayout()
        about_btn = QPushButton("关于及版权信息")
        third_row_layout.addWidget(about_btn)
        button_layout.addLayout(third_row_layout)

        # 连接按钮信号
        init_btn.clicked.connect(self.initialize_program)
        weight_btn.clicked.connect(self.change_weight)
        run_btn.clicked.connect(self.run_program)
        stop_btn.clicked.connect(self.stop_program)
        about_btn.clicked.connect(self.about)

        # 保存按钮引用
        self.run_btn = run_btn
        self.stop_btn = stop_btn
        self.init_btn = init_btn
        self.weight_btn = weight_btn
        self.about_btn = about_btn

        # 添加按钮容器到主布局
        layout.addWidget(button_container)

    def initialize_program(self):
        # TODO: 实现初始化逻辑
        print("初始化程序")
        initialize(self.url_input.text())

    class RunThread(QThread):
        finished = pyqtSignal()  # 添加完成信号
        
        def __init__(self, url, count):
            super().__init__()
            self.url = url
            self.count = count
            # 添加运行状态标志
            self.is_running = True

        def run(self):
            for count_index in range(self.count):
                if self.is_running:
                    run(self.url, count_index=count_index)
                else:
                    print(f"第{count_index}次运行终止运行")
                    break
            self.on_run_finished()

        def stop_program(self):
            print("正在终止程序...")
            self.is_running = False  # 设置停止标志

        def on_run_finished(self):
            print("程序运行完成")

    def run_program(self):
        print("运行程序")
        print(self.config)
        self.run_thread = self.RunThread(self.url_input.text(), self.count_input.value())
        # 可以连接完成信号到相应的处理函数
        self.run_thread.start()

    def stop_program(self):
        print("正在终止程序...")
        self.run_thread.is_running = False  # 设置停止标志

    def change_weight(self):
        print("修改选项权重")
        dialog = WeightEditorDialog(self, url_text=self.url_input.text())
        dialog.exec()

    def about(self):
        dialog = AboutDialog(self)
        dialog.exec()


class FillBlankOptionDialog(QDialog):
    """填空题选项编辑对话框"""
    def __init__(self, parent=None, text="", weight=100):
        super().__init__(parent)
        self.setWindowTitle("编辑填空题选项")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # 文本输入
        text_layout = QHBoxLayout()
        text_label = QLabel("选项文本:")
        self.text_input = QLineEdit(text)
        text_layout.addWidget(text_label)
        text_layout.addWidget(self.text_input)
        layout.addLayout(text_layout)
        
        # 权重输入
        weight_layout = QHBoxLayout()
        weight_label = QLabel("权重(%):")
        self.weight_input = QSpinBox()
        self.weight_input.setRange(0, 100)
        self.weight_input.setValue(weight)
        weight_layout.addWidget(weight_label)
        weight_layout.addWidget(self.weight_input)
        layout.addLayout(weight_layout)
        
        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 13px;
                margin: 5px;
            }
            QLineEdit, QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-height: 30px;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
    
    def get_values(self):
        """获取输入的值"""
        return self.text_input.text(), self.weight_input.value()

class FillBlankOptionListDialog(QDialog):
    """填空题选项列表编辑对话框"""
    def __init__(self, parent=None, options=None):
        super().__init__(parent)
        self.setWindowTitle("编辑填空选项列表")
        self.setMinimumSize(500, 400)
        
        if options is None:
            options = []
        
        self.options = options.copy()
        
        layout = QVBoxLayout(self)
        
        # 选项列表
        self.options_list = QListWidget()
        self.load_options()
        layout.addWidget(self.options_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加选项")
        add_btn.clicked.connect(self.add_option)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("编辑选项")
        edit_btn.clicked.connect(self.edit_option)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("删除选项")
        delete_btn.clicked.connect(self.delete_option)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        # 确定取消按钮
        dialog_buttons = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        dialog_buttons.addWidget(ok_button)
        dialog_buttons.addWidget(cancel_button)
        layout.addLayout(dialog_buttons)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e0f7fa;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
    
    def load_options(self):
        """加载选项到列表"""
        self.options_list.clear()
        for option in self.options:
            item = QListWidgetItem(f"{option['text']} (权重: {option['weight']}%)")
            self.options_list.addItem(item)
    
    def add_option(self):
        """添加选项"""
        dialog = FillBlankOptionDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            text, weight = dialog.get_values()
            new_option = {
                "text": text,
                "weight": weight
            }
            self.options.append(new_option)
            self.load_options()
    
    def edit_option(self):
        """编辑选项"""
        current_row = self.options_list.currentRow()
        if current_row >= 0:
            option = self.options[current_row]
            dialog = FillBlankOptionDialog(self, text=option['text'], weight=option['weight'])
            if dialog.exec() == QDialog.DialogCode.Accepted:
                text, weight = dialog.get_values()
                option['text'] = text
                option['weight'] = weight
                self.load_options()
    
    def delete_option(self):
        """删除选项"""
        current_row = self.options_list.currentRow()
        if current_row >= 0:
            self.options.pop(current_row)
            self.load_options()
    
    def get_values(self):
        """获取选项列表"""
        return self.options


class WeightEditorDialog(QDialog):
    def __init__(self, parent=None, url_text=None):
        super().__init__(parent)
        self.setWindowTitle("选项权重编辑器")
        self.setMinimumSize(800, 600)
        self.url_text = url_text
        # 加载数据
        self.load_data()
        self.current_index = 0  # 添加当前题目索引

        # 创建界面
        self.init_ui()

        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 13px;
                margin: 5px;
            }
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                min-height: 30px;
                min-width: 400px;
            }
            QSlider {
                min-width: 200px;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #ddd;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: none;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QPushButton {
                padding: 8px 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:selected {
                background-color: #e0f7fa;
            }
        """)

    def load_data(self):
        name = self.url_text.split('/')[-1].split('.')[0]
        try:
            with open(os.path.join(WEIGHT_DIR, f"data-{name}.json"), 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"加载数据失败: {e}")
            self.data = []

    def init_ui(self):
        layout = QVBoxLayout(self)

        # 题目导航区域
        nav_layout = QHBoxLayout()

        # 上一题按钮
        self.prev_btn = QPushButton("上一题")
        self.prev_btn.clicked.connect(self.prev_topic)
        nav_layout.addWidget(self.prev_btn)

        # 题目选择下拉框
        topic_label = QLabel("选择题目:")
        self.topic_combo = QComboBox()
        for i, topic in enumerate(self.data):
            self.topic_combo.addItem(f"题目 {i + 1}: {topic['topic-title'][:30]}...")
        nav_layout.addWidget(topic_label)
        nav_layout.addWidget(self.topic_combo)

        # 下一题按钮
        self.next_btn = QPushButton("下一题")
        self.next_btn.clicked.connect(self.next_topic)
        nav_layout.addWidget(self.next_btn)

        layout.addLayout(nav_layout)

        # 选项和权重显示区域
        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout(self.options_widget)

        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidget(self.options_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # 保存按钮
        save_btn = QPushButton("保存修改")
        save_btn.clicked.connect(self.save_changes)
        layout.addWidget(save_btn)

        # 连接题目选择信号
        self.topic_combo.currentIndexChanged.connect(self.on_topic_changed)

        # 初始显示第一题的选项
        self.update_options(0)
        self.update_nav_buttons()

    def clear_options_layout(self):
        """安全清除选项布局"""
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def clear_layout(self, layout):
        """递归清除布局"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def update_options(self, index):
        # 安全清除现有选项
        self.clear_options_layout()

        if index < 0 or index >= len(self.data):
            return

        topic = self.data[index]

        # 添加题目类型标签
        type_label = QLabel(f"题目类型: {self.get_topic_type(topic['topic-type'])}")
        self.options_layout.addWidget(type_label)

        # 添加题目标签
        title_label = QLabel(f"题目: {topic['topic-title']}")
        title_label.setWordWrap(True)  # 允许标签文字换行
        self.options_layout.addWidget(title_label)

        # 根据题目类型显示不同的界面
        if topic['topic-type'] == "1":  # 填空题
            self.show_fill_blank_interface(topic)
        else:  # 单选题或多选题
            self.show_choice_interface(topic)

    def show_fill_blank_interface(self, topic):
        """显示填空题界面"""
        # 添加填空题选项列表
        self.fill_blank_list = QListWidget()
        self.options_layout.addWidget(QLabel("填空题选项:"))
        self.options_layout.addWidget(self.fill_blank_list)

        # 添加选项按钮
        add_btn = QPushButton("添加选项")
        add_btn.clicked.connect(lambda checked, t=topic: self.add_fill_blank_option(t))
        self.options_layout.addWidget(add_btn)

        # 删除选项按钮
        delete_btn = QPushButton("删除选中选项")
        delete_btn.clicked.connect(lambda checked, t=topic: self.delete_fill_blank_option(t))
        self.options_layout.addWidget(delete_btn)

        # 编辑选项按钮
        edit_btn = QPushButton("编辑选中选项")
        edit_btn.clicked.connect(lambda checked, t=topic: self.edit_fill_blank_option(t))
        self.options_layout.addWidget(edit_btn)

        # 加载现有选项
        self.load_fill_blank_options(topic)

    def load_fill_blank_options(self, topic):
        """加载填空题选项到列表"""
        self.fill_blank_list.clear()
        for option in topic['topic-answer-list']:
            item = QListWidgetItem(f"{option['text']} (权重: {option['weight']}%)")
            self.fill_blank_list.addItem(item)

    def add_fill_blank_option(self, topic):
        """添加填空题选项"""
        dialog = FillBlankOptionDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            text, weight = dialog.get_values()
            new_option = {
                "text": text,
                "weight": weight
            }
            topic['topic-answer-list'].append(new_option)
            self.load_fill_blank_options(topic)
            # 保存更改
            self.save_changes()

    def delete_fill_blank_option(self, topic):
        """删除填空题选项"""
        current_row = self.fill_blank_list.currentRow()
        if current_row >= 0:
            topic['topic-answer-list'].pop(current_row)
            self.load_fill_blank_options(topic)
            # 保存更改
            self.save_changes()

    def edit_fill_blank_option(self, topic):
        """编辑填空题选项"""
        current_row = self.fill_blank_list.currentRow()
        if current_row >= 0:
            option = topic['topic-answer-list'][current_row]
            dialog = FillBlankOptionDialog(text=option['text'], weight=option['weight'], parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                text, weight = dialog.get_values()
                option['text'] = text
                option['weight'] = weight
                self.load_fill_blank_options(topic)
                # 保存更改
                self.save_changes()

    def show_choice_interface(self, topic):
        """显示单选题或多选题界面"""
        # 为每个选项创建滑动条
        self.sliders = []
        for option in topic['topic-answer-list']:
            option_layout = QHBoxLayout()

            # 选项文本
            option_label = QLabel(option['text'])
            option_label.setMinimumWidth(300)
            option_layout.addWidget(option_label)

            # 权重滑动条
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(100)
            slider.setValue(option['weight'])
            self.sliders.append(slider)

            # 权重数值显示
            weight_label = QLabel(f"{option['weight']}%")
            slider.valueChanged.connect(lambda v, label=weight_label: label.setText(f"{v}%"))

            option_layout.addWidget(slider)
            option_layout.addWidget(weight_label)

            # 如果选项需要填空，添加编辑按钮
            if option.get('input', False):
                edit_input_btn = QPushButton("编辑填空选项")
                edit_input_btn.clicked.connect(lambda checked, o=option: self.edit_input_option(o))
                option_layout.addWidget(edit_input_btn)

            self.options_layout.addLayout(option_layout)

    def edit_input_option(self, option):
        """编辑需要填空的选项"""
        if 'input-text' not in option:
            option['input-text'] = []

        dialog = FillBlankOptionListDialog(options=option['input-text'], parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            option['input-text'] = dialog.get_values()
            # 保存更改
            self.save_changes()

    def prev_topic(self):
        """切换到上一题"""
        if self.current_index > 0:
            self.current_index -= 1
            self.topic_combo.setCurrentIndex(self.current_index)

    def next_topic(self):
        """切换到下一题"""
        if self.current_index < len(self.data) - 1:
            self.current_index += 1
            self.topic_combo.setCurrentIndex(self.current_index)

    def on_topic_changed(self, index):
        """处理题目切换"""
        self.current_index = index
        self.update_options(index)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        """更新导航按钮状态"""
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.data) - 1)

    def get_topic_type(self, type_id):
        type_map = {
            "1": "判断题",
            "2": "填空题",
            "3": "单选题",
            "4": "多选题"
        }
        return type_map.get(type_id, "未知类型")

    def save_changes(self):
        current_topic_index = self.topic_combo.currentIndex()
        if current_topic_index < 0:
            return

        # 更新当前题目的权重值
        topic = self.data[current_topic_index]
        if topic['topic-type'] != "1":  # 不是填空题才需要更新滑动条
            for i, slider in enumerate(self.sliders):
                self.data[current_topic_index]['topic-answer-list'][i]['weight'] = slider.value()

        # 保存到文件
        try:
            name = self.url_text.split('/')[-1].split('.')[0]
            with open(os.path.join(WEIGHT_DIR, f"data-{name}.json"), 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)

            # 显示保存成功提示框
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("保存成功")
            msg_box.setText("权重修改已成功保存！")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f0f0f0;
                }
                QPushButton {
                    padding: 5px 15px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            msg_box.exec()

        except Exception as e:
            # 显示保存失败提示框
            error_box = QMessageBox(self)
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle("保存失败")
            error_box.setText(f"保存失败: {str(e)}")
            error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_box.setStyleSheet("""
                QMessageBox {
                    background-color: #f0f0f0;
                }
                QPushButton {
                    padding: 5px 15px;
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            error_box.exec()

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            self.setup_ui()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"对话框初始化失败: {str(e)}")
            self.reject()

    def setup_ui(self):
        self.setWindowTitle("关于及版权信息")
        self.setFixedSize(600, 500)  # 更紧凑的窗口尺寸

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(12)

        # 顶部标题区域
        header_layout = QHBoxLayout()

        # Logo显示
        logo_label = QLabel()
        if icon_png_path.exists():
            logo_pixmap = QPixmap(str(icon_png_path)).scaled(
                60, 60, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setText("[LOGO]")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(logo_label)

        # 标题文本
        title_text = """
        <div style="margin-left: 10px;">
        <h2 style="margin: 0;">问卷星自动填写程序</h2>
        <p style="color: #666; margin: 2px 0 0 0;">版本 1.3.0 | © 2025</p>
        </div>
        """
        title_label = QLabel(title_text)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        header_layout.addWidget(title_label)

        header_layout.addStretch()  # 右侧填充空白
        main_layout.addLayout(header_layout)

        # 分隔线（CSS样式）
        separator = QLabel("<hr style='margin: 5px 0; border: 0; height: 1px; background: #ddd;'>")
        main_layout.addWidget(separator)

        # 主要内容区域（文字+二维码）
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # 左侧信息区域
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)

        info_text = """
        <div style="line-height: 1.6; font-size: 13px;">
        <h3 style="margin: 0 0 8px 0; color: #333;">开发者信息</h3>
        <p>▪ <b>Powered By</b>: <a href='https://github.com/666cy666' 
                             style='color: #06c; text-decoration: none;'>CY</a></p>
        <p>▪ <b>GitHub</b>: <a href='https://github.com/666cy666/AutoQuest' 
                             style='color: #06c; text-decoration: none;'>项目源码仓库</a></p>
        <p>▪ <b>联系方式</b>: 19877365586@163.com </p>
        <h3 style="margin: 40px 0 8px 0; color: #333;">技术支持</h3>
        <p>▸ 本软件免费开源，欢迎Star支持</p>
        <p>▪ <b>使用问题请提交GitHub Issue</b>: <a href='https://github.com/666cy666/AutoQuest/issues' 
                             style='color: #06c; text-decoration: none;'>Issue提交</a></p>
        <p>▸ 本软件为<a href='https://github.com/666cy666/AutoQuest/blob/main/LICENSE' 
                             style='color: #06c; text-decoration: none;'>GPL开源协议</a>，请勿以任何形式贩卖此项目</p>
        <p>▸ 若进行商业合作请联系开发者</p>
        </div>
        """
        info_label = QLabel(info_text)
        info_label.setOpenExternalLinks(True)
        info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        info_layout.addWidget(info_label)

        # 添加弹性空间使内容顶部对齐
        info_layout.addStretch()
        content_layout.addWidget(info_widget, stretch=2)

        # 右侧二维码区域
        qr_widget = QWidget()
        qr_layout = QVBoxLayout(qr_widget)
        qr_layout.setSpacing(8)
        qr_layout.setContentsMargins(0, 0, 0, 0)

        # 二维码图片
        qr_code_label = QLabel()
        qr_code_label.setStyleSheet("""
            border: 1px solid #eee;
            border-radius: 4px;
            padding: 8px;
            background: white;
        """)
        if payment_qr_path.exists():
            qr_pixmap = QPixmap(str(payment_qr_path)).scaled(
                250, 250,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            qr_code_label.setPixmap(qr_pixmap)
        else:
            qr_code_label.setText("<div style='color: #999;'>[二维码未加载]</div>")
        qr_code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 二维码说明文字
        qr_text = QLabel("""
        <div style="color: #666; font-size: 12px;">
        <p style="margin: 0; text-align: center;">扫码投喂，助力野生开发者进化！</p>
        <p style="margin: 3px 0 0 0; text-align: center;">您的打赏会让我更新速度+100%✨</p>
        </div>
        """)

        qr_layout.addWidget(qr_code_label)
        qr_layout.addWidget(qr_text)
        qr_layout.addStretch()
        content_layout.addWidget(qr_widget, stretch=1)

        main_layout.addLayout(content_layout)

        # 底部按钮区域
        button_style = """
        QPushButton {
            padding: 10px 20px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 14px;
            min-width: 120px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        """

        # GitHub按钮（添加图标更专业）
        github_btn = QPushButton("下载最新打包版本 From GitHub")
        github_btn.setStyleSheet(button_style + """
        QPushButton {
            background-color: #24292e;  /* GitHub黑色 */
        }
        QPushButton:hover {
            background-color: #2c3136;
        }
        """)
        # github_btn.setIcon(QIcon(":/icons/github.png"))
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/666cy666/AutoQuest/releases")))
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(button_style + """
        QPushButton {
            background-color: #f44336;  /* 红色表示关闭操作 */
        }
        QPushButton:hover {
            background-color: #d32f2f;
        }
        """)

        # 按钮布局（增加间距）
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(github_btn)
        btn_layout.addSpacing(10)  # 按钮间距
        btn_layout.addWidget(close_btn)

        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
