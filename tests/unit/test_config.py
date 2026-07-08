from app.config import Settings, get_settings
import pytest


@pytest.fixture
def settings() -> Settings:
    return get_settings()


class TestAppConfigSettings:
    def test_priority_weights_sum_up_to_100(self, settings: Settings) -> None:
        assert (
            sum(
                [settings.weight_critical, settings.weight_high, settings.weight_normal]
            )
            == 100
        )

    def test_high_watermark_is_greater_than_low_watermark(
        self, settings: Settings
    ) -> None:
        assert isinstance(settings.high_watermark, int)
        assert isinstance(settings.low_watermark, int)
        assert settings.high_watermark > settings.low_watermark
