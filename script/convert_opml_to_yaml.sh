
#!/bin/bash

# OPML 文件路径
opml_file=./resource/inoreader-opml.xml

# 转换为 YAML 文件路
yaml_file=./resource/config.yml

type=o2y

# 执行转换
python src/util.py --opml_file $opml_file --yaml_file $yaml_file --type $type

