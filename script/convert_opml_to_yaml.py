import os
import sys

import opml
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.util import md5hash_6


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

    # 将数据写入 YAML 文件
    with open(yaml_file, "w") as f:
        yaml.dump(data, f, encoding="utf-8", allow_unicode=True)

# OPML 文件路径
opml_file = "./resource/inoreader-opml.xml"

# 转换为 YAML 文件路径
yaml_file = "./resource/config.yml"

# 执行转换
convert_opml_to_yaml(opml_file, yaml_file)