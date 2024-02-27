import os
import logging
from datetime import datetime


class Logger(object):
    def __init__(self, log_dir= "info/log"):
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "log.txt")
        # if os.path.exists(log_path):
        #     os.remove(log_path)
        logging.basicConfig(filename= log_path, level=logging.INFO)

    def log(self, content):
        # 获取当前时间
        current_time = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        logging.info(current_time + content)
        # print(content)
        
    def log(self, *args):
        content = ""
        for arg in args:
            content += str(arg) + " "
        # 获取当前时间
        current_time = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
        logging.info(current_time + content)
        # print(content)
    

        
# 创建全局的Logger对象
logger = Logger()
