import os
import shutil
import sys

import builtins

from PyQt6.QtWidgets import QTextEdit, QApplication
from PyQt6.QtCore import QObject, pyqtSignal

log_path = './Log/log.txt'

# 保存原始的 print 函数
original_print = builtins.print

# 自定义 print 函数，默认使用 end=''
def print(*args, **kwargs):
    original_print(*args, end='', **kwargs)

class StdoutRedirector(QObject):
    output_written = pyqtSignal(str)  # 定义信号

    def __init__(self, log_file, text_widget=None, clear_on_init=True):
        super().__init__()
        self.log_file = log_file
        self.text_widget = text_widget
        
        if text_widget:
            # 连接信号到更新GUI的槽函数
            self.output_written.connect(self.update_text_widget)
        
        if clear_on_init:
            self.clear_log_file()

    def clear_log_file(self):
        # 清空日志文件内容
        with open(self.log_file, 'w', encoding='gbk') as f:
            f.write('')  # 清空日志文件内容

    @staticmethod
    def read_log_file():
        with open(log_path, 'r', encoding='utf-8') as f:
            log_content = f.read()
            return log_content

    def write(self, message):
        if message.strip():
            # 写入文件
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(message + '\n')
            except Exception as e:
                print(f"写入日志文件失败: {e}")

            # 发送信号更新GUI
            if self.text_widget:
                self.output_written.emit(message)

    def update_text_widget(self, message):
        """更新GUI文本显示"""
        if self.text_widget:
            # 在文本末尾添加新消息
            self.text_widget.append(message)
            
            # 滚动到底部
            scrollbar = self.text_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def flush(self):
        pass



