"""Script to run one single simulation."""
import SpeakerVerSim
import argparse
import yaml
import munch


def main():
    parser = argparse.ArgumentParser(
        prog="run_simulator",
        description="Run a single simulation.")

    parser.add_argument("-c", "--config", default="example_config.yml")
    parser.add_argument("-s", "--strategy", choices=SpeakerVerSim.STRATEGIES)
    args = parser.parse_args()

    with open(args.config, "r") as f:
        config = munch.Munch.fromDict(yaml.safe_load(f))

    if args.strategy:
        config.strategy = args.strategy

    SpeakerVerSim.simulate(config)


if __name__ == "__main__":
    main()
