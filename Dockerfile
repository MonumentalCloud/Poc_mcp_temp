FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ server/
COPY skills/ skills/
COPY vdb/ vdb/

ENV PORT=8000
EXPOSE 8000

# streamable HTTP MCP endpoint: http://<host>:$PORT/mcp  (health: /health)
CMD ["python", "-m", "server.main"]
