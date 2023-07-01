import seaborn as sns
import pickle
import os
import matplotlib.pyplot as plt

NUM_RUNS = 100
NUM_USERS = [1, 100, 1000]
NUM_WORKERS = [10, 100, 500]
STRATEGIES = ["SSO", "SSO-sync", "SSO-hash", "SSO-mul", "SDO"]
STATS_DIR = "result_stats"
OUTPUT_DIR = "figures"


def visualize_e2e_latency():
    num_users = 1
    x = []
    y = []
    hue = []
    for num_workers in NUM_WORKERS:
        results_file = os.path.join(
            STATS_DIR,
            "results_{}workers_{}users_{}runs.pickle".format(
                num_workers, num_users, NUM_RUNS))
        with open(results_file, "rb") as f:
            results = pickle.load(f)

        for strategy in STRATEGIES:
            for run in range(NUM_RUNS):
                stats = results[strategy][run]
                x.append(strategy)
                y.append(stats.average_e2e_latency)
                hue.append(num_workers)
    ax = sns.boxplot(x=x, y=y, hue=hue)
    ax.legend(title="Number of workers")
    ax.set_xlabel("Strategy")
    ax.set_ylabel("End-to-end latency")
    plt.tight_layout()
    plt.savefig(os.path.join("figures", "average_e2e_latency.png"))


def main():
    # Create output dir.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sns.set_theme()
    visualize_e2e_latency()


if __name__ == "__main__":
    main()
