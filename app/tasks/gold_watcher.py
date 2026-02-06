# app/tasks/gold_watcher.py
import requests
import logging
import datetime

class GoldWatcher:
    def __init__(self, config, notifier):
        self.notifier = notifier
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # 记录已报警的层级
        self.alerted_levels = set()
        
        # 记录基准价 (用于计算涨跌幅，因为 Swissquote 不返回涨跌幅)
        self.baseline_price = None
        self.last_reset_date = datetime.date.today()

    def _check_reset(self):
        """跨天重置逻辑"""
        today = datetime.date.today()
        if today != self.last_reset_date:
            logging.info(f"📅 日期变更，重置黄金报警状态")
            self.alerted_levels.clear()
            self.baseline_price = None # 每天重新定基准
            self.last_reset_date = today

    def _get_price(self):
        """获取瑞讯银行实时价格"""
        url = "https://forex-data-feed.swissquote.com/public-quotes/bboquotes/instrument/XAU/USD"
        try:
            # 30秒超时，防止网络波动
            resp = requests.get(url, headers=self.headers, timeout=30)
            data = resp.json()
            
            # 解析: List -> 0 -> spreadProfilePrices -> 0 -> bid/ask
            if not data: return 0.0
            quote = data[0]['spreadProfilePrices'][0]
            
            bid = float(quote['bid'])
            ask = float(quote['ask'])
            
            # 取中间价
            return (bid + ask) / 2
        except Exception as e:
            logging.error(f"⚠️ 黄金接口异常: {e}")
            return 0.0

    def run(self):
        self._check_reset()

        price = self._get_price()
        if price == 0: return

        # 1. 初始化基准价 (如果是当天第一次运行)
        if self.baseline_price is None:
            self.baseline_price = price
            logging.info(f"⚓️ 黄金基准价已锁定: {price:.2f}")
            return

        # 2. 计算涨跌幅
        pct = ((price - self.baseline_price) / self.baseline_price) * 100
        logging.info(f"🔎 黄金当前: {price:.2f}, 波动: {pct:+.2f}%")

        # 3. 智能报警策略 (非对称网格)
        # 规则:
        # A. 上涨: 必须 >= 1.0% 才开始报 (忽略 0.5%)
        # B. 下跌: 必须 <= -1.0% 才开始报
        # C. 中间 (-0.49% ~ 0.99%): 即使从高处跌回来，也不报警
        
        level = 0
        step = 1.0 

        if pct >= 1.0:
            # 例如 1.2% -> int(2.4) -> level 2
            level = int(pct / step) 
        elif pct <= -1.0:
            # 例如 -0.6% -> int(-1.2) -> level -1
            level = int(pct / step)
        
        # 只有触发了等级 (level != 0) 且该等级没报过，才报警
        if level != 0 and level not in self.alerted_levels:
            
            trigger_val = abs(level * step)
            direction = "暴涨" if level > 0 else "暴跌"
            icon = "📈" if level > 0 else "📉"
            
            msg = (
                f"{icon} 黄金风控警报 🚨🚨🚨\n"
                f"━━━━━━━━━━\n"
                f"伦敦金 (XAU)\n"
                f"动态: {direction}超 {trigger_val:.1f}%\n"
                f"现价: {price:.2f}\n"
                f"今日波动: {pct:+.2f}%"
            )
            
            self.notifier.send_text(msg)
            
            # 记录该等级
            self.alerted_levels.add(level)
            
            # 优化: 把路过的低等级也标记为“已报”，防止回调骚扰
            if level > 0:
                for i in range(1, level): self.alerted_levels.add(i)
            elif level < 0:
                for i in range(level + 1, 0): self.alerted_levels.add(i)