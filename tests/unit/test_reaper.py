from services.queue_service import QUEUE_NAMES
from services.reaper_service import VISIBILITY_TIMEOUT_MS


def test_visibility_timeouts_defined_for_all_queues():
    "Every priority queue must have a visibility timeout defined."
    for priority in QUEUE_NAMES:
        assert priority in VISIBILITY_TIMEOUT_MS, (
            f"Missing visibility timeout for priority: {priority!r}"
        )


def test_visibility_timeouts_ordered_correctly():
    """
    Critical must be shortest, normal must be longest.
    """
    assert VISIBILITY_TIMEOUT_MS["critical"] < VISIBILITY_TIMEOUT_MS["high"]
    assert VISIBILITY_TIMEOUT_MS["high"] < VISIBILITY_TIMEOUT_MS["normal"]
