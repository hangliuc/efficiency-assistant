# app/modules/finance/monitor.py
import requests
import logging

class FinanceMonitor:
    def __init__(self, config):
        self.config = config
        # 新浪接口支持批量查询，但为了逻辑简单，我们逐个查
        # 接口格式: http://hq.sinajs.cn/list=sh513100
        self.base_url = "http://hq.sinajs.cn/list="
        self.headers = {
            "Referer": "https://finance.sina.com.cn/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_price(self, symbol):
        """
        使用新浪财经接口获取实时价格 (极速、海外可用)
        symbol: e.g., sh513100
        """
        try:
            url = f"{self.base_url}{symbol}"
            resp = requests.get(url, headers=self.headers, timeout=5)
            
            # 响应格式: var hq_str_sh513100="纳指ETF,1.246,1.253,1.249,..."
            # 数据字段索引: 0:名称, 1:开盘, 2:昨收, 3:当前价, ...
            content = resp.text.strip()
            
            if "=\"" not in content:
                logging.warning(f"数据格式异常: {content}")
                return None, 0.0

            # 解析数据字符串
            data_str = content.split("=\"")[1].split("\"")[0]
            if not data_str:
                logging.warning(f"未获取到数据内容: {symbol}")
                return None, 0.0
                
            fields = data_str.split(",")
            if len(fields) < 4:
                return None, 0.0

            # 提取关键数据
            # 昨收 (用于计算涨跌幅) -> Index 2
            # 当前价 -> Index 3
            prev_close = float(fields[2])
            current_price = float(fields[3])
            
            # 停牌或集合竞价期间可能价格为0
            if current_price == 0:
                current_price = prev_close # 暂用昨收代替，或处理为0

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
            
            # 1. 获取现价
            price, day_change = self.get_price(symbol)
            
            if price is None or price == 0:
                logging.warning(f"{name} ({symbol}) 获取失败，跳过")
                continue
                
            # 2. 计算累计收益率
            total_profit_pct = ((price - cost) / cost) * 100
            
            # 3. 格式化输出
            # 颜色逻辑：企业微信 warning=橙红(涨), info=绿(跌)
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