# encoding: utf-8
# 本文件仅供replit部署使用
# https://blog.musnow.top/posts/2556995516/
# 如果您是在云服务器/本地电脑部署本bot，请忽略此文件
# 在replit部署之后，请使用类似uptimerobot的服务来请求replit的url，否则5分钟不活动会休眠

import asyncio
from aiohttp import web,web_request
# 主文件导入bot
from rollbot import bot,get_time,_log,config

## 初始化web节点
routes = web.RouteTableDef()

## 请求routes的根节点
@routes.get('/')
async def hello_world(request:web_request.Request):
    return web.Response(body="bot alive")

## 添加routes到app中
app = web.Application()
app.add_routes(routes)

## webapp的绑定host和端口
HOST,PORT = '0.0.0.0',14725
if __name__ == '__main__':
    # 开机的时候打印一次时间，记录开启时间
    _log.info(f"[BOT] Start in replit {get_time()}")
    # 采用wh启动机器人，不需要用flask也能保证机器人活跃
    # websocket才需要执行webapp
    # 1.同时运行webapp+bot
    if config["ws"]:
        _log.info(f"[BOT] run bot & web_app at {HOST}:{PORT}")
        asyncio.get_event_loop().run_until_complete(
            asyncio.gather(web._run_app(app, host=HOST, port=PORT), bot.start()))
    # 2.只运行bot
    else:
        bot.run()