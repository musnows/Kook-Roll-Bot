import sys
import logging # 采用logging来替换所有print
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime,timezone,timedelta
from khl import Message,PrivateMessage

LOGGER_NAME = "bot-log" # 日志对象名字，这个没啥用
LOGGER_FILE = "bot.log" # 如果想修改log文件的名字和路径，修改此变量
"""日志文件路径"""

#将获取当前时间封装成函数方便使用
def get_time(format_str='%y-%m-%d %H:%M:%S'):
    """获取当前时间，格式为 `23-01-01 00:00:00`"""
    utc_dt = datetime.now(timezone.utc) # 获取当前时间
    beijing_time = utc_dt.astimezone(timezone(timedelta(hours=8))) # 转换为北京时间
    return beijing_time.strftime(format_str)
    # return time.strftime("%y-%m-%d %H:%M:%S", time.localtime())

def get_time_str_from_stamp(timestamp:float,format_str='%y-%m-%d %H:%M:%S'):
    """通过时间戳获取当前的本地时间，格式 23-01-01 00:00:00"""
    a = datetime.fromtimestamp(timestamp,tz=timezone(timedelta(hours=8)))
    return a.strftime(format_str)

def log_flush():
    """刷新输出缓冲区"""
    sys.stdout.flush() # 刷新缓冲区
    sys.stderr.flush() # 刷新缓冲区

def log_msg(msg:Message):
    """命令日志"""
    try:
        gid,chid = "pm","pm"
        if not isinstance(msg, PrivateMessage): # 不是私聊
            chid = msg.ctx.channel.id
            gid = msg.ctx.guild.id
        # 打印日志
        _log.info(
            f"G:{gid} | C:{chid} | Au:{msg.author_id} {msg.author.username}#{msg.author.identify_num} = {msg.content}"
        )
        log_flush() # 刷缓冲区
    except:
        _log.exception(f"err in logging")


def beijing(sec, what):
    """日志返回北京时间的处理"""
    utc_dt = datetime.now(timezone.utc) # 获取当前时间
    beijing_time = utc_dt.astimezone(timezone(timedelta(hours=8))) # 转换为北京时间
    return beijing_time.timetuple()
# 日志时间改为北京时间
logging.Formatter.converter = beijing # type:ignore

# 只打印info以上的日志（debug低于info）
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] %(levelname)s:%(filename)s:%(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%y-%m-%d %H:%M:%S")
# 获取一个logger对象
_log = logging.getLogger(LOGGER_NAME)
"""自定义的logger对象"""
# 1.实例化控制台handler和文件handler，同时输出到控制台和文件
file_handler = logging.FileHandler(LOGGER_FILE, mode="a", encoding="utf-8")
fmt = logging.Formatter(fmt="[%(asctime)s] %(levelname)s:%(filename)s:%(funcName)s:%(lineno)d | %(message)s",
                    datefmt="%y-%m-%d %H:%M:%S")
file_handler.setFormatter(fmt)
# 2.按每天来自动生成日志文件的备份
log_handler = TimedRotatingFileHandler(LOGGER_FILE, when='D',interval=3)
log_handler.setFormatter(fmt)
# 3.添加个日志处理器
# _log.addHandler(file_handler) # 这个不用加，时间的日志处理器已经有这个功能了
_log.addHandler(log_handler)