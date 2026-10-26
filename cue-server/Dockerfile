FROM python:3.12-slim
WORKDIR /app
COPY server.py .
RUN useradd --create-home --uid 10001 cue && mkdir -p /app/data && chown cue /app/data
USER cue
ENV HOST=0.0.0.0 PORT=8080 PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
