# 渠道配置指南

本文档详细说明 mcp-push 支持的所有通知渠道的配置方法。

## 配置说明

- 所有配置通过**环境变量**设置
- 未配置的渠道会被自动跳过
- 支持同时配置多个渠道进行并发推送

---

## Bark

iOS 通知推送服务。

### 环境变量

```bash
# 必填：设备码或服务器地址
export BARK_PUSH="https://api.day.app/DxHcxxxxxRxxxxxxcm/"
# 或仅填写设备码
export BARK_PUSH="DxHcxxxxxRxxxxxxcm"

# 可选配置
export BARK_ARCHIVE=""        # 推送是否存档
export BARK_GROUP="QingLong"  # 推送分组
export BARK_SOUND="choo"      # 推送声音
export BARK_ICON="https://qn.whyour.cn/logo.png"  # 推送图标（需 iOS 15+）
export BARK_LEVEL="active"    # 推送时效性
export BARK_URL=""            # 推送跳转 URL
```

### 获取方式

1. App Store 下载 Bark
2. 打开应用获取设备码

### 常见问题

**Q: 推送没有声音？**
A: 检查 `BARK_SOUND` 是否配置，可在 App 内查看可用铃声列表

**Q: 推送无法点击跳转？**
A: 设置 `BARK_URL` 为目标网址

---

## 钉钉机器人 (DingTalk)

钉钉群机器人推送。

### 环境变量

```bash
# 必填
export DD_BOT_TOKEN="your-access-token"
export DD_BOT_SECRET="your-secret"
```

### 获取方式

1. 钉钉群 → 设置 → 智能群助手 → 添加机器人 → 自定义
2. 安全设置选择"加签"
3. 复制 `access_token` 和 `secret`

### 示例

```bash
# URL 示例: https://oapi.dingtalk.com/robot/send?access_token=XXX
# DD_BOT_TOKEN 填写 XXX 部分

export DD_BOT_TOKEN="e22e31af9fb4e663955e89644a2dc4929acd25a8c2263c3b2b8669df9ff26dd9"
export DD_BOT_SECRET="SECaa82597eb29779c23651e10ee895b2200a992d79f946e20f1a41e5d9c3ca1bc2"
```

### 常见问题

**Q: 提示"签名不匹配"？**
A: 检查 `DD_BOT_SECRET` 是否正确，必须是"加签"方式的 secret

**Q: 提示"token 不存在"？**
A: 检查 `DD_BOT_TOKEN` 是否完整复制

---

## 飞书机器人 (Feishu/Lark)

飞书群机器人推送。

### 环境变量

```bash
export FSKEY="your-webhook-key"
```

### 获取方式

1. 飞书群 → 设置 → 群机器人 → 添加机器人 → 自定义机器人
2. 复制 webhook 地址中的 key 部分

### 示例

```bash
# URL 示例: https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# FSKEY 填写完整的 key

export FSKEY="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

---

## Telegram Bot

Telegram 机器人推送。

### 环境变量

```bash
# 必填
export TG_BOT_TOKEN="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
export TG_USER_ID="987654321"

# 可选：代理设置
export TG_PROXY_HOST="127.0.0.1"
export TG_PROXY_PORT="1080"
export TG_PROXY_AUTH=""  # 认证信息（如需要）

# 可选：自定义 API 地址
export TG_API_HOST="https://api.telegram.org"
```

### 获取方式

1. **获取 Bot Token**:
   - 在 Telegram 搜索 `@BotFather`
   - 发送 `/newbot` 创建机器人
   - 复制返回的 Token

2. **获取 User ID**:
   - 在 Telegram 搜索 `@userinfobot`
   - 发送任意消息获取 ID

### 常见问题

**Q: 机器人无法发送消息？**
A: 必须先主动给机器人发送一条消息

**Q: 国内网络无法访问？**
A: 配置代理或使用自建 API 反向代理

---

## 企业微信机器人 (WeCom Bot)

企业微信群机器人推送。

### 环境变量

```bash
export QYWX_KEY="693a91f6-7xxx-4bc4-97a0-0ec2sifa5aaa"

# 可选：代理地址
export QYWX_ORIGIN="https://qyapi.weixin.qq.com"
```

### 获取方式

1. 企业微信群 → 右键 → 添加群机器人
2. 复制 Webhook 地址中的 key 参数

### 示例

```bash
# URL 示例: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=693a91f6-xxxx
# QYWX_KEY 填写 key 后面的部分

export QYWX_KEY="693a91f6-7xxx-4bc4-97a0-0ec2sifa5aaa"
```

---

## 企业微信应用 (WeCom App)

企业微信应用消息推送。

### 环境变量

```bash
# 格式: corpid,corpsecret,touser,agentid[,media_id]
export QYWX_AM="wwcff56746d9adwers,B-791548lnzXBE,zhangsan|lisi,1000001,MEDIA_ID"

# 可选：代理地址
export QYWX_ORIGIN="https://qyapi.weixin.qq.com"
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| corpid | 企业 ID | `wwcff56746d9adwers` |
| corpsecret | 应用 Secret | `B-791548lnzXBE...` |
| touser | 接收人 ID，多个用 `|` 分隔，`@all` 表示全员 | `zhangsan|lisi` 或 `@all` |
| agentid | 应用 AgentID | `1000001` |
| media_id | 素材库图片 ID（可选）| `MEDIA_ID` |

### 消息类型

- **不填 media_id**: 纯文本消息
- **media_id = "0"**: 文本卡片消息
- **media_id = "1"**: 纯文本消息
- **media_id = 其他**: 图文消息（mpnews）

### 获取方式

1. 企业微信管理后台 → 我的企业 → 企业信息 → 企业 ID (`corpid`)
2. 应用管理 → 创建应用 → 获取 AgentID 和 Secret
3. 通讯录 → 成员 → 查看成员 ID

---

## SMTP 邮件

通过 SMTP 发送邮件通知。

### 环境变量 (JavaScript)

```bash
export SMTP_SERVICE="Gmail"  # 邮箱服务名称
export SMTP_EMAIL="notify@example.com"
export SMTP_PASSWORD="your-password"
export SMTP_NAME="AI Agent"
export SMTP_TO="recipient@example.com"  # 可选，默认发给自己
```

### 环境变量 (Python)

```bash
export SMTP_SERVER="smtp.exmail.qq.com:465"
export SMTP_SSL="true"
export SMTP_EMAIL="notify@example.com"
export SMTP_PASSWORD="your-password"
export SMTP_NAME="AI Agent"
```

### 常见服务配置

| 服务商 | SMTP_SERVICE (JS) | SMTP_SERVER (Python) | 端口 | SSL |
|--------|-------------------|----------------------|------|-----|
| Gmail | `Gmail` | `smtp.gmail.com:465` | 465 | true |
| QQ 邮箱 | `QQ` | `smtp.qq.com:465` | 465 | true |
| 163 邮箱 | `163` | `smtp.163.com:465` | 465 | true |
| 腾讯企业邮 | - | `smtp.exmail.qq.com:465` | 465 | true |

### 常见问题

**Q: 提示"认证失败"？**
A: 部分邮箱需要使用"应用专用密码"，而非登录密码

**Q: Gmail 无法发送？**
A: 需开启"允许不够安全的应用访问"或使用应用专用密码

---

## Server酱 (ServerChan)

微信推送服务。

### 环境变量

```bash
export PUSH_KEY="your-sendkey"
```

### 获取方式

1. 访问 [sct.ftqq.com](https://sct.ftqq.com)
2. 微信扫码登录
3. 复制 SendKey

### 支持版本

- 旧版: `PUSH_KEY` 格式为 `SCU` 开头
- Turbo 版: `PUSH_KEY` 格式为 `sctp` 开头

---

## PushPlus

多渠道推送服务。

### 环境变量

```bash
# 必填
export PUSH_PLUS_TOKEN="your-token"

# 可选
export PUSH_PLUS_USER=""              # 群组编码（一对多推送）
export PUSH_PLUS_TEMPLATE="html"      # 发送模板: html, txt, json, markdown
export PUSH_PLUS_CHANNEL="wechat"     # 发送渠道: wechat, webhook, cp, mail, sms
export PUSH_PLUS_WEBHOOK=""           # webhook 编码
export PUSH_PLUS_CALLBACKURL=""       # 回调地址
export PUSH_PLUS_TO=""                # 好友令牌或企业微信用户 ID
```

### 获取方式

1. 访问 [pushplus.plus](https://www.pushplus.plus)
2. 微信扫码登录
3. 复制 Token

---

## PushDeer

跨平台推送服务。

### 环境变量

```bash
export DEER_KEY="your-pushkey"
export DEER_URL="https://api2.pushdeer.com"  # 可选，自建服务器地址
```

### 获取方式

1. 下载 PushDeer 应用
2. 注册账号
3. 获取 PushKey

---

## Gotify

开源自建推送服务。

### 环境变量

```bash
export GOTIFY_URL="https://push.example.com:8080"
export GOTIFY_TOKEN="your-token"
export GOTIFY_PRIORITY=5  # 优先级: 0-10
```

### 部署方式

```bash
docker run -d --name gotify \
  -p 8080:80 \
  -v /var/gotify/data:/app/data \
  gotify/server
```

---

## Ntfy

开源推送服务。

### 环境变量

```bash
export NTFY_URL="https://ntfy.sh"  # 可选，默认公共服务
export NTFY_TOPIC="your-topic"
export NTFY_PRIORITY="3"           # 1-5
export NTFY_TOKEN=""               # 可选
export NTFY_USERNAME=""            # 可选
export NTFY_PASSWORD=""            # 可选
export NTFY_ACTIONS=""             # 可选
```

### 使用方式

1. 访问 [ntfy.sh](https://ntfy.sh)
2. 创建自定义主题（topic）
3. 在手机安装 ntfy 应用订阅主题

---

## Go-cqhttp

QQ 机器人推送（基于 go-cqhttp）。

### 环境变量

```bash
# 个人消息
export GOBOT_URL="http://127.0.0.1:5700/send_private_msg"
export GOBOT_QQ="user_id=123456789"

# 群消息
export GOBOT_URL="http://127.0.0.1:5700/send_group_msg"
export GOBOT_QQ="group_id=987654321"

# 可选
export GOBOT_TOKEN="your-access-token"
```

### 部署方式

参考 [go-cqhttp 文档](https://docs.go-cqhttp.org/)

---

## Chronocat

QQ 机器人推送（基于 Chronocat Red 协议）。

### 环境变量

```bash
export CHRONOCAT_URL="http://127.0.0.1:16530"
export CHRONOCAT_TOKEN="your-token"
export CHRONOCAT_QQ="user_id=123456789;group_id=987654321"
```

### 部署方式

参考 [Chronocat 文档](https://chronocat.vercel.app/install/docker/official/)

---

## Qmsg 酱

QQ 消息推送服务。

### 环境变量

```bash
export QMSG_KEY="your-key"
export QMSG_TYPE="send"  # send=私聊, group=群聊
```

### 获取方式

访问 [qmsg.zendee.cn](https://qmsg.zendee.cn)

---

## 智能微秘书 (Aibotk)

微信机器人推送。

### 环境变量

```bash
export AIBOTK_KEY="your-apikey"
export AIBOTK_TYPE="room"      # room=群聊, contact=私聊
export AIBOTK_NAME="群名称"    # 或好友昵称
```

### 获取方式

访问 [wechat.aibotk.com](http://wechat.aibotk.com)

---

## iGot

聚合推送服务。

### 环境变量

```bash
export IGOT_PUSH_KEY="your-push-key"
```

### 获取方式

参考 [wahao.github.io/Bark-MP-helper](https://wahao.github.io/Bark-MP-helper)

---

## PushMe

自建推送服务。

### 环境变量

```bash
export PUSHME_KEY="your-key"
export PUSHME_URL="https://push.i-i.me"  # 可选
```

---

## Synology Chat

群晖 Chat 推送。

### 环境变量

```bash
export CHAT_URL="http://your-nas-ip:port/webapi/***token="
export CHAT_TOKEN="your-token"
```

---

## 微加机器人 (WeBot)

微信机器人推送。

### 环境变量

```bash
export WE_PLUS_BOT_TOKEN="your-token"
export WE_PLUS_BOT_RECEIVER=""    # 可选
export WE_PLUS_BOT_VERSION="pro"  # pro=专业版, personal=个人版
```

---

## WxPusher

微信推送服务。

### 环境变量

```bash
export WXPUSHER_APP_TOKEN="your-app-token"
export WXPUSHER_TOPIC_IDS="123;456"  # 主题 ID，分号分隔
export WXPUSHER_UIDS="UID_xxx;UID_yyy"  # 用户 ID，分号分隔
```

### 获取方式

1. 访问 [wxpusher.zjiecode.com](https://wxpusher.zjiecode.com/admin/)
2. 注册并创建应用
3. 获取 appToken

### 注意事项

- `WXPUSHER_TOPIC_IDS` 和 `WXPUSHER_UIDS` 至少配置一个

---

## 自定义 Webhook

通用 Webhook 推送。

### 环境变量

```bash
export WEBHOOK_URL="https://api.example.com/notify?title=\$title&content=\$content"
export WEBHOOK_METHOD="POST"
export WEBHOOK_CONTENT_TYPE="application/json"
export WEBHOOK_HEADERS="Authorization: Bearer token
Content-Type: application/json"
export WEBHOOK_BODY="title: \$title
content: \$content"
```

### 变量替换

- `$title`: 消息标题
- `$content`: 消息内容

### 支持的 Content-Type

- `text/plain`
- `application/json`
- `application/x-www-form-urlencoded`
- `multipart/form-data`

---

## 通用配置

### 一言开关

```bash
export HITOKOTO="false"  # 关闭一言随机句子
```

### 跳过推送

```bash
# 换行分隔的标题列表
export SKIP_PUSH_TITLE="测试通知
调试消息"
```

---

## 配置检查清单

在生产环境使用前，请检查：

- [ ] 所有敏感信息（Token、Secret）已妥善保管
- [ ] 测试通知成功发送到所有配置渠道
- [ ] 网络连通性（特别是 Telegram 等国外服务）
- [ ] 推送频率未超过渠道限制
- [ ] 错误日志监控已配置

---

## 故障排查

### 通用步骤

1. **检查环境变量**: `env | grep -E "DD_BOT|TG_BOT|QYWX"`
2. **查看日志输出**: 每个渠道会打印启动和结果信息
3. **测试单个渠道**: 使用单渠道测试函数
4. **网络检查**: `curl -I https://api.telegram.org`

### 常见错误

| 错误信息 | 可能原因 | 解决方法 |
|---------|---------|---------|
| `Connection timeout` | 网络不通 | 检查防火墙/代理配置 |
| `401 Unauthorized` | Token 错误 | 检查环境变量是否正确 |
| `签名不匹配` | Secret 错误 | 重新复制钉钉 Secret |
| `推送失败` | 渠道配置错误 | 参考官方文档检查参数 |

---

## 推荐配置方案

### 方案 1: 个人开发者

```bash
export BARK_PUSH="your-device-code"
export TG_BOT_TOKEN="your-token"
export TG_USER_ID="your-id"
```

### 方案 2: 团队协作

```bash
export DD_BOT_TOKEN="team-dingtalk-token"
export DD_BOT_SECRET="team-dingtalk-secret"
export QYWX_KEY="team-wecom-key"
export SMTP_SERVER="smtp.company.com:465"
export SMTP_EMAIL="notify@company.com"
```

### 方案 3: 高可用

```bash
# 主渠道
export DD_BOT_TOKEN="primary-token"
export DD_BOT_SECRET="primary-secret"

# 备用渠道
export TG_BOT_TOKEN="backup-token"
export TG_USER_ID="backup-id"
export SMTP_SERVER="backup-smtp:465"
```
