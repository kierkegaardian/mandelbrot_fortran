from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from app import fractal_renderer
from app.fractal_renderer import FractalConfig, RenderCancelled


class FakePipe:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FractalRendererStackTests(unittest.TestCase):
    def _config(self) -> FractalConfig:
        return FractalConfig(
            width=320,
            height=200,
            max_iter=120,
            center_x=-0.5,
            center_y=0.0,
            zoom=1.0,
            fractal_type="mandelbrot",
            palette="rgb",
            freq=0.1,
            power=2.0,
            julia_cx=-0.8,
            julia_cy=0.156,
            smooth=True,
            cyclic=False,
            threads=1,
        )

    def test_render_ppm_uses_temp_output_not_dev_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            fake_bin = Path(td) / "mandelbrot_gen"
            fake_bin.write_text("", encoding="utf-8")
            cfg = self._config()

            captured_args: list[str] = []

            def fake_run(args: list[str], cancel_event: Event | None, timeout_seconds: float) -> None:
                del cancel_event, timeout_seconds
                captured_args.extend(args)
                out_idx = args.index("--output") + 1
                Path(args[out_idx]).write_bytes(b"P6\n1 1\n255\n\x00\x00\x00")

            with patch.object(fractal_renderer, "mandelbrot_binary", return_value=fake_bin), patch.object(
                fractal_renderer, "_run_with_cancel", side_effect=fake_run
            ):
                data = fractal_renderer.render_ppm(cfg)

            self.assertIn("--output", captured_args)
            self.assertNotIn("/dev/stdout", captured_args)
            self.assertTrue(data.startswith(b"P6"))

    def test_run_with_cancel_raises_when_cancelled(self) -> None:
        class FakeProc:
            def __init__(self) -> None:
                self.stdout = FakePipe()
                self.stderr = FakePipe()
                self._killed = False

            def poll(self):
                return None

            def communicate(self, timeout: float):
                del timeout
                return b"", b""

            def kill(self) -> None:
                self._killed = True

            def wait(self, timeout: float) -> int:
                del timeout
                return 0

        cancel = Event()
        cancel.set()
        proc = FakeProc()
        with patch.object(fractal_renderer.subprocess, "Popen", return_value=proc):
            with self.assertRaises(RenderCancelled):
                fractal_renderer._run_with_cancel(["mandelbrot_gen"], cancel_event=cancel, timeout_seconds=1.0)
        self.assertTrue(proc._killed)
        self.assertTrue(proc.stdout.closed)
        self.assertTrue(proc.stderr.closed)

    def test_run_with_cancel_times_out(self) -> None:
        class FakeProc:
            returncode = None

            def __init__(self) -> None:
                self.stdout = FakePipe()
                self.stderr = FakePipe()
                self._killed = False

            def poll(self):
                return None

            def communicate(self, timeout: float):
                raise fractal_renderer.subprocess.TimeoutExpired(cmd="mandelbrot_gen", timeout=timeout)

            def kill(self) -> None:
                self._killed = True

            def wait(self, timeout: float) -> int:
                del timeout
                return 0

        proc = FakeProc()
        with patch.object(fractal_renderer.subprocess, "Popen", return_value=proc):
            with self.assertRaises(TimeoutError):
                fractal_renderer._run_with_cancel(["mandelbrot_gen"], cancel_event=None, timeout_seconds=0.1)
        self.assertTrue(proc._killed)
        self.assertTrue(proc.stdout.closed)
        self.assertTrue(proc.stderr.closed)


if __name__ == "__main__":
    unittest.main()
