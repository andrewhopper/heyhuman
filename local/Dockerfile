# HeyHuman local server. EXPERIMENTAL CODE. Do not use in production.
# File UUID: 4c9a7e21-8d36-4f05-b2e1-6a3f0d8c5b74
FROM python:3.12-slim
RUN pip install --no-cache-dir boto3==1.* paho-mqtt==2.*
WORKDIR /app
COPY lambda/ lambda/
COPY local/serve.py local/serve.py
RUN useradd -r -u 10001 heyhuman && mkdir /data && chown heyhuman /data
USER heyhuman
EXPOSE 8787
CMD ["python3", "-I", "local/serve.py", "--port", "8787", "--db", "/data/heyhuman.db"]
