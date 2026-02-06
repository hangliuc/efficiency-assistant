# lh-wx-helper
## Finance
### 服务启动
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

## English

