import server_single_simple
import server_single_sync
import server_single_hash
import server_single_multiprofile
import server_double


def test_server_single_simple():
    stats = server_single_simple.main()
    assert len(stats.final_messages) == 1080


def test_server_single_sync():
    stats = server_single_sync.main()
    assert len(stats.final_messages) == 1080


def test_server_single_hash():
    stats = server_single_hash.main()
    assert len(stats.final_messages) == 1080
    assert stats.backward_bounce_count == 0
    assert stats.forward_bounce_count in {0, 1}


def test_server_single_multiprofile():
    stats = server_single_multiprofile.main()
    assert len(stats.final_messages) == 1080
    assert stats.backward_bounce_count == 0
    assert stats.forward_bounce_count in {0, 1}


def test_server_double():
    stats = server_double.main()
    assert len(stats.final_messages) == 1080
    assert stats.backward_bounce_count == 0
    assert stats.forward_bounce_count == 0
