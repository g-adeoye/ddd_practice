from collections import Counter

from services.scheduler import pick_queue


def test_pick_queue_respects_weights(queue_weights):
    """
    Over 10,000 picks the distribution must match weights within 5%.
    This proves the algorithm works
    """
    
    results = Counter(pick_queue(queue_weights) for _ in range(10_000))
    
    critical_pct = results["queue:critical"] / 10_000 * 100
    high_pct = results["queue:high"] / 10_000 * 100
    normal_pct = results["queue:normal"] / 10_000 * 100
    
    assert abs(critical_pct - 60) < 5, f"Critical: {critical_pct:.1f}%"
    assert abs(high_pct - 30) < 5, f"High: {high_pct:.1f}%"
    assert abs(normal_pct - 10) < 5, f"Normal: {normal_pct:.1f}%"
    

def test_pick_queue_always_returns_valid_streams(queue_weights):
    "Every pick must return one of the three known stream names."
    valid = {
        "queue:critical",
        "queue:high",
        "queue:normal",
    }
    
    for _ in range(1_000):
        result = pick_queue(queue_weights)
        assert result in valid
        
def test_pick_queue_skewed_weights():
    "With 100% weight on one queue, it must always be selected."
    weights = {"critical": 100, "high": 0, "normal": 0}
    
    results = Counter(pick_queue(weights) for _ in range(10_000))
    assert results["queue:critical"] / 10_000 == 1