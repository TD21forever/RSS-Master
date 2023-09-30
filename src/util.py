import logging
import os
import time
from typing import Union

import yaml

from root import CONFIG_PATH, LOG_DIR


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


def get_config(spec:Union[str, None] = None):
    with open(CONFIG_PATH, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    if not spec: return config
    res = config.get(spec, {})
    return res
    
def init_dirs():
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
    if not os.path.exists(CONFIG_PATH): os.makedirs(CONFIG_PATH)
    

