# 使用官方轻量级 Python 镜像
FROM python:3.9-slim

WORKDIR /app

# 设置时区为上海 (北京时间)，确保 schedule 定时任务准时触发
ENV TZ=Asia/Shanghai
# 确保 Python 日志不被缓存，直接输出到 Docker logs，方便排查问题
ENV PYTHONUNBUFFERED=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY requirements.txt .
# 使用阿里云镜像源加速安装 (国内服务器必备)
RUN pip3 install --no-cache-dir -r requirements.txt 

COPY . .

CMD ["python", "main.py"]