from src.package.utils.DrissionpageUtil import get_drissionPage
from DrissionPage._functions.by import By
import random
from src.package.utils.FileUtil import save_label_json
from src.package.config.paths import OUTPUT_DIR, WEIGHT_DIR
import os

from PyQt6.QtWidgets import QMessageBox

def check_weight_path(url):
    """
    :param url: 问卷链接
    :return: 是否继续运行
    """
    name = url.split('/')[-1].split('.')[0]
    weight_path = os.path.join(WEIGHT_DIR, f"data-{name}.json")
    if os.path.exists(weight_path):
        print("检测到当前问卷已初始化")
        msg_box = QMessageBox()
        msg_box.setWindowTitle('提示')
        msg_box.setText('当前问卷已初始化，是否重新初始化?')
        msg_box.setStandardButtons(QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        reply = msg_box.exec()  # PyQt6使用exec()而不是exec_()
        # 如果用户选择否,则返回
        if reply == QMessageBox.StandardButton.No:
            return False
    return True


def initialize(url):
    # 检查是否已初始化并继续运行
    if not check_weight_path(url):
        print("拒绝初始化")
        return
    name = url.split('/')[-1].split('.')[0]
    output_dir = os.path.join(OUTPUT_DIR, f"data-{name}")
    drissionPage = get_drissionPage()
    drissionPage.driver.get(url)
    topic_element_list = drissionPage.get_elements(xpath_kind=By.CLASS_NAME, xpath='field ui-field-contain')
    topic_data_list = []
    for topic in topic_element_list:
        topic_type = topic.attrs["type"]
        topic_answer_list = []
        topic_title = drissionPage.get_element_text(father_element=topic, xpath_kind=By.CLASS_NAME, xpath='topichtml')
        if topic_type == "1":
            # 单独填空题
            topic_answer_list = [{
                "text": "无",
                "weight": 100
            }]
        else:
            topic_answers = drissionPage.get_elements(father_element=topic, xpath_kind=By.XPATH,
                                                      xpath='//div[@class="ui-controlgroup column1"]/div')
            # print(len(topic_answers))
            all_weight = 100
            true_count = 0
            for topic_answer in topic_answers:
                element = topic_answer.ele((By.CLASS_NAME, 'label'))
                text = element.text
                answer = {
                    "text": text,
                    "weight": 0,
                    "input": False,
                }
                if len(topic_answer.eles((By.XPATH, './*'))) > 2:
                    # print("多选或单选中的填空题")
                    weight = random.randint(1, 5)
                    answer["weight"] = weight
                    answer["input"] = True
                    answer["input-text"] = [{
                        "text": "无",
                        "weight": 100
                    }]
                    all_weight -= weight
                    true_count += 1
                topic_answer_list.append(answer)
            # print(topic_answer_list)
            aver_weight = int(round(all_weight / (len(topic_answers) - true_count), 2))
            for answer in topic_answer_list:
                if not answer["input"]:
                    answer["weight"] = aver_weight
        # print()
        topic_data = {
            "topic-type": topic_type,
            "topic-title": topic_title,
            "topic-answer-list": topic_answer_list
        }
        # 若topic中有minvalue属性, 废弃，大多数问卷没有这个属性，同时设置多选最小都为2
        if topic.attrs.__contains__("minvalue"):
            topic_data["topic-minvalue"] = topic.attrs["minvalue"]
        topic_data_list.append(topic_data)
    print(topic_data_list)
    # 截取url最后的字符串
    os.makedirs(output_dir, exist_ok=True)
    save_path = save_label_json(topic_data_list, name)
    print(f"保存初始化权重保存路径: {save_path}")
    print(f"答案选择输出路径: {output_dir}")