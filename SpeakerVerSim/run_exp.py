import pickle
import yaml
from tqdm import trange
import os

import server_single_simple
import server_single_sync
import server_single_hash
import server_single_multiprofile
import server_double


NUM_RUNS = 100
NUM_USERS = [1, 100, 1000]
NUM_WORKERS = [10, 100, 500]
OUTPUT_DIR = "result_stats"


def main():
    config_file = "example_config.yml"
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Less verbose logging.
    config["log_verbosity"] = 0
    config["print_stats"] = False

    # Create output dir.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for num_users in NUM_USERS:
        print(f"  Simulation for {num_users} users...")
        config["num_users"] = num_users
        # With more users, also increase QPS.
        if num_users > 1:
            config["client_request_interval"] = 1

        for num_workers in NUM_WORKERS:
            print(f"Simulation for {num_workers} workers...")
            config["num_cloud_workers"] = num_workers

            results = {
                "SSO": [],
                "SSO-sync": [],
                "SSO-hash": [],
                "SSO-mul": [],
                "SDO": [],
            }

            for _ in trange(NUM_RUNS):
                results["SSO"].append(
                    server_single_simple.simulate(config))
                results["SSO-sync"].append(
                    server_single_sync.simulate(config))
                results["SSO-hash"].append(
                    server_single_hash.simulate(config))
                results["SSO-mul"].append(
                    server_single_multiprofile.simulate(config))
                results["SDO"].append(
                    server_double.simulate(config))

            results_file = os.path.join(
                OUTPUT_DIR,
                "results_{}workers_{}users_{}runs.pickle".format(
                    num_workers, num_users, NUM_RUNS))
            with open(results_file, "wb") as f:
                pickle.dump(results, f)


if __name__ == "__main__":
    main()
