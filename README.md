# Kook-LinkGuard-Bot

检查邀请链接是否为当前服务器的bot (khl.py)


## 使用

`/alive`命令，测试bot是否在线

邀请bot进入频道后，选定一个文字频道作为bot的日志频道。

在频道内发送`/setch`，bot将此频道设置为日志频道，并开启对整个服务器的邀请链接监控（必须执行此命令，否则bot不会工作）

更多命令详见 `/lgh` 帮助命令

```python
text+= "「/alive」看看bot是否在线\n"
text+= "「/setch」将本频道设置为日志频道 (执行后才会开始监看)\n"
text+= "「/ignch」在监看中忽略本频道\n"
text+= "「/clear」清除本服务器的设置\n"
```

### 功能截图

![log_cm](https://img.kookapp.cn/assets/2023-02/XnNCA8XoZl0jl0aa.png)

![msg_delete](https://img.kookapp.cn/assets/2023-02/ycJ3MJHzSJ0h603w.png)


## 私有部署

保证python版本大于3.9，安装如下包
```
pip3 install -r requirements.txt
```

根据`config/config-exp.json`，新建一个`config/config.json`文件，在里面写入相对应的字段。

* debug_ch 文字频道id，进kook设置-高级-开启开发者模式，右键频道复制
* sqlite_enable 是否使用sqlite3来存放违规的邀请链接。如果使用默认的json策略，`可能`会因为json字符串过长而写入磁盘失败。如果你的服务器所安装python支持sqlite3，建议启用。

配置完毕以后，就可以运行bot了

```
python3 main.py
```

### 一键部署到replit

注册[replit](https://replit.com/)，创建一个Python的repl，随后进入`shell`粘贴如下命令

```
git clone https://github.com/musnows/Kook-LinkGuard-Bot.git && mv -b Kook-LinkGuard-Bot/* ./ && mv -b Kook-LinkGuard-Bot/.[^.]* ./  && rm -rf Kook-LinkGuard-Bot && pip install -r requirements.txt
```

克隆完成，加载好nix文件后，同样是修改`config/config.json`的相字段。随后点击上方绿色RUN按钮，即可运行bot。将右侧webview中出现的url填入kook的callback-url，即可上线机器人。

更多教程信息详见 [Kook-Ticket-Bot/wiki](https://github.com/musnows/Kook-Ticket-Bot/wiki)，基本步骤相同，repl保活工作二者都需要做。

若有不懂之处，可加入[帮助服务器](https://kook.top/gpbTwZ)咨询