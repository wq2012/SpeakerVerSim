"""Batch script to visualize experimental results reported in the paper."""
import seaborn as sns
import pickle
import os
from typing import Callable
import matplotlib.pyplot as plt

from SpeakerVerSim.common import STRATEGIES

NUM_RUNS = 100
NUM_USERS = [1, 100, 1000]
NUM_WORKERS = [10, 100, 500]
STATS_DIR = "result_stats"
OUTPUT_DIR = "figures"


def visualize_single_run_metrics(
        num_users: int,
        label: str,
        figure_name: str,
        get_metrics: Callable):
    """Visualize the metrics of a single simulation run.

    get_metrics is called on one final message.
    """
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
            # Only first run.
            stats = results[strategy][0]

            for msg in stats.final_messages:
                x.append(strategy)
                y.append(get_metrics(msg))
                hue.append(num_workers)
    ax = sns.boxplot(x=x, y=y, hue=hue)
    ax.legend(title="Number of workers")
    ax.set_xlabel("Strategy")
    ax.set_ylabel(label)
    plt.tight_layout()
    plt.savefig(os.path.join("figures", figure_name))
    plt.close()


def visualize_aggregated_metrics(
        num_users: int,
        label: str,
        figure_name: str,
        get_metrics: Callable):
    """Visualize the metrics aggregated on many simulation runs.

    get_metrics is called on stats.
    """
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


def visualize_workload(
        num_users: int,
        num_workers: int,
        figure_name: str):
    """Visualize the workload of different workers over time."""

    results_file = os.path.join(
        STATS_DIR,
        "results_{}workers_{}users_{}runs.pickle".format(
            num_workers, num_users, NUM_RUNS))
    with open(results_file, "rb") as f:
        results = pickle.load(f)

    _, axes = plt.subplots(len(STRATEGIES), 1, figsize=(15, 20))
    for row, strategy in enumerate(STRATEGIES):
        stats = results[strategy][0]
        x = []
        weights = []
        hue = []
        for i in range(num_workers):
            worker_name = f"worker-{i}"
            if worker_name not in stats.workload:
                stats.workload[worker_name] = []
            for event_time, event_flops in stats.workload[worker_name]:
                x.append(event_time)
                weights.append(event_flops)
                hue.append(worker_name)

        ax = sns.kdeplot(ax=axes[row], x=x,
                         weights=weights, hue=hue, bw_adjust=0.05,
                         clip=[100, stats.config.time_to_run-100])
        ax.set_title(strategy)
        ax.set(xticks=[], xlabel="")
        ax.set(yticks=[], ylabel="")

    plt.tight_layout()
    plt.savefig(os.path.join("figures", figure_name))
    plt.close()


def visualize_sso_sync_sweep_interval(
        num_users: int,
        label: str,
        figure_name: str,
        get_metrics: Callable):
    """Visualize SSO-sync metrics for sweeping the version_query_interval."""
    x = []
    y = []
    hue = []
    for num_workers in NUM_WORKERS:
        results_file = os.path.join(
            STATS_DIR,
            "results_{}workers_{}users_{}runs_sweep_interval.pickle".format(
                num_workers, num_users, NUM_RUNS))
        with open(results_file, "rb") as f:
            results = pickle.load(f)

        for interval in [1, 10, 30, 60, 300, 600, 1800, 3600]:
            for run in range(NUM_RUNS):
                stats = results[interval][run]
                x.append(interval)
                y.append(get_metrics(stats))
                hue.append(num_workers)
    ax = sns.boxplot(x=x, y=y, hue=hue)
    ax.legend(title="Number of workers")
    ax.set_xlabel("Version query interval")
    ax.set_ylabel(label)
    plt.tight_layout()
    plt.savefig(os.path.join("figures", figure_name))
    plt.close()


def main():
    # Create output dir.
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    sns.set_theme(palette="colorblind")

    # End-to-end latency.
    visualize_single_run_metrics(
        num_users=1,
        label="End-to-end latency",
        figure_name="e2e_latency.png",
        get_metrics=lambda x: x.client_return_time - x.client_send_time,
    )

    visualize_aggregated_metrics(
        num_users=1,
        label="Average end-to-end latency",
        figure_name="average_e2e_latency.png",
        get_metrics=lambda x: x.average_e2e_latency,
    )

    visualize_aggregated_metrics(
        num_users=1,
        label="Max end-to-end latency",
        figure_name="max_e2e_latency.png",
        get_metrics=lambda x: x.max_e2e_latency,
    )

    # Total flops per request.
    visualize_single_run_metrics(
        num_users=1,
        label="Flops",
        figure_name="total_flops.png",
        get_metrics=lambda x: x.total_flops,
    )

    visualize_aggregated_metrics(
        num_users=1,
        label="Average flops per request",
        figure_name="average_total_flops.png",
        get_metrics=lambda x: x.average_total_flops,
    )

    visualize_aggregated_metrics(
        num_users=1,
        label="Max flops per request",
        figure_name="max_total_flops.png",
        get_metrics=lambda x: x.max_total_flops,
    )

    # Backward bounce rate.
    visualize_aggregated_metrics(
        num_users=1,
        label="Backward bounce rate",
        figure_name="backward_bounce_rate.png",
        get_metrics=lambda x: x.backward_bounce_count / x.total_num_messages,
    )

    # Workload.
    visualize_workload(
        num_users=100,
        num_workers=10,
        figure_name="workload_10workers_100users.png",
    )

    # SSO-sync sweep interval.
    visualize_sso_sync_sweep_interval(
        num_users=1,
        label="Average end-to-end latency",
        figure_name="average_e2e_latency_sweep_interval.png",
        get_metrics=lambda x: x.average_e2e_latency,
    )


if __name__ == "__main__":
    main()
