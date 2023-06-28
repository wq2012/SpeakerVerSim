"""Configurations for running experiments."""

# How may cloud workers do we have in total.
NUM_CLOUD_WORKERS = 10

# Latency between client and frontend server.
CLIENT_FRONTEND_LATENCY = 0.1

# Latency between frontend server and cloud worker.
FRONTEND_WORKER_LATENCY = 0.002

# Latency for database IO.
DATABASE_IO_LATENCY = 0.005

# Latency to run speech inference engine.
WORKER_INFERENCE_LATENCY = 0.5

# Flops cost to run one inference.
FLOPS_PER_INFERENCE = 1000000

# How often do we send requests.
CLIENT_REQUEST_INTERVAL = 10

# Mean time of a model version update for each worker.
WORKER_UPDATE_MEAN_TIME = 3600
