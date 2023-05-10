import aiohttp
import asyncio
import traceback
import os
import copy
import random

from khl import Bot,Cert, Message,requester,Event,EventTypes
from khl.card import Card,CardMessage,Types,Module,Element
from aiohttp import client_exceptions
from datetime import datetime,timedelta

from utils.files import config,RollLog,StartTime,write_roll_log
from utils.myLog import get_time,get_time_str_from_stamp,log_msg,_log
from utils.argsCheck import get_card_msg,roll_args_check,upd_card

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

async def help_card():
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
    text+= " 1.奖品名字必须带上英文双引号\n 2.角色组可以不指定，即所有人可参加\n"
    text+= " 3.抽奖天数/小时可以设置为小数，比如半天设置为0.5\n 4.请勿在抽奖中@用户，否则视作全体成员抽奖\n"
    # 小字
    sub_text = f"开机于：{StartTime}  |  开源仓库：[Github](https://github.com/musnows/Kook-Roll-Bot)\n"
    sub_text+= "如有问题，请加入帮助频道咨询：[邀请链接](https://kook.top/gpbTwZ)"
    return await get_card_msg(text,sub_text,header_text="抽奖菈 帮助命令")

# 帮助命令
@bot.command(name='rdh',aliases=['rdhelp'],case_sensitive=False)
async def help_cmd(msg:Message,*arg):
    try:
        log_msg(msg)
        await msg.reply(await help_card())
        _log.info(f"Au:{msg.author_id} | help reply")
    except Exception as result:
        _log.exception(f"Err in help")
        await msg.reply(await get_card_msg(f"ERR! [{get_time()}] help",err_card=True))

@bot.on_message()
async def at_help_cmd(msg:Message):
    """at机器时发送帮助命令"""
    try:
        # kook系统通知，忽略
        if msg.author_id == "3900775823": return
        # 要求只是存粹at机器人的时候才回复，字数大概为20字
        elif len(msg.content) >= 22: return
        # 获取机器人的用户对象
        cur_bot = await bot.client.fetch_me()
        if f"(met){cur_bot.id}(met)" in msg.content:
            log_msg(msg)
            await msg.reply(await help_card())
            _log.info(f"Au:{msg.author_id} | at_help reply")
    except:
        _log.exception(f"Err in at_help")

################################################################################

async def get_rid_list(arg):
    """通过参数元组获取角色id列表（int列表）"""
    temp_list = []
    for s in arg:
        if "met" in s: # 全体成员(met)all(met)或者在线成员(met)here(met)，或者at的是用户
            continue
        temp_list.append(int(s.replace("(rol)","")))
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
    text = "给本条消息添加表情回应，即可参与抽奖！\n"
    text+= f"当前参与人数：{join_count}" # 参与人数
    c.append(Module.Context(Element.Text(text,Types.Text.KMD)))
    return CardMessage(c)

async def roll_start_log(guild_id:str,channel_id:str,msg_id:str,user_id:str,
                         item_name:str,item_num:int,roll_sec:float,rid_list=[]):
    """记录开启时的抽奖信息"""
    global RollLog
    if guild_id not in RollLog['data']:
        RollLog['data'][guild_id] = {}

    cur_time = datetime.now().timestamp()
    RollLog['data'][guild_id][msg_id] = {
        "start_time":cur_time,
        "end_time": cur_time + roll_sec,
        "item":{
            "name":item_name,
            "num":item_num
        },
        "user_id": user_id,
        "channel_id":channel_id,
        "rid_list":rid_list,
        "join":{
            "count":-1,
            "reward_user":[]
        }
    }
    RollLog['msg'][msg_id] = {"user":[],"guild_id":guild_id} # 加入抽奖用户的list
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
        await roll_start_log(msg.ctx.guild.id,msg.ctx.channel.id,
                            send_msg['msg_id'],msg.author_id,name,int(num),roll_time,rid_list)
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
        await roll_start_log(msg.ctx.guild.id,msg.ctx.channel.id,
                             send_msg['msg_id'],msg.author_id,name,int(num),roll_time,rid_list)
        _log.info(f"Au:{msg.author_id} | rh success")
    except:
        _log.exception(f"Err in rd | Au:{msg.author_id}")
        cm = await get_card_msg(f"ERR! [{get_time()}] rd",err_card=True)
        await msg.reply(cm)


@bot.on_event(EventTypes.ADDED_REACTION)
async def emoji_reaction_event(b:Bot,e:Event):
    """监测消息的表情回应"""
    try:
        global RollLog
        msg_id = e.body['msg_id'] # 消息ID
        user_id = e.body['user_id'] # 用户id
        # 消息id不在，不是抽奖信息，直接退出
        if msg_id not in RollLog['msg']: return
        ch = await bot.client.fetch_public_channel(e.body['channel_id'])
        text = f"(met){user_id}(met)"
        # 判断用户id，在通知用户后退出
        if user_id in RollLog['msg'][msg_id]['user']:
            cm = await get_card_msg(f"{text}\n您已成功参加了此次抽奖，请勿多次操作！")
            return await ch.send(cm,temp_target_id=user_id)

        # 此次抽奖的信息
        guild_id = RollLog['msg'][msg_id]['guild_id']
        rinfo = RollLog['data'][guild_id][msg_id] 
        # 获取用户角色组，判断是否在info中
        if rinfo['rid_list']: # list 不为空
            role_flag = False
            guild_user = await (await bot.client.fetch_guild(guild_id)).fetch_user(user_id)
            for r in guild_user.roles:
                if r in rinfo['rid_list']:
                    role_flag = True
                    break # 跳出
            # 如果为假，代表没有这个权限，不给参加
            if not role_flag:
                _log.info(f"[roll] Au:{user_id} | Msg:{msg_id} | not in roles")
                cm = await get_card_msg(f"{text}\n抱歉，您没有参与此次抽奖的权限！")
                return await ch.send(cm,temp_target_id=user_id)

        # 用户id不在，添加用户并通知
        RollLog['msg'][msg_id]['user'].append(user_id) 
        emoji = e.body['emoji']['id'] # 1通用emoji
        str_index = e.body['emoji']['id'].find('/')
        # 2找到了/，且没有第二个/，说明是服务器表情
        if str_index != -1 and e.body['emoji']['id'].find('/',str_index+1) == -1:
            emoji = f"(emj){e.body['emoji']['name']}(emj)[{e.body['emoji']['id']}]"
        elif str_index != -1: # 3用户表情
            emoji = f"`{e.body['emoji']['id']}`"
        text+= f"\n「添加回应 {emoji}」抽奖参与成功！"
        cm = await get_card_msg(text)
        await ch.send(cm,temp_target_id=user_id) # 发送信息
        # 重新获取消息卡片并更新
        time_diff = rinfo['end_time'] - datetime.now().timestamp()
        # 获取卡片
        cm = await roll_card_msg(rinfo['user_id'],
                                 rinfo['item']['name'],
                                 rinfo['item']['num'],
                                 time_diff,rinfo['rid_list'],
                                 len(RollLog['msg'][msg_id]['user']))
        await upd_card(bot,msg_id,cm) # 更新卡片
        _log.info(f"[roll] Au:{user_id} | Msg:{msg_id} | join")
    except:
        _log.exception(f"Err in roll event | {e.body}")


@bot.task.add_interval(seconds=57)
async def roll_check_task():
    """检查抽奖是否结束的task"""
    msg_id = "none"
    try:
        _log.info("[BOT.TASK] roll check begin")
        global RollLog
        RollLogTemp = copy.deepcopy(RollLog)
        for msg_id in RollLogTemp['msg']:
            guild_id = RollLogTemp['msg'][msg_id]['guild_id'] # 服务器id
            rinfo = RollLogTemp['data'][guild_id][msg_id] 
            # 1.已经结束了，重大err
            if rinfo['join']['count'] != -1: 
                del RollLog['msg'][msg_id] # 只删除消息id，不修改info
                _log.critical(f"G:{guild_id} | Msg:{msg_id} | roll already end!")
                continue
            cur_time = datetime.now().timestamp()
            # 2.没有超过结束时间，继续
            if cur_time < rinfo['end_time']: 
                continue 
            # 3.抽奖时间到了,结束抽奖
            vnum = rinfo['item']['num'] # 奖品数量
            join_sz = len(RollLogTemp['msg'][msg_id]['user']) # 参与人数
            RollLog['data'][guild_id][msg_id]['join'] = join_sz
            #   人数大于奖品数量
            ran = []
            if join_sz > vnum:
                ran = random.sample(range(0, join_sz), vnum)  # 生成n个随机数
            else:  # 生成一个从0到len-1的列表 如果只有一个用户，生成的是[0]
                ran = list(range(join_sz))
            #   开始遍历
            text = "恭喜 "
            for index in ran:
                user_id = RollLogTemp['msg'][msg_id]['user'][index]
                user_str = f"(met){user_id}(met) "
                text += user_str
                RollLog['data'][guild_id][msg_id]['join']['reward_user'].append(user_id)
            text += "获得了本次奖品！"

            #  删除抽奖消息
            del RollLog['msg'][msg_id]
            # 结束，发送信息
            cm = await get_card_msg(text,header_text=f"开奖菈！奖品「{rinfo['item']['name']}」")
            ch = await bot.client.fetch_public_channel(rinfo['channel_id']) 
            await ch.send(cm)
            _log.info(f"G:{guild_id} | Msg:{msg_id} | roll end success")

        _log.info("[BOT.TASK] roll check  end")
    except:
        _log.exception(f"Err in roll check | {msg_id}")

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
# 定时写文件
@bot.task.add_interval(minutes=4)
async def save_log_file_task():
    await write_roll_log(log_info="[BOT.TASK]")

# 开机 （如果是主文件就开机）
if __name__ == '__main__':
    # 开机的时候打印一次时间，记录开启时间
    _log.info(f"[BOT] Start at {get_time()}")
    bot.run()