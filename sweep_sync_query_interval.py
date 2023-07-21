"""Script to sweep version_query_interval for SSO-sync."""
import pickle
import yaml
from tqdm import trange
import os
import munch

from SpeakerVerSim import simulate


NUM_RUNS = 100
NUM_USERS = 1
NUM_WORKERS = [10, 100, 500]
QUERY_INTERVAL = [1, 10, 30, 60, 300, 600, 1800, 3600]
OUTPUT_DIR = "result_stats"
STRATEGY = "SSO-sync"


def main():
    config_file = "example_config.yml"
    with open(config_file, "r") as f:
        config = munch.Munch.fromDict(yaml.safe_load(f))

    # Less verbose logging.
    config.log_verbosity = 0
    config.print_stats = False

    config.num_users = NUM_USERS
    config.strategy = STRATEGY

    # Create output dir.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for num_workers in NUM_WORKERS:
        print(f"Simulation for {num_workers} workers...")
        config.num_cloud_workers = num_workers

        # Initialize the results.
        results = {interval: [] for interval in QUERY_INTERVAL}

        for _ in trange(NUM_RUNS):
            for interval in QUERY_INTERVAL:
                config.version_query_interval = interval
                results[interval].append(simulate(config))

        results_file = os.path.join(
            OUTPUT_DIR,
            "results_{}workers_{}users_{}runs_sweep_interval.pickle".format(
                num_workers, NUM_USERS, NUM_RUNS))
        with open(results_file, "wb") as f:
            pickle.dump(results, f)


if __name__ == "__main__":
    main()
