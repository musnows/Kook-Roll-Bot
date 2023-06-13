import os
import json
import asyncio
from .myLog import _log,get_time


FlieSaveLock = asyncio.Lock()
"""用于日志文件写入的锁"""
StartTime = get_time()
"""机器人启动时间"""


def write_file(path: str, value):
    """写入文件"""
    with open(path, 'w+', encoding='utf-8') as fw2:
        json.dump(value, fw2, indent=2, sort_keys=True, ensure_ascii=False)

def open_file(path:str):
    """读取json文件"""
    with open(path, 'r', encoding='utf-8') as f:
        tmp = json.load(f)
    return tmp


def create_log_file(path: str, content):
    """create path/file

    Retrun value
    - False: path exist but keyerr / create false
    - True: path exist / path not exist, create success
    """
    try:
        # 如果文件路径存在
        if os.path.exists(path):
            tmp = open_file(path)  # 打开文件
            for key in content:  # 遍历默认的键值
                if key not in tmp:  # 判断是否存在
                    _log.critical(f"[file] ERR! files exists, but key '{key}' not in {path}")
                    return False
            return True
        # 文件路径不存在，通过content写入path
        write_file(path, content)
        return True
    except Exception as result:
        _log.exception(f"create log file ERR!")
        return False


##################机器人需要用到的文件##############################################

config = open_file('./config/config.json')
"""机器人配置文件"""

# 打开日志文件
RollLogPath = './config/rollLog.json'
"""日志文件路径"""
RollLog = {"data":{},"msg":{},'err_msg':{}}
"""日志文件 {"data":{},"msg":{},'err_msg':{}}"""

try:
    # 自动创建日志文件
    if (not create_log_file(RollLogPath,RollLog)):
        os._exit(1)  # err,退出进程

    # 创建日志文件成功，打开
    RollLog = open_file(RollLogPath)
    """日志文件 {"data":{},"msg":{}}"""

    _log.info(f"[BOT.INIT] open log.files success!")
except:
    _log.info(f"[BOT.INIT] open log.files ERR")
    os.abort()


async def write_roll_log(log_info=""):
    """将抽奖记录写入日志"""
    try:
        global FlieSaveLock
        async with FlieSaveLock:
            write_file(RollLogPath,RollLog)
            _log.info(f"[write.file] RollLog to {RollLogPath} | {log_info}")
    except:
        _log.exception(f"Err when write file")
