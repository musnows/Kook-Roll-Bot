import traceback

from khl import Message,Bot
from khl.card import Card,CardMessage,Module,Element,Types

from .files import config,_log

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
    if not has_admin_rol(bot,msg.author_id,msg.ctx.guild.id):
        _log.info(f"Au:{msg.author_id} | invalid user {roll_day}")
        await msg.reply(await get_card_msg("您必须拥有本频道管理员权限才能执行抽奖"))
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