## 服务启动
1. 构建 Docker 镜像：
   ```bash
   docker build -t lh-wx-helper:v1 .
   ```
2. 运行容器：
   ```bash
   docker run -d \
  --name lh-wx-helper \
  --restart always \
  -v $(pwd)/config:/app/config \
  lh-wx-helper:v1
   ```

## 回撤止盈策略
- 当 current_profit > 20% 时，进入“监控区”。

- 如果 current_profit 继续涨到 25%，不做操作，更新 max_profit = 25%。

- 只有当 current_profit 从 max_profit 回撤一定比例（比如回撤 3%，即跌回 22%）时，才发送坚决卖出的信号。

这样可以让你在单边上涨的行情里（如最近的纳指）吃到更多鱼身。

## 新增黄金机器人