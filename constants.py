import numpy as np

RESPEAKER_RATE = fs = 16000
RESPEAKER_CHANNELS = 6
USED_CHANNELS = 4
CHUNK = 1024
SEG_LEN = 500
OVERLAP = 50
SOUND_V = 343
RADIUS = 3
MIC_POSITIONS = np.array(
    [[0.045, 0, 0],
     [0.045, 0.045, 0],
     [0, 0.045, 0],
     [0, 0, 0]]).T

nfft = 256  # FFT 长度