# app/modules/finance/monitor.py
import requests
import logging

class FinanceMonitor:
    def __init__(self, config):
        self.config = config
        self.base_url = "http://qt.gtimg.cn/q="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_price(self, symbol):
        """获取腾讯财经实时价格"""
        try:
            url = f"{self.base_url}{symbol}"
            resp = requests.get(url, headers=self.headers, timeout=5)
            
            try:
                content = resp.content.decode('gbk').strip()
            except UnicodeDecodeError:
                content = resp.text.strip()

            if '="' not in content:
                return None, 0.0

            data_str = content.split('="')[1].split('"')[0]
            if not data_str:
                return None, 0.0
                
            fields = data_str.split("~")
            if len(fields) < 10:
                return None, 0.0

            current_price = float(fields[3])
            prev_close = float(fields[4])
            
            if current_price == 0:
                current_price = prev_close

            if prev_close == 0:
                change_pct = 0.0
            else:
                change_pct = ((current_price - prev_close) / prev_close) * 100

            return current_price, round(change_pct, 2)

        except Exception as e:
            logging.error(f"获取行情失败 {symbol}: {e}")
        
        return None, 0.00

    def run_analysis(self):
        """生成持仓日报 (纯文本美化版)"""
        lines = []
        
        for item in self.config['holdings']:
            name = item['name']
            symbol = item['symbol_ref']
            
            price, day_change = self.get_price(symbol)
            
            if price is None or price == 0:
                continue
                
            # --- 视觉优化逻辑 ---
            
            # 1. 图标与符号
            if day_change > 0:
                icon = "📈" 
                sign = "+"
            elif day_change < 0:
                icon = "📉" 
                sign = "" 
            else:
                icon = "⚪"
                sign = ""

            # 2. 排版美化
            # 格式：
            # 🔴 +1.18%  沪深300
            #    4660.11
            
            line = (
                f"{name}\n"
                f"{icon} {sign}{day_change}%  {price}"
            )
            lines.append(line)
            
        # 使用分割线连接
        return "\n\n".join(lines)