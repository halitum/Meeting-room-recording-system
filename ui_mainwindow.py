import time
import numpy as np
import pyqtgraph as pg

from PyQt5 import QtCore, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from audio_processor import AudioProcessor
from constants import RADIUS
from utils import volume_bar_sheet_css



class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Real-time Audio Direction Visualization")
        self.resize(1400, 800)

        self.processor = None  # 稍后启动时创建
        self.init_ui_controls()
        self.show()

    def init_ui_controls(self):
        self.main_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QtWidgets.QHBoxLayout(self.main_widget)

        # 左侧布局
        self.left_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.left_layout, 1)

        self.info_layout = QtWidgets.QVBoxLayout()
        self.left_layout.addLayout(self.info_layout)

        # 水平音量条
        self.volume_bar = QtWidgets.QProgressBar()
        self.volume_bar.setOrientation(QtCore.Qt.Horizontal)
        self.volume_bar.setMinimum(0)
        self.volume_bar.setMaximum(100)
        self.volume_bar.setTextVisible(False)
        self.volume_bar.setStyleSheet(volume_bar_sheet_css)
        self.info_layout.addWidget(self.volume_bar)

        # 滑条 用于控制 volume_offset
        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume_label = QtWidgets.QLabel("Volume Offset: 60")
        self.volume_slider.setMinimum(20)
        self.volume_slider.setMaximum(120)
        self.volume_slider.setValue(60)
        self.volume_offset = 60
        self.volume_slider.valueChanged.connect(self.update_volume_offset)
        self.volume_slider.valueChanged.connect(lambda value: self.volume_label.setText(f"Volume Offset: {value}"))
        self.info_layout.insertWidget(0, self.volume_label)
        self.info_layout.insertWidget(1, self.volume_slider)

        # 文本显示
        self.text_display = QtWidgets.QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setMaximumHeight(100)
        self.info_layout.addWidget(self.text_display)

        # 方向指示图
        self.direction_plot = pg.PlotWidget()
        self.direction_plot.setAspectLocked(True)
        self.direction_plot.hideAxis('left')
        self.direction_plot.hideAxis('bottom')
        self.left_layout.addWidget(self.direction_plot, 1)

        # 绘制圆形和角度线
        angle_lines = []
        for angle in range(0, 360, 30):
            x = [0, RADIUS * np.cos(np.radians(angle))]
            y = [0, RADIUS * np.sin(np.radians(angle))]
            line = pg.PlotDataItem(x, y, pen=pg.mkPen(color=(200, 200, 200), style=QtCore.Qt.DashLine))
            self.direction_plot.addItem(line)
            angle_lines.append(line)
            # 添加角度文本
            text = pg.TextItem(f"{angle}°", anchor=(0.5, -0.5))
            text.setPos(x[1], y[1])
            self.direction_plot.addItem(text)

        # 绘制外圈
        theta = np.linspace(0, 2 * np.pi, 360)
        x_circle = RADIUS * np.cos(theta)
        y_circle = RADIUS * np.sin(theta)
        circle_line = pg.PlotDataItem(x_circle, y_circle, pen=pg.mkPen(color=(200, 200, 200)))
        self.direction_plot.addItem(circle_line)

        # 添加指示点
        self.direction_point = pg.ScatterPlotItem(pen=pg.mkPen(width=5, color='deepskyblue'), size=15)
        self.direction_plot.addItem(self.direction_point)

        # 右侧布局
        self.right_layout = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.right_layout, 3)

        # 水平布局，用于存放算法选择和启动/停止按钮
        self.button_layout = QtWidgets.QHBoxLayout()
        self.left_layout.insertLayout(0, self.button_layout)

        # 算法选择下拉菜单
        self.method_select = QtWidgets.QComboBox()
        self.method_select.addItems(["NormMUSIC", "MUSIC", "TOPS", "CSSM", "SRP"])
        self.button_layout.addWidget(self.method_select)

        # 启动和停止按钮
        self.start_button = QtWidgets.QPushButton("Start Processing")
        self.start_button.clicked.connect(self.start_audio_processor)
        self.button_layout.addWidget(self.start_button)

        self.stop_button = QtWidgets.QPushButton("Stop Processing")
        self.stop_button.clicked.connect(self.stop_audio_processor)
        self.stop_button.setEnabled(False)
        self.button_layout.addWidget(self.stop_button)

        # 方向-时间图
        self.init_matplotlib_canvas()

        # 存储历史数据
        self.history_x = []
        self.history_y = []
        self.history_time = []
        self.history_alpha = []
        self.start_time = time.time()

    def init_matplotlib_canvas(self):
        # 创建 Matplotlib Figure
        self.fig = Figure()
        self.canvas = FigureCanvas(self.fig)
        self.right_inner_layout = QtWidgets.QHBoxLayout()
        self.right_inner_layout.addWidget(self.canvas)

        # 日志文字框
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.log_display.setFixedWidth(400)
        self.right_inner_layout.addWidget(self.log_display)
        self.right_layout.addLayout(self.right_inner_layout)

        # 创建 3D 子图
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_title("Direction Over Time")
        self.ax.set_xlabel("")
        self.ax.set_ylabel("")
        self.ax.set_zlabel("Time (s)")

        # 初始化散点图
        self.history_scatter = self.ax.scatter([], [], [], c='blue', alpha=0.8)

        # 调整视角
        self.ax.view_init(elev=20, azim=-60)

        # 设置坐标轴范围
        self.ax.set_xlim(-1.2 * RADIUS, 1.2 * RADIUS)
        self.ax.set_ylim(-1.2 * RADIUS, 1.2 * RADIUS)
        self.ax.set_zlim(0, 10)
        self.ax.invert_zaxis()

    def start_audio_processor(self):
        # 获取用户选择的算法
        selected_method = self.method_select.currentText()

        # 启动 AudioProcessor 并传递所选算法
        self.processor = AudioProcessor(selected_method, self.volume_offset)
        self.processor.angle_updated.connect(self.update_plots)
        self.processor.start()

        # 禁用启动按钮并启用停止按钮
        self.start_button.setEnabled(False)
        self.volume_slider.setEnabled(False)
        self.method_select.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_audio_processor(self):
        if self.processor:
            self.processor.stop()
        
        # 启用滑条和方法选择
        self.volume_slider.setEnabled(True)
        self.method_select.setEnabled(True)

        # 启用启动按钮并禁用停止按钮
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_volume_offset(self, value):
        self.volume_offset = value

    def update_plots(self, theta_deg, decibels):
        # 更新音量条
        volume_level = (decibels - self.volume_offset) / 40 * 100
        volume_level = np.clip(volume_level, 0, 100)
        self.volume_bar.setValue(int(volume_level))

        # 更新文本显示
        text_content = f"Sound Level: {decibels:.2f} dB\n"
        if theta_deg is not None:
            text_content += f"Estimated Angle: {theta_deg:.2f}°\n"
            log_entry = f"[{time.strftime('%H:%M:%S')}] - Estimated Angle: {theta_deg:.2f}°"
            self.log_display.append(log_entry)
        else:
            text_content += "Estimated Angle: N/A\n"
        self.text_display.setPlainText(text_content)

        current_time = time.time() - self.start_time

        if theta_deg is not None:
            theta_deg = ((theta_deg + 180) % 360) - 180
            theta_plot = np.radians(90 - theta_deg)
            x = RADIUS * 0.7 * np.cos(theta_plot)
            y = RADIUS * 0.7 * np.sin(theta_plot)
            self.direction_point.setData([x], [y])

            self.history_x.append(x)
            self.history_y.append(y)
            self.history_time.append(current_time)
            self.history_alpha.append(1.0)
        else:
            self.direction_point.setData([], [])

            corner_x = RADIUS
            corner_y = RADIUS
            self.history_x.append(corner_x)
            self.history_y.append(corner_y)
            self.history_time.append(current_time)
            self.history_alpha.append(0.0)

        valid_indices = [i for i, t in enumerate(self.history_time) if current_time - t <= 10]
        self.history_x = [self.history_x[i] for i in valid_indices]
        self.history_y = [self.history_y[i] for i in valid_indices]
        self.history_time = [self.history_time[i] for i in valid_indices]
        self.history_alpha = [self.history_alpha[i] for i in valid_indices]

        self.history_alpha = [max(0.0, alpha - 0.01) for alpha in self.history_alpha]

        if self.history_scatter:
            self.history_scatter.remove()

        colors = [(0, 0, 1, alpha) for alpha in self.history_alpha]
        self.history_scatter = self.ax.scatter(self.history_x, self.history_y, self.history_time, c=colors)

        self.ax.set_xlim(-1.2 * RADIUS, 1.2 * RADIUS)
        self.ax.set_ylim(-1.2 * RADIUS, 1.2 * RADIUS)
        self.ax.set_zlim(current_time - 10, current_time)

        self.canvas.draw_idle()

    def closeEvent(self, event):
        if self.processor:
            self.processor.stop()
        super().closeEvent(event)