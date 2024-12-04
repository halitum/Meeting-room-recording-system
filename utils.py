import pyaudio

def get_device_index(target_name="ReSpeaker 4 Mic Array (UAC1.0)"):
    p = pyaudio.PyAudio()
    device_id = None
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')

    for i in range(num_devices):
        device_info = p.get_device_info_by_host_api_device_index(0, i)
        if device_info.get('maxInputChannels') > 0:
            device_name = device_info.get('name')
            if target_name in device_name:
                device_id = i
                break

    p.terminate()
    return device_id


volume_bar_sheet_css = \
"""
    QProgressBar {
        border: 2px solid grey;
        border-radius: 5px;
        text-align: center;
    }

    QProgressBar::chunk {
        background-color: orange;
        width: 1px;
    }
"""
