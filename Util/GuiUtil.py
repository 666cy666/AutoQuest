from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QSpinBox, QComboBox, QPushButton, QLabel, QDialog, QScrollArea, QSlider, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import json
import os
import sys

from Api.InitializeApi import initialize
from Api.RunApi import run
from Util.FileUtil import init_folder
from Util.stdout_util import StdoutRedirector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("问卷星自动填写程序")
        self.setMinimumSize(600, 400)
        init_folder()
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

    def load_config(self):
        config_path = os.path.join("Config", "setting.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            return {}
        
    def save_config(self):
        """保存配置到JSON文件"""
        try:
            # 获取当前界面的值
            new_config = self.config.copy()
            new_config["url"] = self.url_input.text()
            new_config["count"] = self.count_input.value()
            
            # 根据下拉框选择更新mode-type
            mode_index = self.mode_select.currentIndex()
            if mode_index == 0:
                new_config["mode"]["mode-type"] = "average-mode"
            else:
                new_config["mode"]["mode-type"] = "other-mode"
            
            # 写入JSON文件
            config_path = os.path.join("Config", "setting.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, ensure_ascii=False, indent=2)
            
            self.config = new_config
            print("配置已保存")
            
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def load_config(self):
        """加载配置文件并更新界面"""
        config_path = os.path.join("Config", "setting.json")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 更新界面值（如果界面元素已经创建）
            if hasattr(self, 'url_input'):
                self.url_input.setText(config.get("url", ""))
            if hasattr(self, 'count_input'):
                self.count_input.setValue(config.get("count", 200))
            if hasattr(self, 'mode_select'):
                mode_type = config["mode"].get("mode-type", "average-mode")
                self.mode_select.setCurrentIndex(0 if mode_type == "average-mode" else 1)
                
            return config
            
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
        self.output_text.setMinimumHeight(200)
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
            log_file=os.path.join("Log", "log.txt"),
            text_widget=self.output_text
        )
        sys.stdout = self.stdout_redirector

    def create_button_section(self, layout):
        # 第一排按钮布局
        first_row_layout = QHBoxLayout()
        init_btn = QPushButton("初始化程序")
        weight_btn = QPushButton("修改权重")
        
        first_row_layout.addWidget(init_btn)
        first_row_layout.addWidget(weight_btn)
        
        # 第二排按钮布局
        second_row_layout = QHBoxLayout()
        run_btn = QPushButton("运行程序")
        stop_btn = QPushButton("重启以中止程序")
        
        second_row_layout.addWidget(run_btn)
        second_row_layout.addWidget(stop_btn)
        
        # 连接按钮信号
        init_btn.clicked.connect(self.initialize_program)
        weight_btn.clicked.connect(self.change_weight)
        run_btn.clicked.connect(self.run_program)
        stop_btn.clicked.connect(self.stop_program)
        
        # 保存按钮引用
        self.run_btn = run_btn
        self.stop_btn = stop_btn
        self.init_btn = init_btn
        self.weight_btn = weight_btn
        
        # 添加两排按钮布局到主布局
        layout.addSpacing(20)
        layout.addLayout(first_row_layout)
        layout.addLayout(second_row_layout)
        layout.addStretch()

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

        def run(self):
            run(self.url, self.count)
            self.finished.emit()  # 发送完成信号

    def run_program(self):
        print("运行程序")
        print(self.config)
        self.run_thread = self.RunThread(self.url_input.text(), self.count_input.value())
        # 可以连接完成信号到相应的处理函数
        self.run_thread.finished.connect(self.on_run_finished)
        self.run_thread.start()

    def on_run_finished(self):
        print("程序运行完成")

    def change_weight(self):
        # TODO: 实现查看结果逻辑
        print("修改选项权重")
        dialog = WeightEditorDialog(self)
        dialog.exec()

    def stop_program(self):
        if hasattr(self, 'run_thread') and self.run_thread.isRunning():
            print("正在终止程序...")
            # 重启程序
            python = sys.executable
            os.execl(python, python, *sys.argv)

class WeightEditorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选项权重编辑器")
        self.setMinimumSize(800, 600)
        
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
        """)

    def load_data(self):
        try:
            with open(os.path.join("Config", "data-tL4FoDX.json"), 'r', encoding='utf-8') as f:
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
            self.topic_combo.addItem(f"题目 {i+1}: {topic['topic-title'][:30]}...")
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
            
            self.options_layout.addLayout(option_layout)

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
        for i, slider in enumerate(self.sliders):
            self.data[current_topic_index]['topic-answer-list'][i]['weight'] = slider.value()
            
        # 保存到文件
        try:
            with open(os.path.join("Config", "data-tL4FoDX.json"), 'w', encoding='utf-8') as f:
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