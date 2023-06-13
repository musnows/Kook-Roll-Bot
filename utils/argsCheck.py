import traceback
import json
import aiohttp

from khl import Message,Bot,ChannelPrivacyTypes
from khl.card import Card,CardMessage,Module,Element,Types
from typing import Union

from .files import config,_log

kook_base_url = "https://www.kookapp.cn"
kook_headers = {f'Authorization': f"Bot {config['token']}"}

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

async def upd_card(bot:Bot,msg_id: str,content,target_id='',
                    channel_type: Union[ChannelPrivacyTypes, str] = 'public'):
    """更新卡片消息"""
    content = json.dumps(content)
    data = {'msg_id': msg_id, 'content': content}
    if target_id != '':
        data['temp_target_id'] = target_id
    if channel_type == 'public' or channel_type == ChannelPrivacyTypes.GROUP:
        result = await bot.client.gate.request('POST', 'message/update', data=data)
    else:
        result = await bot.client.gate.request('POST', 'direct-message/update', data=data)
    return result


def is_positive_int(num:str):
    """检查传入的字符串是否为正整数"""
    if '.' in num or '-' in num:
        return False
    try:
        test = int(num)  # 尝试将其强转为int 
        return True
    except:
        return False
    
def is_positive_float(num:str):
    """检查传入的字符串是否为正的小数或整数"""
    if is_positive_int(num):
        return True
    try:
        test = float(num)  # 尝试将其强转
        return True
    except:
        return False
    
async def has_admin_rol(bot:Bot,user_id:str, guild_id:str):
    """判断用户是否拥有管理员角色权限"""
    if user_id in config['admin_user']:
        return True
    guild = await bot.client.fetch_guild(guild_id)
    user_roles = (await guild.fetch_user(user_id)).roles
    guild_roles = await (await bot.client.fetch_guild(guild_id)).fetch_roles()
    for i in guild_roles:  # 遍历服务器身分组
        if i.id in user_roles and i.has_permission(0):  # 查看当前遍历到的身分组是否在用户身分组内且是否有管理员权限
            return True
    if user_id == guild.master_id: # 由于腐竹可能没给自己上身分组，但是依旧拥有管理员权限
        return True
    return False

async def roll_args_check(bot:Bot,msg:Message,num:str,roll_day:str):
    """检查抽奖参数是否正确"""
    if not await has_admin_rol(bot,msg.author_id,msg.ctx.guild.id):
        _log.info(f"Au:{msg.author_id} | invalid user {roll_day}")
        await msg.reply(await get_card_msg("您必须拥有本频道管理员权限才能创建抽奖\n若您是服主，请给自己上一个拥有管理员权限的角色。"))
        return False
    if not is_positive_int(num):
        _log.info(f"Au:{msg.author_id} | invalid num {num}")
        await msg.reply(await get_card_msg("抽奖物品数量必须为正整数！"))
        return False
    if not is_positive_float(roll_day):
        _log.info(f"Au:{msg.author_id} | invalid time {roll_day}")
        await msg.reply(await get_card_msg("抽奖天数必须为正整数或正小数！"))
        return False
    
    return True


async def msg_view(msg_id: str):
    """获取消息详情，判断消息是否已经被删除;删除了的code是40000"""
    url = kook_base_url + "/api/v3/message/view"
    params = {"msg_id": msg_id}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=kook_headers) as response:
            ret1 = json.loads(await response.text())
            _log.debug(ret1)
            return ret1
