# 文件工具函数
import os
import time
import shutil
import sys
import json
import random
sys.path.append('./Util')

# 初始化文件夹
def init_folder():
    # 获取当前脚本所在目录
    current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, "Output")
    log_dir = os.path.join(current_dir, "Log")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)

# 根据时间戳返回文件名
def get_file_name_by_timestamp():
    return time.strftime("%Y%m%d%H%M%S", time.localtime())

def get_random_option_by_percent(topic_data):
    # 计算每个选项的权重
    weights = [option["percent"] for option in topic_data["topic_answer"]]
    # 根据权重随机选择一个选项
    random_option = random.choices(topic_data["topic_answer"], weights=weights, k=1)[0]
    # 获取随机选择的选项的下标
    random_index = topic_data["topic_answer"].index(random_option)
    # 返回随机选择的选项的下标
    return random_index

def get_random_item(list_data):
    # 随机选择一个选项
    random_item = random.choice(list_data)
    return random_item

def save_label_json(file_content, file_name="", is_extend=False):
    """
    保存JSON标签文件
    :param file_content: 爬取结果（字典）
    :param file_name: 文件名（不包含扩展名）
    :param is_extend: 是否追加文件
    :return: 保存的文件路径
    """
    try:
        # 获取当前脚本所在目录
        current_dir = os.getcwd()
        output_dir = os.path.join(current_dir, "Config")
        
        # 生成文件名
        file_name = "data-" + file_name + ".json"
        json_path = os.path.join(output_dir, file_name)
        
        # 保存JSON文件
        with open(json_path, "w" if not is_extend else "a", encoding="utf-8") as f:
            json.dump(file_content, f, ensure_ascii=False, indent=4)
        return json_path
    except Exception as e:
        print(f"JSON文件时发生错误: {str(e)}")
        raise

def save_json(file_content, file_path): 
    """
    保存JSON文件
    :param file_content: 保存内容
    :param file_path: 文件路径
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(file_content, f, ensure_ascii=False, indent=4)
    return file_path

def load_json(file_path):
    """
    加载JSON文件
    :param file_path: JSON文件路径
    :return: JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件时发生错误: {str(e)}")
        return None

def save_temp(file_path):
    # 将file_path保存到temp目录下
    current_dir = os.getcwd()
    output_dir = os.path.join(current_dir, "Output", "temp")
    file_name = os.path.basename(file_path)
    temp_path = os.path.join(output_dir, file_name)
    shutil.copy(file_path, temp_path)
    return temp_path

class SettingLoader:
    _instance = None
    _key_mapping = None
    _json_path = 'Config/setting.json'

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingLoader, cls).__new__(cls)
            cls._key_mapping = load_json(cls._json_path)
        return cls._instance

    @classmethod
    def get_key_mapping(cls):
        """
        获取关键词映射数据
        :return: 关键词映射字典
        """
        if cls._key_mapping is None:
            cls._key_mapping = load_json(cls._json_path)
        return cls._key_mapping

    @classmethod
    def reload(cls):
        """
        重新加载关键词映射数据
        """
        cls._key_mapping = load_json(cls._json_path)

