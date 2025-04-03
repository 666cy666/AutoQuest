import os
import re
import shutil
import subprocess

from DrissionPage._configs.chromium_options import ChromiumOptions
from DrissionPage._elements.chromium_element import ChromiumElement
from DrissionPage._base.chromium import Chromium
from DrissionPage._elements.none_element import NoneElement
from functools import wraps

from DrissionPage.errors import PageDisconnectedError
from injector import inject, Module, provider, singleton, Injector
from selenium.common import SessionNotCreatedException
from selenium.webdriver.chrome import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from DrissionPage import ChromiumPage
from webdriver_manager.chrome import ChromeDriverManager


def choose_driver():

    driver_list = ['Chorme', 'Edge']
    driver_name = 'Edge'
    # 设置启动端口，静音
    co = ChromiumOptions().set_address("127.0.0.1:9222").mute(True)

    chromium_driver = Chromium(addr_or_opts=co)  # 重新创建 Chromium 实例
    # 挂载dom后加载
    chromium_driver.set.load_mode.normal()
    return chromium_driver # 获取最新的标签页


class DrissionPage_Util:
    def __init__(self, driver=None):
        self.drissionpage = choose_driver()
        self.driver = self.drissionpage.latest_tab if driver is None else driver

    @staticmethod
    def locate_element(func):
        @wraps(func)
        def wrapper(self, xpath, xpath_kind=By.XPATH, father_element=None, wait=False, timeout=3, *args, **kwargs):
            try:
                # 如果父元素为空，获取默认的 ChromiumPage 实例
                if father_element is None:
                    father_element = self.driver
                # 显示等待，直到元素加载完成或超时
                if wait and not father_element.wait.eles_loaded((xpath_kind, xpath), timeout=timeout):
                    print("Element not loaded: " + xpath)
                    return None
                # 若xpath_kind 为 NONE
                if xpath_kind == None:
                    element = father_element.ele(xpath, timeout=timeout)
                else:
                    element = father_element.ele((xpath_kind, xpath), timeout=timeout)
                # 如果元素是 NoneElement，返回 None
                if isinstance(element, NoneElement):
                    print("Element not found: " + xpath)
                    return None
                # 如果找到了元素，调用原函数
                return func(self, element, *args, **kwargs)
            except Exception as e:
                return None
        return wrapper

    @locate_element
    def get_element(self, element):
        return element

    @locate_element
    def get_element_text(self, element):
        text = element.text.strip()  # 移除可能的前后空白字符
        return text if text else "None"  # 如果文本不为空，则返回文本，否则返回None

    def get_text(self, element):
        text = element.text.strip()  # 移除可能的前后空白字符
        return text if text else "None"  # 如果文本不为空，则返回文本，否则返回None

    @locate_element
    def get_element_attribute(self, element, attribute='href'):
        # 'textContent' 标签内的文字
        # 'innerHTML'   标签的html
        # 'outerHTML'   标签的完整 html
        # ’href'        链接地址
        print(element.attr('html'))
        return element.attr(attribute)

    def get_attribute(self, element, attribute='href'):
        # 'textContent' 标签内的文字
        # 'innerHTML'   标签的html
        # 'outerHTML'   标签的完整 html
        # ’href'        链接地址
        print(element.attr('html'))
        return element.attr(attribute)

    @locate_element
    def drag_element(self, element, left_offset=0, right_offset=0):
        tab = Chromium().latest_tab
        # 左键按住元素
        if right_offset > 0:
            tab.actions.hold(element).right(right_offset).release()
        elif left_offset > 0:
            tab.actions.hold(element).left(left_offset).release()
        else:
            print("请输入正确的偏移量！")

    @locate_element
    def click_element(self, element, set_new_window=False, is_new_window=False):
        if is_new_window:
            return element.click.for_new_tab()
        else:
            self.driver.actions.click(element)
        if set_new_window:
            self.set_window_newest()

    def click(self, element, set_new_window=False, is_new_window=False):
        if is_new_window:
            return element.click.for_new_tab()
        else:
            self.driver.actions.click(element)
        if set_new_window:
            self.set_window_newest()

    @locate_element
    def input_text(self, element, text):
        element.clear()
        element.input(text)

    @locate_element
    def hover_element(self, element):
        element.hover()

    @staticmethod
    def locate_elements(func):
        @wraps(func)
        def wrapper(self, xpath, xpath_kind=By.XPATH, father_element=None, timeout=3, *args, **kwargs):
            try:
                # 如果父元素为空，获取默认的 ChromiumPage 实例
                if father_element is None:
                    father_element = self.driver
                # 定位元素
                element = father_element.eles((xpath_kind, xpath), timeout=timeout)
                # 如果元素是 NoneElement，返回 None
                if isinstance(element, NoneElement):
                    return None
                # 如果找到了元素，调用原函数
                return func(self, element, *args, **kwargs)
            except Exception as e:
                return None
        return wrapper

    # 批量解决同一类型元素，对特殊元素需自己进行调用单个元素方法处理
    @locate_elements
    def get_elements(self, elements):
        return elements

    def set_window_newest(self):
        browser = Chromium()
        self.driver = browser.latest_tab

    def close_window(self, set_new_window=False):
        if set_new_window:
            self.set_window_newest()
        self.driver.close()

    def load_page(self):
        self.driver.wait.load_start()

    def destory(self):
        self.driver.close()


class BrowserModule(Module):
    @singleton  # 确保此提供的对象为单例
    @provider   # 用于标记方法为提供依赖的工厂方法
    def provide_browser(self) -> DrissionPage_Util:
        # 第一次访问时才创建实例，后续访问都返回同一个实例
        try:
            if not hasattr(self, "drissionPage"):
                self.drissionPage = DrissionPage_Util()  # 创建实例
        except PageDisconnectedError as e:
            self.drissionPage = DrissionPage_Util()  # 创建实例
        return self.drissionPage  # 后续返回的是已经创建的单例实例


def get_drissionPage():
    injector = Injector([BrowserModule])
    # 通过 Injector 获取 ChromiumPage 单例实例
    return injector.get(DrissionPage_Util)

drissionPage = get_drissionPage()


# def update_chrome_driver_by_windows():
#     """判断谷歌驱动版本是否和谷歌浏览器版本一致"""
#     print("正在检查谷歌浏览器驱动版本是否一致，不一致将重新下载")
#     # 谷歌浏览器可执行文件的完整路径
#     chrome_path = r'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
#     # 指定谷歌驱动目标位置
#     current_directory = os.getcwd()
#     # 构建目标文件夹路径
#     target_directory = os.path.join(current_directory, "drive")
#     # 驱动名称
#     file_name = 'chromedriver.exe'
#     # 路径拼接
#     file_path = os.path.join(target_directory, file_name)
#
#     if os.path.exists(file_path):
#         # 获取chromedriver.exe版本(谷歌浏览器驱动)
#         result = subprocess.run([file_path, '--version'], capture_output=True, text=True)
#         driverversion = '.'.join(result.stdout.strip().split(' ')[1].split('.')[:-1])
#         # 获取chrome.exe版本(谷歌浏览器)
#         command = f'wmic datafile where name="{chrome_path}" get Version /value'
#         result_a = subprocess.run(command, capture_output=True, text=True, shell=True)
#         output = result_a.stdout.strip()
#         chromeversion = '.'.join(output.split('=')[1].split('.')[0:3])
#         # 判断版本是否一致，不一致就重新下载
#         if driverversion != chromeversion:
#             # 使用ChromeDriverManager安装ChromeDriver，并获取驱动程序的路径
#             download_driver_path = ChromeDriverManager().install()
#             # 复制文件到目标位置
#             shutil.copy(download_driver_path, target_directory)
#         else:
#             print("版本一致，无需重新下载！")
#     else:
#         download_driver_path = ChromeDriverManager().install()
#         shutil.copy(download_driver_path, target_directory)
#
#     return file_path

# def update_driver():
#     from Util.file_util import loading_memory
#     driverIndex = loading_memory("driverIndex")
#     driverPath = loading_memory("driverPath")
#     driver_list = ['Chorme', 'Edge']
#     driver_name = driver_list[driverIndex]
#     if driver_name == 'Chorme':
#         driverPath = ChromeDriverManager().install()

