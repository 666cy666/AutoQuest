from src.package.utils.FileUtil import load_json, save_json
from src.package.utils.DrissionpageUtil import get_drissionPage
from src.package.config.paths import OUTPUT_DIR, WEIGHT_DIR
from selenium.webdriver.common.by import By
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
        random_count = random.randint(random_count, len(topic_answer_list))

    # 获取所有选项的权重
    weights = [option["weight"] for option in topic_answer_list]

    # 根据权重随机选择指定数量的选项,直到选够指定数量
    selected_options = []
    while len(selected_options) < random_count:
        option = random.choices(
            range(len(topic_answer_list)),
            weights=weights,
            k=1
        )[0]
        if option not in selected_options:
            selected_options.append(option)

    # 排序后返回
    return sorted(selected_options)

def input_text_from_option(other_text_list, answer_element):
    """
    从配置中根据权重随机选择一个填入填空题
    :param other_text_list: 填空题选项列表
    :param answer_element: 当前选项元素
    :return:
    """
    drissionPage = get_drissionPage()
    input_index = get_random_option_by_weight(other_text_list)[0]
    input_text = other_text_list[input_index]['text']
    drissionPage.input_text(father_element=answer_element, xpath_kind=By.XPATH,
                            xpath="./following-sibling::div[@class='ui-text']/input",
                            text=input_text, timeout=2)
    return input_text

def run(url, count_index):
    '''
    运行程序
    :param topic_data_list: 题目数据列表
    :param url: 问卷星地址
    :param count_index: 当前第几次运行
    :return:
    '''
    drissionPage = get_drissionPage()
    drissionPage.driver.get(url)
    if drissionPage.get_element(xpath_kind=By.CLASS_NAME, xpath='layui-layer-btn1', timeout=5):
        drissionPage.click_element(xpath_kind=By.CLASS_NAME, xpath='layui-layer-btn1')
    name = url.split('/')[-1].split('.')[0]
    output_dir = os.path.join(OUTPUT_DIR, f"data-{name}")
    answer_data_url = os.path.join(WEIGHT_DIR, f"data-{name}.json")
    if not os.path.exists(answer_data_url):
        print(f"答案数据不存在,请先初始化程序并调整权重")
        return False
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    topic_data_list = load_json(answer_data_url)
    topic_element_list = drissionPage.get_elements(xpath_kind=By.CLASS_NAME, xpath='field ui-field-contain')
    answer_records = []
    for index, topic_data in enumerate(topic_data_list):
        topic_answer_list = topic_data["topic-answer-list"]
        topic_element = topic_element_list[index]
        print(f"当前题目:{topic_data['topic-title']}, 题目类型:{topic_data['topic-type']}")
        record = {
            "题目序号": index + 1,
            "题目标题": topic_data['topic-title'],
            "选择答案": [],
            "填空答案": []
        }
        if topic_data["topic-type"] == "4":
            # 多选题
            answer_list = topic_element.eles((By.CLASS_NAME, 'label'))
            # 若topic_data中有minvalue属性,若无为2
            random_count = topic_data.get("minvalue", 2)
            random_index_list = get_random_option_by_weight(topic_answer_list, random_count=random_count)
            record["选择答案"] = random_index_list
            print(f"多选随机选择答案:{random_index_list}")
            for answer_index in random_index_list:
                answer_element = answer_list[answer_index]
                answer_element.click()
                if topic_answer_list[answer_index]["input"]:
                    other_text_list = topic_answer_list[answer_index]["input-text"]
                    input_text = input_text_from_option(other_text_list, answer_element)
                    record["填空答案"].extend(input_text)
        elif topic_data["topic-type"] == "3":
            # 单选题
            answer_list = topic_element.eles((By.CLASS_NAME,'label'))
            answer_index = get_random_option_by_weight(topic_answer_list)[0]
            answer_element = answer_list[answer_index]
            answer_element.click()
            record["选择答案"].append(answer_index)
            print(f"单选随机选择答案:{answer_index}")
            if topic_answer_list[answer_index]["input"]:
                other_text_list = topic_answer_list[answer_index]["input-text"]
                input_text = input_text_from_option(other_text_list, answer_element)
                record["填空答案"].extend(input_text)
        elif topic_data["topic-type"] == "1":
            # 填空题
            input_index = get_random_option_by_weight(topic_answer_list)[0]
            input_text = topic_answer_list[input_index]['text']
            print(f"填空答案{input_text}")
            drissionPage.input_text(father_element=topic_element, xpath_kind=By.XPATH, xpath='//div[@class="ui-input-text"]//input', text=input_text)
            record["填空答案"] = input_text
        answer_records.append(record)
    save_path = save_json(answer_records, os.path.join(output_dir, f"answer_records_{count_index}.json"))
    drissionPage.click_element(xpath_kind=By.ID, xpath='ctlNext')
    if drissionPage.get_element(xpath_kind=By.ID, xpath='rectMask', timeout=3):
        # 检测到有弹窗,点击确定
        drissionPage.click_element(xpath_kind=By.ID, xpath='rectMask')
        if drissionPage.get_element(xpath_kind=By.ID, xpath='nc_1_n1z', timeout=3):
            # 滑动验证码
            print("滑动验证码验证")
            drissionPage.drag_element(xpath_kind=By.ID, xpath='nc_1_n1z', right_offset=300)
    if drissionPage.get_element(xpath_kind=By.ID, xpath='divdsc',timeout=3):
        print(f"答题成功，记录答卷情况到路径:{save_path}")
        return True
    else:
        print(f"第{count_index}次运行失败,重新运行")
        return False