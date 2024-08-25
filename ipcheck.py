import os
import requests
import re
import time
import smtplib
import email
import email.utils
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
 
class ENV:
  def __init__(self):
 
    if(os.environ.get("FROM_EMAIL") == None):
      raise Exception("请配置发送邮箱账户！")
    if(os.environ.get("FROM_EMAIL_PASSWORD") == None):
      raise Exception("请配置发送邮箱授权密码！")
 
    api_str = "https://4.ipw.cn" if os.environ.get("API") == None else os.environ.get("API")
    api_list = api_str.split(",")
    # 对不符合规范添加 http请求头， 使 api 符合协议
    for i in range(len(api_list)):
      match = re.match("http", api_list[i])
      if(match == None):
        api_list[i] = "http://" + api_list[i]
 
    self.api_list = api_list
    self.from_email = os.environ.get("FROM_EMAIL")
    self.from_email_password = os.environ.get("FROM_EMAIL_PASSWORD")
    self.to_email = self.from_email if os.environ.get("TO_EMAIL")  == None else os.environ.get("TO_EMAIL")
    self.smtp_server = "smtpdm.aliyun.com" if os.environ.get("SMTP_SERVER") == None else os.environ.get("SMTP_SERVER")
    self.smtp_port = 465 if os.environ.get("SMTP_PORT") == None else os.environ.get("SMTP_PORT")
    self.interval = 10 if os.environ.get("INTERVAL") == None else os.environ.get("INTERVAL")
 
def check_ip(api_list):
  headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36"}
 
  for api in api_list:
    html = requests.get(api, headers=headers)
    if(html.status_code == 200):
      match = re.match(r'^((2((5[0-5])|([0-4]\d)))|([0-1]?\d{1,2}))(\.((2((5[0-5])|([0-4]\d)))|([0-1]?\d{1,2}))){3}$',html.text)
      if match != None:
        currentIp = match.string
        return currentIp
  print("所有获取公网的 api 均不可用")
 
def sendmail_template(oldIp, currentIp, env):
        # username，通过控制台创建的发信地址
    username = env.from_email
    # password，通过控制台创建的SMTP密码
    password = env.from_email_password

    # 显示的To收信地址
    rcptto = list(env.to_email.split(","))
    # # 显示的Cc收信地址
    rcptcc = []
    # # Bcc收信地址，密送人不会显示在邮件上，但可以收到邮件
    rcptbcc = []
    # 全部收信地址，包含抄送地址，单次发送不能超过60人
    receivers = rcptto  + rcptcc + rcptbcc

    # 构建alternative结构
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header('IP 地址变动提醒')
    msg['From'] = formataddr(["家里电脑", username])  # 昵称+发信地址(或代发)
    # list转为字符串
    msg['To'] = ",".join(rcptto)
    msg['Cc'] = ",".join(rcptcc)
    # msg['Reply-to'] = replyto  #用于接收回复邮件，需要收信方支持标准协议
    # msg['Return-Path'] = 'test@example.net' #用于接收退信邮件，需要收信方支持标准协议
    msg['Message-id'] = email.utils.make_msgid() # message-id 用于唯一地标识每一封邮件，其格式需要遵循RFC 5322标准，通常如 <uniquestring@example.com>，其中uniquestring是邮件服务器生成的唯一标识，可能包含时间戳、随机数等信息。
    msg['Date'] = email.utils.formatdate()

    template = """
    <p>Kinsue ，您的 IP 地址改变啦！</p>
    <p>原 <b>IP</b> 地址：<b>{0}</b></p>
    <p>现 <b>IP</b> 地址：<b>{1}</b></p>
    """
    html_msg = template.format(oldIp, currentIp)

    # 构建alternative的text/html部分
    texthtml = MIMEText(html_msg, _subtype='html', _charset='UTF-8')
    msg.attach(texthtml)

    # 发送邮件
    try:

        # 发信服务器
        smtp_server = env.smtp_server
        # SMTP普通端口为25或465
        smtp_port = int(env.smtp_port) if env.smtp_port != None else 465
        if smtp_port == 25 or smtp_port == 80:
          client = smtplib.SMTP(smtp_server, smtp_port)
        else:
          client = smtplib.SMTP_SSL(smtp_server, 465)
        # 开启DEBUG模式
        client.set_debuglevel(1)
        # 发件人和认证地址必须一致
        client.login(username, password)
        # 备注：若想取到DATA命令返回值,可参考smtplib的sendmail封装方法:
        # 使用SMTP.mail/SMTP.rcpt/SMTP.data方法
        # print(receivers)
        client.sendmail(username, receivers, msg.as_string())  # 支持多个收件人，具体数量参考规格清单
        client.quit()
        print('邮件发送成功！')
    except smtplib.SMTPConnectError as e:
        print('邮件发送失败，连接失败:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPAuthenticationError as e:
        print('邮件发送失败，认证错误:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPSenderRefused as e:
        print('邮件发送失败，发件人被拒绝:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPRecipientsRefused as e:
        print('邮件发送失败，收件人被拒绝:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPDataError as e:
        print('邮件发送失败，数据接收拒绝:', e.smtp_code, e.smtp_error)
    except smtplib.SMTPException as e:
        print('邮件发送失败, ', str(e))
    except Exception as e:
        print('邮件发送异常, ', str(e))
 
def check_job(env: ENV):

  # 如果根目录存在 PublicIP.txt 文件, 读取文件中的 IP 地址,
  if not os.path.exists("./ip.txt"):
    with open("./ip.txt", "w") as f:
      f.write("127.0.0.1")

  with open("./ip.txt", "r") as f:
    os.environ["PublicIP"] = f.readline()

  PreIP = str(os.environ["PublicIP"])
  CurIP = check_ip(env.api_list)
  print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + "---oldIp：" + PreIP + "，currentIp：" + CurIP)

  if(PreIP != CurIP):
    print("Ip 地址发生改变")
    sendmail_template(PreIP, CurIP, env)
    os.environ["PublicIP"] = CurIP
    with open("./ip.txt", "w") as f:
      f.write(CurIP)

if __name__ == '__main__':

  env = ENV()
  while True:
    check_job(env)
    time.sleep(60 * int(env.interval))

