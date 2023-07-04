import unittest
import yaml

import server_single_simple
import server_single_sync
import server_single_hash
import server_single_multiprofile
import server_double


class TestServerSimulation(unittest.TestCase):

    def setUp(self):
        with open("example_config.yml", "r") as f:
            self.config = yaml.safe_load(f)

    def test_server_single_simple(self):
        stats = server_single_simple.simulate(self.config)
        assert len(stats.final_messages) == 1080

    def test_server_single_syncself(self):
        stats = server_single_sync.simulate(self.config)
        assert len(stats.final_messages) == 1080

    def test_server_single_hash(self):
        stats = server_single_hash.simulate(self.config)
        assert len(stats.final_messages) == 1080
        assert stats.backward_bounce_count == 0
        assert stats.forward_bounce_count in {0, 1}

    def test_server_single_multiprofile(self):
        stats = server_single_multiprofile.simulate(self.config)
        assert len(stats.final_messages) == 1080
        assert stats.backward_bounce_count == 0
        assert stats.forward_bounce_count in {0, 1}

    def test_server_double(self):
        stats = server_double.simulate(self.config)
        assert len(stats.final_messages) == 1080
        assert stats.backward_bounce_count == 0
        assert stats.forward_bounce_count == 0


if __name__ == "__main__":
    unittest.main()
