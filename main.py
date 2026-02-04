# main.py
import schedule
import time
import logging
import yaml
import os
from app.core.notifier import WeComNotifier
from app.modules.finance.monitor import FinanceMonitor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def load_config():
    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        logging.error("配置文件 config/config.yaml 不存在！")
        return None
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def job_daily_report():
    logging.info("开始执行定时持仓分析...")
    config = load_config()
    if not config: return

    # 1. 抓取数据
    monitor = FinanceMonitor(config)
    report_content = monitor.run_analysis()
    
    # 2. 发送通知
    if report_content:
        webhook_config = config['notification']['webhook']
        notifier = WeComNotifier(webhook_config)
        
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # 纯文本消息组合
        full_msg = f"💷 定时推送 ({current_time})💷 \n━━━━━━━━━━━━━━━\n{report_content}"
        
        # ⚠️ 注意这里改为 send_text
        notifier.send_text(full_msg)
    else:
        logging.warning("无报告内容生成")

def run():
    config = load_config()
    if not config: return
    
    # 注册定时任务
    times = config['schedules']['times']
    for t in times:
        schedule.every().day.at(t).do(job_daily_report)
        logging.info(f"⏰ 已设定任务: {t}")

    # --- 启动测试 ---
    logging.info("🚀 系统启动，正在测试 Webhook 推送...")
    job_daily_report()
    logging.info("✅ 测试运行结束。")
    # ---------------

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run()