import time


class SpeedSamplerMixin:
    SPEED_SAMPLER_NUM_SAMPLES = 20

    def _speed_sample(self, n):
        if not hasattr(self, "_speed_sample_num_iterations") or not hasattr(
            self, "_speed_sampler_start_time"
        ):
            raise RuntimeError("Run _reset_speed first!")

        self._speed_sample_num_iterations += n

    def _reset_speed(self):
        self._speed_sample_num_iterations = 0
        self._speed_sampler_start_time = time.monotonic()

    def speed(self) -> float:
        if not hasattr(self, "_speed_sample_num_iterations"):
            return 0.0
        return self._speed_sample_num_iterations / (
            time.monotonic() - self._speed_sampler_start_time
        )
