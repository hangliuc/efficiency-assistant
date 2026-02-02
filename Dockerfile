FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 创建数据目录挂载点
VOLUME /app/data 
CMD ["python", "main.py"]