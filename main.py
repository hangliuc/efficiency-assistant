# main.py
import schedule
import time
import logging
import yaml
import os
from app.core.notifier import WeComAppNotifier
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
    
    # 2. 发送通知 (使用应用模式)
    if report_content:
        # 传入 wecom_app 部分的配置
        app_config = config['notification']['wecom_app']
        notifier = WeComAppNotifier(app_config)
        
        current_time = time.strftime("%H:%M")
        full_msg = f"### 📊 持仓监控日报 ({current_time})\n----------------\n{report_content}"
        
        notifier.send_markdown(full_msg)
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

    # --- 启动时立即测试一次 ---
    logging.info("🚀 系统启动，正在测试应用消息推送...")
    job_daily_report()
    logging.info("✅ 测试运行结束，请检查企业微信应用通知。")
    # -----------------------

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run()