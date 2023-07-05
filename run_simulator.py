"""Script to run one single simulation."""
import SpeakerVerSim
import argparse
import yaml


def main():
    parser = argparse.ArgumentParser(
        prog="run_simulator",
        description="Run a single simulation.")

    parser.add_argument("-c", "--config_file", default="example_config.yml")
    parser.add_argument("-s", "--strategy", choices=SpeakerVerSim.STRATEGIES)
    args = parser.parse_args()

    with open(args.config_file, "r") as f:
        config = yaml.safe_load(f)

    if args.strategy:
        config["strategy"] = args.strategy

    SpeakerVerSim.simulate(config)


if __name__ == "__main__":
    main()
