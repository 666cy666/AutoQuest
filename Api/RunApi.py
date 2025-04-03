from Util.FileUtil import load_json, save_json
from Util.drissionpage_util import drissionPage
from selenium.webdriver.common.by import By
from time import sleep
import os
import random
def get_random_option_by_weight(topic_answer_list, random_count=1):
    """
    根据权重随机选择选项
    :param topic_answer_list: 选项列表
    :param random_count: 需要选择的数量,默认为1
    :return: 选中的选项索引列表（始终返回列表类型）
    """
    # 如果是多选题,随机生成选择数量
    if random_count > 1:
        random_count = random.randint(1, min(random_count, len(topic_answer_list)))

    # 获取所有选项的权重
    weights = [option["weight"] for option in topic_answer_list]

    # 根据权重随机选择指定数量的选项
    selected_options = random.choices(
        range(len(topic_answer_list)),
        weights=weights,
        k=random_count
    )

    # 去重并排序，始终返回列表
    return sorted(list(set(selected_options)))

def run(url, count=10):
    '''
    运行程序
    :param topic_data_list: 题目数据列表
    :param url: 问卷星地址
    :param count: 运行次数,默认为10
    '''
    drissionPage.driver.get(url)
    sleep(1)
    if drissionPage.get_element(xpath_kind=By.CLASS_NAME,xpath='layui-layer-btn1',timeout=2):
        drissionPage.click_element(xpath_kind=By.CLASS_NAME,xpath='layui-layer-btn1')
    name = url.split('/')[-1].split('.')[0]
    output_dir = os.path.join(os.getcwd(), "Output", f"data-{name}")
    answer_data_url = os.path.join(os.getcwd(), "Config", f"data-{name}.json")
    if not os.path.exists(answer_data_url):
        print(f"答案数据不存在,请先初始化程序并调整权重")
        return
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    topic_data_list = load_json(answer_data_url)
    topic_element_list = drissionPage.get_elements(xpath_kind=By.CLASS_NAME, xpath='field ui-field-contain')
    answer_records = []
    for index,topic_data in enumerate(topic_data_list):
        topic_answer_list = topic_data["topic-answer-list"]
        answer_list = topic_element_list[index].eles((By.CLASS_NAME,'label'))
        print(f"当前题目:{topic_data['topic-title']}")
        record = {
            "题目序号": index + 1,
            "题目标题": topic_data['topic-title'],
            "选择答案": [],
            "填空答案": []
        }
        if topic_data["topic-type"] == "4":
            # 多选题
            random_index_list = get_random_option_by_weight(topic_answer_list, random_count=2)
            record["选择答案"] = random_index_list
            print(f"多选随机选择答案:{random_index_list}")
            for answer_index in random_index_list:
                answer_list[answer_index].click()
                if topic_answer_list[answer_index]["input"]:
                    input_text = topic_answer_list[answer_index]["input-text"]
                    record["填空答案"].extend(input_text)

        elif topic_data["topic-type"] == "3":
            # 单选题
            random_index = get_random_option_by_weight(topic_answer_list)[0]
            answer_list[random_index].click()
            record["选择答案"].append(random_index)
            print(f"单选随机选择答案:{random_index}")
            if topic_answer_list[random_index]["input"]:
                input_text = topic_answer_list[random_index]["input-text"]
                record["填空答案"].extend(input_text)

        answer_records.append(record)
    # break
    save_path = save_json(answer_records, os.path.join(output_dir, f"answer_records_{count}.json"))
    drissionPage.click_element(xpath_kind=By.ID, xpath='ctlNext')
    if drissionPage.get_element(xpath_kind=By.ID,xpath='rectMask',timeout=3):
        drissionPage.click_element(xpath_kind=By.ID, xpath='rectMask')
    if drissionPage.get_element(xpath_kind=By.ID,xpath='divdsc',timeout=3):
        print(f"答题成功，记录答卷情况到路径:{save_path}")
        run(url, count-1)
    else:
        print(f"第{count}次运行失败,重新运行")
        run(url, count)