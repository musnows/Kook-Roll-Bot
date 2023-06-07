# Kook-Roll-Bot

一个简单的抽奖机器人 (khl.py)

## 使用

* `/alive` 测试bot是否在线;
* `/rdh` 或 `/rdhelp` 为帮助命令;
* `/rd "奖品名字" 奖品个数 抽奖天数 @角色组` 按天数开奖;
* `/rh "奖品名字" 奖品个数 抽奖小时 @角色组` 按小时开奖;

抽奖命令示例

```
/rd "通行证一个" 2 2 @角色组1 @角色组2
```
如上命令将开启一个奖品为通行证，获奖人数为2，为期2天的抽奖，并且只有指定的角色组才可以参加抽奖。

### 功能截图

![roll](https://img.kookapp.cn/assets/2023-05/b3hDEXymQj0n709o.png)

![join](https://img.kookapp.cn/assets/2023-05/sAwON82qBb0jv039.png)


## 私有部署

保证python版本大于3.9，安装如下包
```
pip3 install -r requirements.txt
```

根据 [config-exp.json](./config.exp.json)，新建一个`config/config.json`文件，在里面写入相对应的字段。

* debug_ch 文字频道id，进kook设置-高级-开启开发者模式，右键文字频道-复制ID
* admin_user 管理员用户ID，同上方式开启开发者模式后，右键频道内用户头像-复制ID

配置完毕以后，就可以运行bot了

```
python3 main.py
```

### 一键部署到replit

注册[replit](https://replit.com/)，创建一个Python的repl，随后进入`shell`粘贴如下命令

```
git clone https://github.com/musnows/Kook-Roll-Bot.git && mv -b Kook-Roll-Bot/* ./ && mv -b Kook-Roll-Bot/.[^.]* ./  && rm -rf Kook-Roll-Bot && pip install -r requirements.txt
```

克隆完成，加载好nix文件后，同样是修改`config/config.json`的相关字段。随后点击上方绿色RUN按钮，即可运行bot。将右侧webview中出现的url填入kook的callback-url，即可上线机器人。

更多教程信息详见 [Kook-Ticket-Bot/wiki](https://github.com/musnows/Kook-Ticket-Bot/wiki)，基本步骤相同，repl保活工作二者都需要做。

若有不懂之处，可加入[帮助服务器](https://kook.top/gpbTwZ)咨询