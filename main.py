import json
import aiohttp
import asyncio
import traceback
import os

from khl import Bot,Cert, Message,PrivateMessage,requester
from khl.card import Card,CardMessage,Types,Module,Element
from aiohttp import client_exceptions

from utils.files import *
from utils.myLog import get_time,log_flush,log_msg,_log

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

async def get_card_msg(text:str,sub_text="",header_text="",err_card=False):
    """获取一个简单卡片的函数"""
    c = Card()
    if header_text !="":
        c.append(Module.Header(header_text))
        c.append(Module.Divider())
    if err_card:# 错误卡
        text += f"\n```\n{traceback.format_exc()}\n```\n"
    # 总有内容
    c.append(Module.Section(Element.Text(text,Types.Text.KMD)))
    if sub_text != "":
        c.append(Module.Context(Element.Text(sub_text,Types.Text.KMD)))
    return CardMessage(c)

# 查看bot状态
@bot.command(name='alive',case_sensitive=False)
async def alive_check(msg:Message,*arg):
    try:
        log_msg(msg)
        await msg.reply(f"bot alive here")# 回复
    except:
        _log.exception(f"Err in help")

# 帮助命令
@bot.command(name='rdh',aliases=['rdhelp'],case_sensitive=False)
async def help(msg:Message,*arg):
    try:
        log_msg(msg)
        text = "" if not "notice" in config else config["notice"]
        text+= "\n「/alive」看看bot是否在线\n"
        text+= "「/rd \"奖品名字\" 奖品个数 抽奖天数 @角色组」开奖\n"
        text+= "```\n"
        text+= "/rd \"通行证一个\" 2 2 @角色组1 @角色组2\n"
        text+= "```\n"
        text+= " 如上命令将开启一个奖品为通行证，获奖人数为2，为期2天的抽奖，并且只有指定的角色组才可以参加抽奖。\n"
        text+= "**注意事项：**\n"
        text+= " 1.奖品名字必须带上英文双引号\n 2.角色组可以不指定，即所有人可参加\n 3.抽奖天数可以设置为小数，比如半天设置为0.5\n"
        cm = CardMessage()
        c = Card(
            Module.Header(f"开奖菈 帮助命令"),
            Module.Divider(),
            Module.Section(Element.Text(text,Types.Text.KMD))
        )
        cm.append(c)
        await msg.reply(cm)
    except Exception as result:
        _log.exception(f"Err in help")
        cm = await get_card_msg(f"ERR! [{get_time()}] help",err_card=True)
        await msg.reply(cm)

################################################################################





################################################################################

# 开机任务
@bot.on_startup
async def startup_task(b:Bot):
    try:
        global debug_ch
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