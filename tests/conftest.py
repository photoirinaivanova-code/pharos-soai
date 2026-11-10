import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="Run tests that call the public Atlantic Testnet RPC",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "live: optional tests that call the public RPC")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-live"):
        return
    skip_live = pytest.mark.skip(reason="need --run-live to hit the public RPC")
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
