# app/core/notifier.py
import requests
import logging

class WeComAppNotifier:
    def __init__(self, config):
        """
        初始化应用通知器
        config: 包含 corpid, corpsecret, agentid, touser
        """
        self.corpid = config['corpid']
        self.corpsecret = config['corpsecret']
        self.agentid = config['agentid']
        self.touser = config.get('touser', '@all')
        
    def _get_token(self):
        """获取 Access Token"""
        url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}"
        try:
            resp = requests.get(url, timeout=10)
            data = resp.json()
            if data.get('errcode') == 0:
                return data.get('access_token')
            else:
                logging.error(f"获取 Token 失败: {data}")
                return None
        except Exception as e:
            logging.error(f"获取 Token 网络异常: {e}")
            return None

    def send_markdown(self, content):
        """发送 Markdown 消息"""
        token = self._get_token()
        if not token:
            logging.error("无法发送消息：Token 获取失败")
            return

        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        
        payload = {
            "touser": self.touser,
            "msgtype": "markdown",
            "agentid": self.agentid,
            "markdown": {
                "content": content
            },
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }

        try:
            resp = requests.post(send_url, json=payload, timeout=10)
            data = resp.json()
            if data.get('errcode') == 0:
                logging.info("企业微信(应用)推送成功")
            else:
                logging.error(f"推送失败: {data}")
        except Exception as e:
            logging.error(f"推送网络异常: {e}")