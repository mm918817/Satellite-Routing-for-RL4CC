FROM python:3.11-slim

# Per problemi dei log Ray
#ENV RAY_DEDUP_LOGS=0 # Forza print dei messaggi di log individuale
#ENV RAY_AIR_NEW_OUTPUT=0 # Per usare formato output vecchio


RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

# Installa torch prima per tenerlo in cache e poi i requirements
WORKDIR /app
RUN pip install torch
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia RL4CC, lo script principale ed i file necessari
COPY RL4CC-main ./RL4CC-main
COPY main.py .
COPY exp_config.json .
COPY env_config.json .
COPY ray_config.json .
COPY tune_config.json .
COPY src ./src
COPY flows_src__dst_timeline.json .
COPY flows_eval.json .
COPY satellite_topology.json .
COPY dijkstra_results.json .

# Installa RL4CC
WORKDIR /app/RL4CC-main
RUN pip install .

WORKDIR /app

# Default command del container
CMD ["python", "main.py"]
