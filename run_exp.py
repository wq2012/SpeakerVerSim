import pickle
import yaml

import server_single_simple
import server_single_sync
import server_single_hash
import server_single_multiprofile
import server_double


NUM_RUNS = 100


def main():
    config_file = "example_config.yml"
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    results = {
        "SSO": [],
        "SSO-sync": [],
        "SSO-hash": [],
        "SSO-mul": [],
        "SDO": [],
    }

    for run in range(NUM_RUNS):
        results["SSO"].append(server_single_simple.simulate(config))
        results["SSO-sync"].append(server_single_sync.simulate(config))
        results["SSO-hash"].append(server_single_hash.simulate(config))
        results["SSO-mul"].append(server_single_multiprofile.simulate(config))
        results["SDO"].append(server_double.simulate(config))

    with open("results_10workers.pickle", "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    main()
