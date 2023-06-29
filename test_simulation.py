import server_single_simple
import server_single_sync


def test_server_single_simple():
    stats = server_single_simple.main()
    assert len(stats.final_messages) == 1080


def test_server_single_sync():
    stats = server_single_sync.main()
    assert len(stats.final_messages) == 1080
