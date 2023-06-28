import server_single_simple


def test_server_single_simple():
    stats = server_single_simple.main()
    assert len(stats.final_messages) == 100


test_server_single_simple()
