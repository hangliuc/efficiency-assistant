# app/core/notifier.py
import requests
import logging

class WeComNotifier:
    def __init__(self, config):
        self.webhook_url = config['url']
        self.mention_list = config.get('mention_list', []) # 获取需要@的人
        self.headers = {"Content-Type": "application/json"}

    def send_text(self, content):
        """
        发送纯文本消息 (普通微信可见)
        """
        # 如果有配置 @手机号，拼接到文本末尾
        if self.mention_list:
             # 企微机器人 text 模式下，@需要用手机号列表
             # 这里我们简单粗暴地把内容拼在一起
             pass 

        data = {
            "msgtype": "text",
            "text": {
                "content": content,
                "mentioned_mobile_list": self.mention_list # 真正实现 @提醒
            }
        }
        
        try:
            resp = requests.post(self.webhook_url, json=data, headers=self.headers, timeout=10)
            result = resp.json()
            if result.get('errcode') == 0:
                logging.info("企业微信推送成功")
            else:
                logging.error(f"推送失败: {result}")
        except Exception as e:
            logging.error(f"网络异常: {e}")