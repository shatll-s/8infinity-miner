import time


class SpeedSamplerMixin:
    SPEED_SAMPLER_NUM_SAMPLES = 20

    def _speed_sample(self, n):
        if not hasattr(self, "_speed_sampler_last_time"):
            self._speed_sampler_last_time = time.monotonic()
            self._speed_sampler_samples = []
            return

        timedelta = time.monotonic() - self._speed_sampler_last_time
        self._speed_sampler_samples.append(n / timedelta)
        self._speed_sampler_samples = self._speed_sampler_samples[
            -self.SPEED_SAMPLER_NUM_SAMPLES :
        ]
        self._speed_sampler_last_time = time.monotonic()

    def speed(self) -> float:
        if (
            not hasattr(self, "_speed_sampler_samples")
            or len(self._speed_sampler_samples) == 0
        ):
            return 0.0
        return sum(self._speed_sampler_samples) / len(self._speed_sampler_samples)
