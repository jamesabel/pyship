from ismain import is_main
import time
import random

from pyship.launcher import RestartMonitor


def test_restart_monitor_excessive():
    restart_monitor = RestartMonitor()
    for _ in range(0, restart_monitor.max_samples):
        assert not restart_monitor.excessive()
        restart_monitor.add()
        time.sleep(0.1 * random.random())
    for _ in range(0, 4):
        assert restart_monitor.excessive()
        restart_monitor.add()
        time.sleep(0.1 * random.random())


def test_restart_monitor_not_excessive():
    restart_monitor = RestartMonitor()
    quick = 0.1
    restart_monitor.quick = quick  # make the "quick" time short to test that we never go below that
    # run for a lot more than max samples
    for _ in range(0, 2 * restart_monitor.max_samples):
        assert not restart_monitor.excessive()
        restart_monitor.add()
        time.sleep(quick + 0.1)  # always longer than "quick"


if is_main():
    test_restart_monitor_excessive()
    test_restart_monitor_not_excessive()
