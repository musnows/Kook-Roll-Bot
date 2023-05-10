import aiohttp
import asyncio
import traceback
import os

from khl import Bot,Cert, Message,PrivateMessage,requester
from khl.card import Card,CardMessage,Types,Module,Element
from aiohttp import client_exceptions
from datetime import datetime,timedelta

from utils.files import *
from utils.myLog import get_time,get_time_str_from_stamp,log_msg,_log
from utils.argsCheck import get_card_msg,roll_args_check

# 用读取来的 config 初始化 bot
bot = Bot(token=config['token']) # websocket
if not config["ws"]: # webhook
    _log.info(f"[BOT] using webhook at {config['webhook_port']}")
    bot = Bot(cert=Cert(token=config['token'], verify_token=config['verify_token'],encrypt_key=config['encrypt']),
              port=config["webhook_port"])
# 配置kook头链接
kook_base_url = "https://www.kookapp.cn"
kook_headers = {f'Authorization': f"Bot {config['token']}"}
CmdLock = asyncio.Lock()
"""配置命令上锁"""

#####################################################################################

# 查看bot状态
@bot.command(name='alive',case_sensitive=False)
async def alive_check(msg:Message,*arg):
    try:
        log_msg(msg)
        await msg.reply(f"bot alive here")# 回复
    except:
        _log.exception(f"Err in alive")

# 帮助命令
@bot.command(name='rdh',aliases=['rdhelp'],case_sensitive=False)
async def help(msg:Message,*arg):
    try:
        log_msg(msg)
        # 信息主体
        text = "" if not "notice" in config else config["notice"]
        text+= "\n「/alive」看看bot是否在线\n"
        text+= "「/rd \"奖品名字\" 奖品个数 抽奖天数 @角色组」按天数开奖\n"
        text+= "「/rh \"奖品名字\" 奖品个数 抽奖小时 @角色组」按小时开奖\n"
        text+= "```\n"
        text+= "/rd \"通行证一个\" 2 2 @角色组1 @角色组2\n"
        text+= "```\n"
        text+= " 如上命令将开启一个奖品为通行证，获奖人数为2，为期2天的抽奖，并且只有指定的角色组才可以参加抽奖。\n"
        text+= "**注意事项：**\n"
        text+= " 1.奖品名字必须带上英文双引号\n 2.角色组可以不指定，即所有人可参加\n 3.抽奖天数可以设置为小数，比如半天设置为0.5\n"
        # 小字
        sub_text = f"开机于：{StartTime}  |  开源仓库：[Github](https://github.com/musnows/Kook-Roll-Bot)\n"
        sub_text+= "如有问题，请加入帮助频道咨询：[邀请链接](https://kook.top/gpbTwZ)"
        cm = await get_card_msg(text,sub_text,header_text="抽奖菈 帮助命令")
        await msg.reply(cm)
        _log.info(f"Au:{msg.author_id} | help reply")
    except Exception as result:
        _log.exception(f"Err in help")
        cm = await get_card_msg(f"ERR! [{get_time()}] help",err_card=True)
        await msg.reply(cm)

################################################################################

async def get_rid_list(arg):
    """通过参数元组获取角色id列表（str列表）"""
    temp_list = []
    for s in arg:
        temp_list.append(s.replace("(rol)",""))
    return temp_list

async def roll_card_msg(user_id:str,item_name:str,item_num:int,roll_sec:float,rid_list = [],join_count=0):
    """
    - user_id: 发起抽奖的用户id
    - item_name: 商品名字
    - item_num : 商品个数
    - roll_sec: 抽奖秒数 (距离当前时间的秒数，更新卡片的时候需要重新计算sec)
    - rid_list: 可参与抽奖用户的角色id列表
    """
    c = Card(Module.Header(f"抽奖菈！奖品「{item_name}」"),Module.Divider())
    text = f"发起者：(met){user_id}(met)\n"
    # 可参与用户
    rid_str = "全体用户"
    if rid_list: # 如果有用户列表
        rid_str = ""
        for rid in rid_list:
            rid_str+=f"(rol){rid}(rol) "
    text+= f"可参与角色：{rid_str}\n"
    # 获奖信息
    time_deta = datetime.now() + timedelta(seconds=roll_sec)
    text+= f"获奖名额：{item_num}   开奖时间：{get_time_str_from_stamp(time_deta.timestamp())}"
    c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
    c.append(Module.Countdown(time_deta, mode=Types.CountdownMode.DAY))
    text = f"当前参与人数：{join_count}" # 参与人数
    c.append(Module.Context(Element.Text(text,Types.Text.KMD)))
    return CardMessage(c)

async def roll_start_log(guild_id:str,msg_id:str,user_id:str,roll_sec:float,rid_list=[]):
    """记录开启时的抽奖信息"""
    global RollLog
    if guild_id not in RollLog['data']:
        RollLog['data'][guild_id] = {}

    cur_time = datetime.now().timestamp()
    RollLog['data'][guild_id][msg_id] = {
        "start_time":cur_time,
        "end_time": cur_time + roll_sec,
        "user_id": user_id,
        "rid_list":rid_list,
        "is_end":False,
        "join":{
            "count":0,
            "reward_user":[]
        }
    }
    RollLog['msg'][msg_id] = [] # 加入抽奖用户的list
    _log.info(f"[roll_log] Au:{user_id} | G:{guild_id} | Msg:{msg_id}")

@bot.command(name='rd',case_sensitive=False)
async def roll_day_cmd(msg:Message,name:str,num:str,roll_day:str,*arg):
    """抽奖天数命令"""
    try:
        log_msg(msg)
        if not await roll_args_check(bot,msg,num,roll_day): return

        # 获取卡片消息
        roll_time = float(roll_day) * 24 * 3600 # 一天的秒数
        rid_list = await get_rid_list(arg)
        cm = await roll_card_msg(msg.author_id,name,int(num),roll_time,rid_list)
        send_msg = await msg.reply(cm,use_quote=False) # 不引用的消息
        await roll_start_log(msg.ctx.guild.id,send_msg['msg_id'],msg.author_id,roll_time,rid_list)
        _log.info(f"Au:{msg.author_id} | rd success")
    except:
        _log.exception(f"Err in rd | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] rd",err_card=True)
        await msg.reply(cm)

@bot.command(name='rh',case_sensitive=False)
async def roll_hour_cmd(msg:Message,name:str,num:str,roll_hour:str,*arg):
    """抽奖小时命令"""
    try:
        log_msg(msg)
        if not await roll_args_check(bot,msg,num,roll_hour): return

        # 获取卡片消息
        roll_time = float(roll_hour) * 3600 # 1h的秒数
        rid_list = await get_rid_list(arg)
        cm = await roll_card_msg(msg.author_id,name,int(num),roll_time,rid_list)
        send_msg = await msg.reply(cm,use_quote=False) # 不引用的消息
        await roll_start_log(msg.ctx.guild.id,send_msg['msg_id'],msg.author_id,roll_time,rid_list)
        _log.info(f"Au:{msg.author_id} | rh success")
    except:
        _log.exception(f"Err in rd | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] rd",err_card=True)
        await msg.reply(cm)

    

################################################################################

# 开机任务
@bot.on_startup
async def startup_task(b:Bot):
    try:
        global debug_ch
        assert('admin_user' in config)
        # 获取debug频道
        debug_ch = await bot.client.fetch_public_channel(config['debug_ch'])
        _log.info("[BOT.START] fetch debug channel success")
    except:
        _log.exception(f"[BOT.START] ERR!")
        os.abort()

# botmarket通信,暂时不启用
# @bot.task.add_interval(minutes=25)
async def botmarket_ping_task():
    api = "http://bot.gekj.net/api/v1/online.bot"
    headers = {'uuid': '1d266c78-30b2-4299-b470-df0441862711'}
    async with aiohttp.ClientSession() as session:
        await session.post(api, headers=headers)
# 定时写文件，因为很多地方都写了，所以这里只需要10分钟执行一次
@bot.task.add_interval(minutes=10)
async def save_log_file_task():
    await write_roll_log(log_info="[BOT.TASK]")

# 开机 （如果是主文件就开机）
if __name__ == '__main__':
    # 开机的时候打印一次时间，记录开启时间
    _log.info(f"[BOT] Start at {get_time()}")
    bot.run()