import seaborn as sns
import pickle
import os
from typing import Callable
import matplotlib.pyplot as plt

NUM_RUNS = 100
NUM_USERS = [1, 100, 1000]
NUM_WORKERS = [10, 100, 500]
STRATEGIES = ["SSO", "SSO-sync", "SSO-hash", "SSO-mul", "SDO"]
STATS_DIR = "result_stats"
OUTPUT_DIR = "figures"


def visualize_aggregated_metrics(
        num_users: int,
        label: str,
        figure_name: str,
        get_metrics: Callable):
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
                y.append(get_metrics(stats))
                hue.append(num_workers)
    ax = sns.boxplot(x=x, y=y, hue=hue)
    ax.legend(title="Number of workers")
    ax.set_xlabel("Strategy")
    ax.set_ylabel(label)
    plt.tight_layout()
    plt.savefig(os.path.join("figures", figure_name))
    plt.close()


def main():
    # Create output dir.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sns.set_theme(palette="colorblind")

    # End-to-end latency.
    visualize_aggregated_metrics(
        num_users=1,
        label="End-to-end latency",
        figure_name="average_e2e_latency.png",
        get_metrics=lambda x: x.average_e2e_latency,
    )

    # Total flops per request.
    visualize_aggregated_metrics(
        num_users=1,
        label="Flops per request",
        figure_name="average_total_flops.png",
        get_metrics=lambda x: x.average_total_flops,
    )

    # Backward bounce rate.
    visualize_aggregated_metrics(
        num_users=1,
        label="Backward bounce rate",
        figure_name="backward_bounce_rate.png",
        get_metrics=lambda x: x.backward_bounce_count / x.total_num_messages,
    )


if __name__ == "__main__":
    main()
