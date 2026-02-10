"""Audio recording via sounddevice (24kHz mono PCM)."""

import io
import struct
import threading

import numpy as np
import sounddevice as sd

from .constants import CHANNELS, DTYPE, SAMPLE_RATE


class Recorder:
    def __init__(self):
        self._frames: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            self._frames = []
            self._stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=self._callback,
            )
            self._stream.start()

    def stop(self) -> bytes:
        """Stop recording and return WAV bytes."""
        with self._lock:
            if self._stream is not None:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            frames = self._frames
            self._frames = []
        if not frames:
            return b""
        audio = np.concatenate(frames)
        return self._encode_wav(audio)

    def _callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        with self._lock:
            self._frames.append(indata.copy())

    @staticmethod
    def _encode_wav(audio: np.ndarray) -> bytes:
        """Encode int16 numpy array to WAV bytes."""
        buf = io.BytesIO()
        num_samples = len(audio)
        data_size = num_samples * 2  # 16-bit = 2 bytes per sample

        # WAV header
        buf.write(b"RIFF")
        buf.write(struct.pack("<I", 36 + data_size))
        buf.write(b"WAVE")
        buf.write(b"fmt ")
        buf.write(struct.pack("<I", 16))          # chunk size
        buf.write(struct.pack("<H", 1))            # PCM format
        buf.write(struct.pack("<H", CHANNELS))
        buf.write(struct.pack("<I", SAMPLE_RATE))
        buf.write(struct.pack("<I", SAMPLE_RATE * CHANNELS * 2))  # byte rate
        buf.write(struct.pack("<H", CHANNELS * 2))  # block align
        buf.write(struct.pack("<H", 16))            # bits per sample
        buf.write(b"data")
        buf.write(struct.pack("<I", data_size))
        buf.write(audio.tobytes())

        return buf.getvalue()
