"""Tests for audio recording and WAV encoding."""

import struct
import wave
import io

import numpy as np

from oai_whisper.recorder import Recorder
from oai_whisper.constants import SAMPLE_RATE, CHANNELS


class TestEncodeWav:
    """Tests for Recorder._encode_wav static method."""

    def test_valid_wav_header(self):
        """Encoded WAV has correct RIFF/WAVE header."""
        audio = np.array([0, 100, -100, 32767, -32768], dtype=np.int16)
        wav_bytes = Recorder._encode_wav(audio)

        assert wav_bytes[:4] == b"RIFF"
        assert wav_bytes[8:12] == b"WAVE"
        assert wav_bytes[12:16] == b"fmt "
        assert wav_bytes[36:40] == b"data"

    def test_wav_parseable(self):
        """Encoded WAV can be parsed by Python's wave module."""
        audio = np.zeros(SAMPLE_RATE, dtype=np.int16)  # 1 second of silence
        wav_bytes = Recorder._encode_wav(audio)

        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            assert wf.getnchannels() == CHANNELS
            assert wf.getsampwidth() == 2  # 16-bit
            assert wf.getframerate() == SAMPLE_RATE
            assert wf.getnframes() == SAMPLE_RATE

    def test_wav_data_matches_input(self):
        """WAV data section contains the exact input samples."""
        audio = np.array([0, 1000, -1000, 32767, -32768], dtype=np.int16)
        wav_bytes = Recorder._encode_wav(audio)

        with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
            raw = wf.readframes(wf.getnframes())

        recovered = np.frombuffer(raw, dtype=np.int16)
        np.testing.assert_array_equal(recovered, audio)

    def test_wav_file_size(self):
        """WAV file size matches expected: 44-byte header + data."""
        num_samples = 1000
        audio = np.zeros(num_samples, dtype=np.int16)
        wav_bytes = Recorder._encode_wav(audio)

        expected_size = 44 + num_samples * 2  # header + data
        assert len(wav_bytes) == expected_size

    def test_riff_size_field(self):
        """RIFF chunk size field = file_size - 8."""
        audio = np.zeros(500, dtype=np.int16)
        wav_bytes = Recorder._encode_wav(audio)

        riff_size = struct.unpack_from("<I", wav_bytes, 4)[0]
        assert riff_size == len(wav_bytes) - 8


class TestRecorderState:
    """Tests for Recorder start/stop state management."""

    def test_stop_without_start_returns_empty(self):
        """Calling stop() before start() returns empty bytes."""
        recorder = Recorder()
        assert recorder.stop() == b""

    def test_initial_rms_is_zero(self):
        """RMS level is 0.0 before any recording."""
        recorder = Recorder()
        assert recorder.rms == 0.0

    def test_callback_updates_rms(self):
        """Simulating audio callback updates the RMS level."""
        recorder = Recorder()
        # Simulate a loud signal
        loud = np.full((1024, 1), 16384, dtype=np.int16)
        recorder._callback(loud, 1024, None, None)
        assert recorder.rms > 0.0

    def test_callback_appends_frames(self):
        """Audio callback appends frames to internal buffer."""
        recorder = Recorder()
        frame = np.zeros((512, 1), dtype=np.int16)
        recorder._callback(frame, 512, None, None)
        recorder._callback(frame, 512, None, None)
        assert len(recorder._frames) == 2

    def test_rms_clamped_to_one(self):
        """RMS is clamped to 1.0 even with max-amplitude signal."""
        recorder = Recorder()
        max_signal = np.full((1024, 1), 32767, dtype=np.int16)
        recorder._callback(max_signal, 1024, None, None)
        assert recorder.rms <= 1.0
