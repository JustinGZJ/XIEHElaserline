# logger.py
import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logger():
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    mylogger = logging.getLogger("my-logger")
    mylogger.setLevel(logging.INFO)

    # 构造文件路径
    log_file_path = os.path.join(log_directory, "app.log")

    # 创建一个滚动日志处理器
    handler = RotatingFileHandler(
        log_file_path, maxBytes=1048576, backupCount=5  # 文件大小为1MB，保留5个备份
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    mylogger.addHandler(handler)
    return mylogger


# 确保只配置一次
logger = setup_logger()
