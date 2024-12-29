# 使用官方 Python 镜像作为基础镜像
FROM python:3.10-slim-buster

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 文件到容器中
COPY requirements.txt .

# 安装项目依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码到容器中
COPY . .

# 暴露端口
EXPOSE 7874

# 定义环境变量文件路径
ENV ENV_FILE /app/.env

# 运行命令
CMD ["gunicorn", "--env", "ENV_FILE", "--bind", "0.0.0.0:8000", "app:app"]