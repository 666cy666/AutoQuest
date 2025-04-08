from Util.drissionpage_util import drissionPage
from DrissionPage._functions.by import By
import random
from Util.FileUtil import save_label_json, get_base_dir
import os

def initialize(url):
    # url = 'https://www.wjx.cn/vm/tL4FoDX.aspx'
    drissionPage.driver.get(url)
    topic_element_list = drissionPage.get_elements(xpath_kind=By.CLASS_NAME, xpath='field ui-field-contain')
    topic_data_list = []
    for topic in topic_element_list:
        topic_type = topic.attrs["type"]
        topic_answer_list = []
        topic_title = drissionPage.get_element_text(father_element=topic, xpath_kind=By.CLASS_NAME, xpath='topichtml')
        topic_answers = drissionPage.get_elements(father_element=topic, xpath_kind=By.XPATH, xpath='//div[@class="ui-controlgroup column1"]/div')
        # print(len(topic_answers))
        all_weight = 100
        true_count = 0
        for topic_answer in topic_answers:
            element = topic_answer.ele((By.CLASS_NAME,'label'))
            text = element.text
            answer = {
                "text": text,
                "weight": 0,
                "input": False,
            }
            if len(topic_answer.eles((By.XPATH,'./*'))) > 2:
                # print("填空题")
                weight = random.randint(1, 5)
                answer["weight"] = weight
                answer["input"] = True
                answer["input-text"] = ['无']
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
        topic_data_list.append(topic_data)
    print(topic_data_list)
    # 截取url最后的字符串
    name = url.split('/')[-1].split('.')[0]
    save_path = save_label_json(topic_data_list, name)
    output_dir = os.path.join(get_base_dir(), "Output", f"data-{name}")
    os.makedirs(output_dir, exist_ok=True)
    print(f"保存初始化权重保存路径: {save_path}")
    print(f"答案选择输出路径: {output_dir}")