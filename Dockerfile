FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ server/
COPY skills/ skills/
COPY vdb/ vdb/

ENV PORT=8000
# 프록시(fly.dev 등) 뒤에서 서비스: FastMCP의 localhost 전용 Host 헤더 검증(DNS
# rebinding 보호)을 끈다 — 공개 호스트명/내부 헬스체크 Host가 421로 거부되는 것 방지
ENV FASTMCP_HTTP_HOST_ORIGIN_PROTECTION=false
EXPOSE 8000

# streamable HTTP MCP endpoint: http://<host>:$PORT/mcp  (health: /health)
CMD ["python", "-m", "server.main"]
