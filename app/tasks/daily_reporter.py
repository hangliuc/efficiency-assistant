# app/tasks/daily_reporter.py
import requests
import logging
import time
from datetime import datetime
from chinese_calendar import is_workday

class DailyReporter:
    def __init__(self, config, notifier):
        """
        :param config: 全局配置
        :param notifier: 已经初始化好的 WeComNotifier 对象
        """
        self.config = config
        self.notifier = notifier
        self.base_url = "http://qt.gtimg.cn/q="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _is_trading_day(self):
        """
        判断是否为A股交易日 
        逻辑: 必须是 '法定工作日' 且 '必须是周一到周五'
        (因为A股在调休上班的周末也是不开市的)
        """
        today = datetime.now().date()
        
        # 1. 基础判断: 如果是法定节假日(春节/国庆等)或者是普通周末 -> is_workday 为 False
        if not is_workday(today):
            logging.info("😴 今天是法定节假日或休息日，A股休市")
            return False
            
        # 2. 调休过滤: 如果是法定工作日(is_workday=True)，但它是周六或周日 -> A股依然休市
        if today.weekday() >= 5:
            logging.info("😴 今天是调休上班日(周末)，A股休市")
            return False
            
        # 既是工作日，又是周一到周五 -> 开盘
        return True

    def _get_price(self, symbol):
        """内部方法：获取价格"""
        try:
            url = f"{self.base_url}{symbol}"
            resp = requests.get(url, headers=self.headers, timeout=5)
            try:
                content = resp.content.decode('gbk').strip()
            except UnicodeDecodeError:
                content = resp.text.strip()

            if '="' not in content: return None, 0.0
            data_str = content.split('="')[1].split('"')[0]
            if not data_str: return None, 0.0
            fields = data_str.split("~")
            if len(fields) < 10: return None, 0.0

            current_price = float(fields[3])
            prev_close = float(fields[4])
            if current_price == 0: current_price = prev_close

            change_pct = 0.0
            if prev_close > 0:
                change_pct = ((current_price - prev_close) / prev_close) * 100
            
            return current_price, round(change_pct, 2)
        except Exception as e:
            logging.error(f"获取行情失败 {symbol}: {e}")
            return None, 0.00

    def run(self):
        # 非交易日直接返回
        if not self._is_trading_day():
            return

        """执行日报任务：抓取 -> 生成报告 -> 发送"""
        logging.info("开始执行 [日报任务]...")
        lines = []
        
        for item in self.config['holdings']:
            name = item['name']
            symbol = item['symbol_ref']
            
            price, day_change = self._get_price(symbol)
            
            if price is None or price == 0: continue
            
            # 图标逻辑
            if day_change > 0:
                icon = "📈" ; sign = "+"
            elif day_change < 0:
                icon = "📉" ; sign = "" 
            else:
                icon = "⚪" ; sign = ""

            line = f"{name}\n{icon} {sign}{day_change}%  {price}"
            lines.append(line)
            
        if not lines:
            logging.warning("日报内容为空，跳过发送")
            return

        report_content = "\n\n".join(lines)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"💷 定时推送 ({current_time})💷 \n━━━━━━━━━━━━━━━\n{report_content}"
        
        # 使用注入的 notifier 发送，逻辑统一
        self.notifier.send_text(full_msg)