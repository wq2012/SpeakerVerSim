import unittest
import yaml
import munch

from SpeakerVerSim import server_single_simple
from SpeakerVerSim import server_single_sync
from SpeakerVerSim import server_single_hash
from SpeakerVerSim import server_single_multiprofile
from SpeakerVerSim import server_double
from SpeakerVerSim import simulate


class TestServerSimulation(unittest.TestCase):
    """Test the simulate function from each Python script."""

    def setUp(self):
        with open("example_config.yml", "r") as f:
            self.config = munch.Munch.fromDict(yaml.safe_load(f))

    def test_server_single_simple(self):
        self.config.strategy = "SSO"
        stats = server_single_simple.simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertGreater(stats.backward_bounce_count, 1)
        self.assertGreater(stats.forward_bounce_count, 1)

    def test_server_single_sync(self):
        self.config.strategy = "SSO-sync"
        stats = server_single_sync.simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertGreater(stats.forward_bounce_count, 0)

    def test_server_single_hash(self):
        self.config.strategy = "SSO-hash"
        stats = server_single_hash.simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertEqual(stats.backward_bounce_count, 0)
        self.assertIn(stats.forward_bounce_count, {0, 1})

    def test_server_single_multiprofile(self):
        self.config.strategy = "SSO-mul"
        stats = server_single_multiprofile.simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertEqual(stats.backward_bounce_count, 0)
        self.assertIn(stats.forward_bounce_count, {0, 1})

    def test_server_double(self):
        self.config.strategy = "SD"
        stats = server_double.simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertEqual(stats.backward_bounce_count, 0)
        self.assertEqual(stats.forward_bounce_count, 0)

    def test_bad_strategy(self):
        with self.assertRaises(ValueError):
            server_double.simulate(self.config)


class TestSimulatorAPI(unittest.TestCase):
    """Test the simulator API."""

    def setUp(self):
        with open("example_config.yml", "r") as f:
            self.config = munch.Munch.fromDict(yaml.safe_load(f))

    def test_simulator_SSO(self):
        self.config.strategy = "SSO"
        stats = simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertGreater(stats.backward_bounce_count, 1)
        self.assertGreater(stats.forward_bounce_count, 1)

    def test_simulator_SSO_sync(self):
        self.config.strategy = "SSO-sync"
        stats = simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertGreater(stats.forward_bounce_count, 0)

    def test_simulator_SSO_hash(self):
        self.config.strategy = "SSO-hash"
        stats = simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertEqual(stats.backward_bounce_count, 0)
        self.assertIn(stats.forward_bounce_count, {0, 1})

    def test_simulator_SSO_mul(self):
        self.config.strategy = "SSO-mul"
        stats = simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertEqual(stats.backward_bounce_count, 0)
        self.assertIn(stats.forward_bounce_count, {0, 1})

    def test_simulator_SD(self):
        self.config.strategy = "SD"
        stats = simulate(self.config)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertEqual(stats.backward_bounce_count, 0)
        self.assertEqual(stats.forward_bounce_count, 0)

    def test_bad_strategy(self):
        self.config.strategy = ""
        with self.assertRaises(ValueError):
            simulate(self.config)

    def test_simulator_file_input(self):
        config_file = "example_config.yml"
        stats = simulate(config_file)
        self.assertEqual(len(stats.final_messages), 1080)
        self.assertGreater(stats.backward_bounce_count, 1)
        self.assertGreater(stats.forward_bounce_count, 1)


if __name__ == "__main__":
    unittest.main()
