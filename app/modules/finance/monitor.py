# app/modules/finance/monitor.py
import requests
import logging

class FinanceMonitor:
    def __init__(self, config):
        self.config = config
        # 腾讯财经接口
        self.base_url = "http://qt.gtimg.cn/q="
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_price(self, symbol):
        """
        使用腾讯财经接口获取实时价格
        symbol: e.g., sh513100
        """
        try:
            url = f"{self.base_url}{symbol}"
            # 腾讯接口极快，5秒超时足够
            resp = requests.get(url, headers=self.headers, timeout=5)
            
            # 关键：腾讯接口返回的是 GBK 编码，必须显式解码，否则中文会乱码
            try:
                content = resp.content.decode('gbk').strip()
            except UnicodeDecodeError:
                # 如果GBK解不开，尝试utf-8或忽略错误，防止程序崩溃
                content = resp.text.strip()

            # 响应示例: v_sh513100="1~纳指ETF~513100~1.833~..."
            if '="' not in content:
                logging.warning(f"数据格式异常: {content}")
                return None, 0.0

            # 提取双引号内容
            data_str = content.split('="')[1].split('"')[0]
            if not data_str:
                return None, 0.0
                
            fields = data_str.split("~")
            if len(fields) < 10:
                return None, 0.0

            # 字段 3: 当前价 (1.833)
            # 字段 4: 昨收价 (1.881)
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
        
        return None, 0.0

    def run_analysis(self):
        """生成持仓日报"""
        lines = []
        
        for item in self.config['holdings']:
            name = item['name']
            symbol = item['symbol_ref']
            cost = item['cost_price']
            
            price, day_change = self.get_price(symbol)
            
            if price is None or price == 0:
                logging.warning(f"{name} 获取失败，跳过")
                continue
                
            total_profit_pct = ((price - cost) / cost) * 100
            
            day_color = "warning" if day_change >= 0 else "info"
            day_sign = "+" if day_change >= 0 else ""
            
            total_color = "warning" if total_profit_pct >= 0 else "info"
            total_sign = "+" if total_profit_pct >= 0 else ""

            icon = "🔴" if day_change >= 0 else "🟢"
            
            line = (
                f"{icon} **{name}**\n"
                f"> 现价: {price} (<font color=\"{day_color}\">{day_sign}{day_change}%</font>)\n"
                f"> 收益: <font color=\"{total_color}\">{total_sign}{total_profit_pct:.2f}%</font>"
            )
            lines.append(line)
            
        return "\n\n".join(lines)