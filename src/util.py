import argparse
import hashlib
import logging
import os
import sys
import time
import xml.etree.ElementTree as ET
from typing import Union

import opml
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from root import BASE_URL, CONFIG_PATH, LOG_DIR


def init_logger():
    """
    A logger that can show a message on standard output and write it into the
    file named `filename` simultaneously.
    All the message that you want to log MUST be str.

    Args:
        config (Config): An instance object of Config, used to record parameter information.

    Example:
        >>> logger = logging.getLogger(config)
        >>> logger.debug(train_state)
        >>> logger.info(train_result)
    """
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
    
    current_date = time.strftime("%Y-%m-%d", time.localtime())
    logfilename = f"{current_date}.log"

    logfilepath = os.path.join(LOG_DIR, logfilename)

       # 创建日志格式器
    filefmt = "[%(asctime)s]-[%(levelname)s]:%(message)s"
    filedatefmt = "%Y-%m-%d"
    file_formatter = logging.Formatter(filefmt, filedatefmt)

    sfmt = "[%(asctime)s]-[%(levelname)s]:%(message)s"
    sdatefmt = "%Y-%m-%d"
    sformatter = logging.Formatter(sfmt, sdatefmt)
    
    level = logging.INFO
    
    fh = logging.FileHandler(logfilepath)
    fh.setLevel(level)
    fh.setFormatter(file_formatter)

    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(sformatter)

    logging.basicConfig(level=level, handlers=[sh, fh])


def get_config():
    with open(CONFIG_PATH, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config
    
def init_dirs():
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
    if not os.path.exists(CONFIG_PATH): os.makedirs(CONFIG_PATH)
    

def md5hash_6(text:str):
    m = hashlib.md5()
    m.update(text.encode("utf-8"))
    return m.hexdigest()[:6]


def convert_yaml_to_opml(yaml_path, opml_path):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)

    
    opml = ET.Element("opml", version="1.0")
    head = ET.SubElement(opml, "head")
    title = ET.SubElement(head, "title")
    title.text = "Feeds of 435212619 from Inoreader [https://www.inoreader.com]"
    
    body = ET.SubElement(opml, "body")

    for category_name, categoty_vals in data.items():
        outline = ET.SubElement(body, 'outline', text=category_name, title=category_name)
        for item in categoty_vals:
            url = BASE_URL + item["name"] + ".xml"
            feed_outline = ET.SubElement(outline, "outline", text=item['text'], title=item['text'], type='rss',
                                        xmlUrl=url, htmlUrl=item['htmlUrl'])
    
    tree = ET.ElementTree(opml)
    tree.write(opml_path, encoding='utf-8', xml_declaration=True)
    

def convert_opml_to_yaml(opml_file, yaml_file):
    # 使用 opml 库解析 OPML 文件
    with open(opml_file, "r") as f:
        opml_data = opml.parse(f)

    # 创建 YAML 数据结构
    data = {}

    # 遍历大纲项
    for outline in opml_data:
        group = outline.text
        if group:
            data[group] = []
            for child in outline:
                item = {}
                item["url"] = child.xmlUrl
                item["text"] = child.text
                item["htmlUrl"] = child.htmlUrl
                item["name"] = md5hash_6(item["url"])
                data[group].append(item)

    # 如果yaml文件存在,则改名,防止丢失
    if os.path.exists(yaml_file):
        os.rename(yaml_file, yaml_file + ".bak")
        
    # 将数据写入 YAML 文件
    with open(yaml_file, "w") as f:
        yaml.dump(data, f, encoding="utf-8", allow_unicode=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--opml_file", help="Path to the OPML file")
    parser.add_argument("--yaml_file", help="Path to the YAML file")
    parser.add_argument("--type", help="Type of the conversion")
    args = parser.parse_args()
    print(args.opml_file, args.yaml_file)
    if args.type == "y2o":
        convert_yaml_to_opml(args.yaml_file, args.opml_file)
    else:
        convert_opml_to_yaml(args.opml_file, args.yaml_file)