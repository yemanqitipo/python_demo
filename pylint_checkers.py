import re
import requests
from bs4 import BeautifulSoup
import bs4
import json
import os

#这里将代理变量定义为全局变量，如果你不需要代理，应当将其改成 proxier = {}
proxies = {
    'http': 'http://127.0.0.1:10809',
    'https': 'http://127.0.0.1:10809',
}


"""
返回对应url请求的html文本
"""
def get_html(url, headers = {"user-agent": "Chrome/10"}, timeout = 30, proxies={}):
    try:
        r = requests.get(url, headers=headers, timeout=timeout, proxies=proxies)
        r.raise_for_status() #如果返回码不是200， 则跑出一个异常
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return ""

"""
在checker列表页面解析得到各个checker详情的url.
"""
def get_checker_url_list(html, checker_url_list, base_url):
    soup = BeautifulSoup(html, "html.parser")
    id_list = ['fatal', "error", "warning", "convention", "refactor", "information"]
    all_atag_list = []
    for section_id in id_list:
        category_section = soup.select_one("#"+section_id)
        atag_list = parse_list_from_category_section(category_section)
        all_atag_list.extend(atag_list)

    for atag in all_atag_list:
        url_info = get_url_info_from_atag(atag, base_url)
        checker_url_list.append(url_info)

"""
这个函数的主要逻辑和目的是：
BeautifulSoup的select默认返回的是一个ResultSet类型，我们将其改为list类型
"""
def parse_list_from_category_section(category_section):
    atag_list = []
    for atag in category_section.select("li.toctree-l1 > a"):
        atag_list.append(atag)
    return atag_list

"""
参数：
    atag：从checker list页面中解析得到的a标签。该标签包含checker详情页面的相对地址
    base_url： checker list页面的http地址
返回：
    返回是一个列表，其中包含一个checker的名字、id、类别和该checker 详情页面的http地址
"""
def get_url_info_from_atag(atag, base_url):
    checker_name= atag.string.strip().split("/")[0].strip()
    checker_id= atag.string.strip().split("/")[1].strip()
    category = get_category_by_id(checker_id)
    href = atag.get("href")
    if not href.startswith("http"):
        href = get_absolute_path(base_url, href)
    return [checker_name, checker_id, category, href]

def get_category_by_id(checker_id):
    if checker_id.startswith("E"):
        return "error"
    elif checker_id.startswith("F"):
        return "fatal"
    elif checker_id.startswith("W"):
        return "warning"
    elif checker_id.startswith("C"):
        return "convention"
    elif checker_id.startswith("R"):
        return "refactor"
    elif checker_id.startswith("I"):
        return "information"
    else:
        return "bad_practice"

def get_absolute_path(base_url, href):
    last_index = base_url.rfind("/")
    begin_url = base_url[:last_index]
    return begin_url + "/" + href

def get_checker_info_list(checker_url_list, checker_info_list):
    for checker_url in checker_url_list:
        url = checker_url[3]
        html = get_html(url, proxies=proxies)
        checker_info = get_checker_info(html, checker_url)
        if checker_info is not None:
            checker_info_list.append(checker_info)
    return

"""
在checker的告警详情页面，对其进行解析，得到checker的详情信息。用一个dict表示，具体包含：
1. name
2. id
3. category
4. url即该详情页面的http url
5. message
6. description
7. correct_code
8. problematic_code
"""
def get_checker_info(html, checker_url):
    checker_name = checker_url[0]
    checker_id = checker_url[1]
    checker_info = {}
    soup = BeautifulSoup(html, 'html.parser')
    tag_selector_prefix = "#" + checker_name + "-" + checker_id.lower()
    print(tag_selector_prefix)
    message_emitted_p_tag = soup.select_one(tag_selector_prefix + "> p:nth-child(4)")
    if message_emitted_p_tag is None:
        return None
    message = message_emitted_p_tag.get_text()
    description_em_tag = soup.select_one(tag_selector_prefix + "> p:nth-child(6) > em")
    description = description_em_tag.string.strip()
    checker_info["message"] = message
    checker_info["description"] = description

    correct_code_tag = soup.select_one(tag_selector_prefix + ">div:nth-child(8) > div")
    if correct_code_tag is not None:
        checker_info["correct_code"] = correct_code_tag.__str__()
    else:
        checker_info["correct_code"] = None

    problematic_code_tag = soup.select_one(tag_selector_prefix + ">div:nth-child(10) > div")
    if correct_code_tag is not None:
        checker_info["problematic_code"] = problematic_code_tag.__str__()
    else:
        checker_info["problematic_code"] = None

    checker_info["name"] = checker_name
    checker_info["id"] = checker_id
    checker_info["category"] = checker_url[2]
    checker_info["href"] = checker_url[3]
    return checker_info

"""
将checker告警详情信息的列表写入json文件中
"""
def save_checker_info_list(checker_info_list, json_file):
    with open(json_file, 'w') as f:
        json.dump(checker_info_list, f)

proxies = {
    'http': 'http://127.0.0.1:10809',
    'https': 'http://127.0.0.1:10809',
}

"""
测试函数，用于调试在解析checker详情页面时的异常
"""
def get_checker_html_test():
    url = "https://pylint.pycqa.org/en/latest/messages/warning/subprocess-run-check.html"
    html = get_html(url, proxies=proxies)
    soup = BeautifulSoup(html, 'html.parser')
    message_emitted_p_tag = soup.select_one("#subprocess-run-check-w1510 > p:nth-child(4)")
    if message_emitted_p_tag is None:
        return None
    message = message_emitted_p_tag.get_text()
    description_em_tag = soup.select_one("#subprocess-run-check-w1510 > p:nth-child(6)>em")
    description = description_em_tag.string.strip()

    checker_info = {}
    correct_code_tag = soup.select_one("#subprocess-run-check-w1510 > p:nth-child(8) > div")
    problematic_code_tag = soup.select_one("#subprocess-run-check-w1510 > p:nth-child(8) > div")
    if correct_code_tag is not None:
        checker_info["problematic_code"] = problematic_code_tag.__str__()
    else:
        checker_info["problematic_code"] = None

    return checker_info

if __name__ == "__main__":
    url = "https://pylint.pycqa.org/en/latest/messages/messages_list.html"
    checker_url_list = []
    checker_info_list = []

    html = get_html(url, proxies=proxies)
    get_checker_url_list(html, checker_url_list, url)
    get_checker_info_list(checker_url_list, checker_info_list)
    json_file = "pylint_checker_list.json"
    save_checker_info_list(checker_info_list, json_file)
    print(len(checker_info_list))

    # get_checker_html()
