# 1. 构建镜像
docker build -t efficiency-assistant .

# 2. 运行 (挂载 data 目录以持久化 state.json)
docker run -d \
  --name my-assistant \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v /etc/localtime:/etc/localtime:ro \
  efficiency-assistant


## 回撤止盈策略
- 当 current_profit > 20% 时，进入“监控区”。

- 如果 current_profit 继续涨到 25%，不做操作，更新 max_profit = 25%。

- 只有当 current_profit 从 max_profit 回撤一定比例（比如回撤 3%，即跌回 22%）时，才发送坚决卖出的信号。

这样可以让你在单边上涨的行情里（如最近的纳指）吃到更多鱼身。


## 代码结构
```shell
efficiency-assistant/
├── config/
│   └── config.yaml          # 全局配置文件
├── data/
│   └── finance_state.json   # [自动生成] 用于持久化存储最高收益率(max_profit)
├── app/
│   ├── __init__.py
│   ├── core/                # 核心组件
│   │   ├── __init__.py
│   │   ├── config_loader.py # 配置加载器
│   │   └── notifier.py      # 统一通知模块 (企业微信)
│   ├── modules/             # 业务模块 (可扩展英语、个人管理)
│   │   ├── __init__.py
│   │   └── finance/         # 金融理财模块
│   │       ├── __init__.py
│   │       ├── monitor.py   # 负责抓取数据
│   │       └── strategy.py  # [核心] 负责止盈策略 & 状态管理
│   └── utils/
│       └── logger.py
├── main.py                  # 程序入口
├── requirements.txt
└── Dockerfile
```