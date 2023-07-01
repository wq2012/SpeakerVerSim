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
NUM_WORKERS = [10, 50, 100]
NUM_USERS = [1, 100, 10000]


def main():
    config_file = "example_config.yml"
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Less verbose logging.
    config["log_verbosity"] = 0

    results = {
        "SSO": [],
        "SSO-sync": [],
        "SSO-hash": [],
        "SSO-mul": [],
        "SDO": [],
    }

    for num_workers in NUM_WORKERS:
        print(f"Simulation for {num_workers} workers...")
        config["num_cloud_workers"] = num_workers

        for num_users in NUM_USERS:
            print(f"  Simulation for {num_users} users...")
            config["num_users"] = num_users
            # With more users, also increase QPS.
            if num_users > 1:
                config["client_request_interval"] = 1

            for _ in trange(NUM_RUNS):
                results["SSO"].append(
                    server_single_simple.simulate(
                        config, print_stats=False))
                results["SSO-sync"].append(
                    server_single_sync.simulate(
                        config, print_stats=False))
                results["SSO-hash"].append(
                    server_single_hash.simulate(
                        config,  print_stats=False))
                results["SSO-mul"].append(
                    server_single_multiprofile.simulate(
                        config, print_stats=False))
                results["SDO"].append(
                    server_double.simulate(
                        config, print_stats=False))

            results_file = os.path.join(
                "result_stats",
                "results_{}workers_{}users_{}runs.pickle".format(
                    num_workers, num_users, NUM_RUNS))
            with open(results_file, "wb") as f:
                pickle.dump(results, f)


if __name__ == "__main__":
    main()
