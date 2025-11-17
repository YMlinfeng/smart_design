# 第一阶段：构建 wheels（不变）
FROM 129.211.72.112:6541/library/python/python-3.11-slim-bullseye AS wheels

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com

WORKDIR /wheels
# ✅ 只复制 requirements，不复制全部代码
COPY requirement.txt ./
RUN python -m pip install -U pip wheel --no-cache-dir --progress-bar off \
 && pip wheel --prefer-binary --no-cache-dir -r requirement.txt -w /wheels

# 第二阶段：创建 venv 并安装依赖
FROM 129.211.72.112:6541/library/python/python-3.11-slim-bullseye AS venv

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN python -m venv /opt/venv
COPY --from=wheels /wheels /wheels
COPY requirement.txt /tmp/requirement.txt

# ✅ 这一步只会在 requirement.txt 改变时重新执行
RUN . /opt/venv/bin/activate \
 && pip install --no-index --find-links=/wheels -r /tmp/requirement.txt --progress-bar off \
 && rm -rf /wheels /root/.cache /tmp/requirement.txt \
 && find /opt/venv -name '__pycache__' -type d -prune -exec rm -rf {} + \
 && find /opt/venv -name '*.pyc' -delete \
 && /opt/venv/bin/pip uninstall -y pip setuptools wheel || true

# 第三阶段：最终镜像
FROM 129.211.72.112:6541/library/python/python-3.11-slim-bullseye

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=venv /opt/venv /opt/venv
# ✅ 最后才复制代码（不影响缓存的 pip install）
COPY . .

EXPOSE 7753
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7753", "--workers", "1"]
