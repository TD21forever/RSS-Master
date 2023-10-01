import os
from functools import partial

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
absolute = partial(os.path.join, BASE_DIR)

LOG_DIR = absolute("log")
DOCS_DIR = absolute("doc")

RSS_TEMPLATE_PATH = absolute("resource/template.xml")
RSS_HTML_TEMPLATE_PATH = absolute("resource/template.html")
CONFIG_PATH = absolute("resource/config.yml")