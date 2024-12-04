import logging
import threading
import time
import numpy as np
import pyaudio
from PyQt5 import QtCore
from utils import get_device_index
from doa_method import doa_estimation
from constants import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("./log/audio_processor.log"),
        logging.StreamHandler()
    ]
)

class AudioProcessor(QtCore.QObject):
    angle_updated = QtCore.pyqtSignal(object, float)

    def __init__(self, method, volume_offset):
        super().__init__()
        self.method = method
        self.volume_offset = volume_offset

        RESPEAKER_INDEX = get_device_index()
        if RESPEAKER_INDEX is None:
            raise ValueError("No ReSpeaker Mic Array found!")

        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            rate=RESPEAKER_RATE, format=pyaudio.paInt16,
            channels=RESPEAKER_CHANNELS, input=True,
            input_device_index=RESPEAKER_INDEX,
            frames_per_buffer=CHUNK
            )
        self.running = True
        self.audio_data = [[] for _ in range(USED_CHANNELS)]

    def start(self):
        self.thread = threading.Thread(target=self.process_audio)
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def process_audio(self):
        while self.running:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            audio_chunk = np.frombuffer(data, dtype=np.int16)

            # 抽取每个麦克风通道的数据
            for i in range(USED_CHANNELS):
                self.audio_data[i].extend(audio_chunk[i + 1::RESPEAKER_CHANNELS])

            if len(self.audio_data[0]) > SEG_LEN * 2:
                cor_data = [data[:SEG_LEN * 2] for data in self.audio_data]
                self.audio_data = [data[-OVERLAP:] for data in self.audio_data]

                # 计算声音的分贝，使用第一个麦克风通道的数据
                mic_data = np.array(audio_chunk[1::RESPEAKER_CHANNELS], dtype=np.float32)
                rms = np.sqrt(np.mean(np.square(mic_data)))
                decibels = 20 * np.log10(max(rms, 1e-6))

                # 如果音量大于等于 VOLUMN_OFFSET dB，才进行角度估计
                if decibels >= self.volume_offset:
                    theta = doa_estimation(cor_data, method=self.method)
                    theta_deg = (450 - np.degrees(theta)) % 360

                    print(f"Estimated Angle: {theta_deg:.2f}°")
                else:
                    theta_deg = None

                # 发射信号，传递角度和音量
                self.angle_updated.emit(theta_deg, decibels)
            else:
                time.sleep(0.01)