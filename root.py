import os
from functools import partial
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
absolute = partial(os.path.join, BASE_DIR)

LOG_DIR = absolute("log")
DOCS_DIR = absolute("docs")

RSS_TEMPLATE_PATH = absolute("resource/template.xml")
RSS_HTML_TEMPLATE_PATH = absolute("resource/template.html")
CONFIG_PATH = absolute("resource/config.yml")

# Allow customization of BASE_URL through environment variables
BASE_URL = os.getenv("RSS_BASE_URL", "https://www.dcts.top/rssdocs/")

CACHE_PATH = absolute("resource/cache.pkl")

COST_RECORD_PATH = absolute("resource/cost.xlsx")