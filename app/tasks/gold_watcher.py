# app/tasks/gold_watcher.py
import requests
import logging
import datetime

class GoldWatcher:
    def __init__(self, config, notifier):
        self.targets = config.get('gold_targets', [])
        self.notifier = notifier
        
        self.headers = {
            "Referer": "https://finance.sina.com.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # 记录已报警的层级
        self.alerted_levels = {}
        
        # [关键] 记录上一次重置的日期
        self.last_reset_date = datetime.date.today()

    def _check_date_reset(self):
        """检查是否跨天，如果是，重置状态"""
        today = datetime.date.today()
        if today != self.last_reset_date:
            logging.info(f"📅 检测到日期变更 ({self.last_reset_date} -> {today})，重置黄金报警状态。")
            self.alerted_levels.clear() # 清空所有记录
            self.last_reset_date = today

    def _get_sina_price(self, code):
        """内部方法：获取新浪价格"""
        try:
            url = f"http://hq.sinajs.cn/list={code}"
            resp = requests.get(url, headers=self.headers, timeout=30)
            content = resp.text.strip()
            
            if '="' not in content: return None, 0.0
            data = content.split('="')[1].split('"')[0].split(',')
            
            current = 0.0
            prev_close = 0.0
            
            if code.startswith("hf_"): # 伦敦金
                if len(data) > 7:
                    current = float(data[0]); prev_close = float(data[7])
            elif code.startswith("g_"): # 上海金
                 if len(data) > 4:
                    current = float(data[0]); prev_close = float(data[4]) 
            
            pct = 0.0
            if prev_close > 0:
                pct = ((current - prev_close) / prev_close) * 100
            return current, pct
        except Exception as e:
            logging.error(f"黄金接口异常 {code}: {e}")
            return None, 0.0

    def run(self):
        logging.info("执行 [黄金巡检]...")
        # 1. 每次执行前，先检查一下是不是新的一天
        self._check_date_reset()

        for item in self.targets:
            name = item['name']
            code = item['code']
            
            price, pct = self._get_sina_price(code)
            if price is None or price == 0: 
                logging.warning(f"⚠️ {name}: 价格获取失败")
            else:
                logging.info(f"🔎 {name}: 当前 {price}, 涨幅 {pct:.2f}%")

            if code not in self.alerted_levels:
                self.alerted_levels[code] = set()

            # --- 逻辑调整：步长 0.5% ---
            step = 0.5 
            
            # 计算当前等级 (取整)
            # 例如: 0.6% / 0.5 = 1.2 -> int 1 (代表触发 0.5% 线)
            # 例如: 1.2% / 0.5 = 2.4 -> int 2 (代表触发 1.0% 线)
            level = int(pct / step)
            
            # 只有当等级不为0，且该等级没报过，才报警
            if level != 0 and level not in self.alerted_levels[code]:
                
                # 计算触发阈值 (用于显示)
                trigger_val = abs(level * step)
                
                direction = "上涨" if level > 0 else "下跌"
                icon = "🚀" if level > 0 else "📉"
                
                msg = (
                    f"{icon} 黄金风控警报\n"
                    f"━━━━━━━━━━\n"
                    f"{name}\n"
                    f"动态: {direction}超 {trigger_val:.1f}%\n"
                    f"现价: {price}\n"
                    f"今日涨幅: {pct:+.2f}%"
                )
                
                self.notifier.send_text(msg)
                
                # 记录该等级已报过
                self.alerted_levels[code].add(level)
                
                # [优化] 自动标记“路过”的低等级
                # 如果直接暴涨到 1.0% (Level 2)，把 0.5% (Level 1) 也标记为已报
                if level > 0:
                    for i in range(1, level):
                        self.alerted_levels[code].add(i)
                elif level < 0:
                    for i in range(level + 1, 0):
                        self.alerted_levels[code].add(i)