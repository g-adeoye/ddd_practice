import pytest
from schemas.job import JobCreate, WeightUpdateRequest
from pydantic import ValidationError


class TestJobCreatePriorityEnums:
    def test_priority_is_uppercase(self):
        job_create = JobCreate(
            payload=dict(),
            priority="normal",  # type: ignore
        )

        assert job_create.priority == "NORMAL"

    def test_invalid_priortiy_types(self):

        with pytest.raises(ValidationError):
            JobCreate(payload={}, priority="LOW")  # type: ignore


class TestWeightUpdateRequest:
    def test_value_error_is_raised_for_negative_critical_weights(self):
        with pytest.raises(ValueError, match="Weight must be non-negative"):
            WeightUpdateRequest(critical=-10, high=20, normal=80)
        with pytest.raises(ValueError):
            WeightUpdateRequest(critical=10, high=-20, normal=80)
        with pytest.raises(ValueError):
            WeightUpdateRequest(critical=10, high=20, normal=-80)

    def test_sum_of_weights_must_equal_100(self):
        weight_update_request = WeightUpdateRequest(critical=60, high=30, normal=10)
        assert sum(
            [
                weight_update_request.critical,
                weight_update_request.high,
                weight_update_request.normal,
            ]
        )

    def test_sum_of_weights_not_equal_100(self):
        with pytest.raises(ValueError):
            WeightUpdateRequest(critical=60, high=30, normal=20)
