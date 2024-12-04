import numpy as np
import pyroomacoustics as pra
from constants import MIC_POSITIONS, fs, nfft, SOUND_V

def doa_estimation(cor_data, method='NormMUSIC'):
    """
    通用的 DOA 估计函数，支持多种算法

    参数：
    - cor_data: 输入的麦克风数据，形状为 (num_samples, num_channels)
    - method: 算法名称，支持 'MUSIC', 'FRIDA', 'WAVES', 'TOPS', 'CSSM', 'SRP', 'NormMUSIC'

    返回：
    - azimuth: 估计的方位角（弧度制）
    """
    # 数据预处理
    data_array = np.array(cor_data).T  # 转换为 numpy 数组，并转置为 (num_channels, num_samples)
    X = pra.transform.stft.analysis(
        data_array, nfft, nfft // 2, win=np.hanning(nfft)
    )  # STFT 分析
    X = np.swapaxes(X, 2, 0)  # 调整形状为 (n_freq_bins, n_frames, num_channels)

    # 执行 DOA 估计
    doa = pra.doa.algorithms[method](
        MIC_POSITIONS, fs, nfft, c=SOUND_V, num_src=1
    )
    doa.locate_sources(X)

    return doa.azimuth_recon[0]





"""
FRIDA报错：
F:\ProgramFiles\miniconda3\envs\4mic-tdoa\lib\site-packages\pyroomacoustics\doa\tools_fri_doa_plane.py:927: LinAlgWarning: Ill-conditioned matrix (rcond=3.0366e-42): result may not be accurate.
  c_ri_half = linalg.solve(mtx_loop, rhs, check_finite=False)[:sz_coef]
F:\ProgramFiles\miniconda3\envs\4mic-tdoa\lib\site-packages\pyroomacoustics\doa\tools_fri_doa_plane.py:927: LinAlgWarning: Ill-conditioned matrix (rcond=3.03662e-42): result may not be accurate.
  c_ri_half = linalg.solve(mtx_loop, rhs, check_finite=False)[:sz_coef]
F:\ProgramFiles\miniconda3\envs\4mic-tdoa\lib\site-packages\pyroomacoustics\doa\tools_fri_doa_plane.py:927: LinAlgWarning: Ill-conditioned matrix (rcond=3.03663e-42): result may not be accurate.
  c_ri_half = linalg.solve(mtx_loop, rhs, check_finite=False)[:sz_coef]
F:\ProgramFiles\miniconda3\envs\4mic-tdoa\lib\site-packages\pyroomacoustics\doa\tools_fri_doa_plane.py:927: LinAlgWarning: Ill-conditioned matrix (rcond=3.03664e-42): result may not be accurate.
  c_ri_half = linalg.solve(mtx_loop, rhs, check_finite=False)[:sz_coef]
Estimated Angle: 224.14°

WAVES问题：
效率太低
"""
