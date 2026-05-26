from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt

class HUDWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Frameless, Always on Top, Click-Through
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.WindowTransparentForInput |
            Qt.WindowType.Tool
        )
        
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.central_widget = QWidget()
        self.central_widget.setObjectName("HudContainer")
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(15, 12, 15, 12)
        self.layout.setSpacing(6)

        # Header: Clock & Pomodoro
        header_layout = QHBoxLayout()
        self.time_label = QLabel("--:--:--")
        self.time_label.setObjectName("ClockLabel")
        
        self.pomodoro_label = QLabel("Work: 25:00")
        self.pomodoro_label.setObjectName("DataLabel")
        
        header_layout.addWidget(self.time_label)
        header_layout.addStretch()
        header_layout.addWidget(self.pomodoro_label)
        self.layout.addLayout(header_layout)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("Separator")
        self.layout.addWidget(line)

        # System Metrics
        self.cpu_label = QLabel("CPU: --%")
        self.cpu_label.setObjectName("DataLabel")
        
        self.ram_label = QLabel("RAM: --% (--/-- GB)")
        self.ram_label.setObjectName("DataLabel")

        self.gpu_label = QLabel("GPU: --% (--/-- GB)")
        self.gpu_label.setObjectName("DataLabel")
        self.gpu_label.hide()

        self.layout.addWidget(self.cpu_label)
        self.layout.addWidget(self.ram_label)
        self.layout.addWidget(self.gpu_label)

        # Network Section
        self.ping_label = QLabel("Ping: -- ms")
        self.ping_label.setObjectName("DataLabel")

        self.net_layout = QHBoxLayout()
        self.net_layout.setSpacing(10)
        self.down_label = QLabel("↓ --")
        self.down_label.setObjectName("NetLabel")
        self.up_label = QLabel("↑ --")
        self.up_label.setObjectName("NetLabel")
        self.net_layout.addWidget(self.down_label)
        self.net_layout.addWidget(self.up_label)

        self.layout.addWidget(self.ping_label)
        self.layout.addLayout(self.net_layout)

        # Processes Section
        self.proc_title = QLabel("Top RAM Consumers:")
        self.proc_title.setObjectName("SmallHeader")
        self.layout.addWidget(self.proc_title)
        
        self.proc_labels = []
        for _ in range(3):
            lbl = QLabel("-")
            lbl.setObjectName("ProcLabel")
            self.proc_labels.append(lbl)
            self.layout.addWidget(lbl)

        # Health Alert
        self.health_label = QLabel("⚠️ MOLA ZAMANI!")
        self.health_label.setObjectName("AlertLabel")
        self.health_label.hide()
        self.layout.addWidget(self.health_label)

        # Size and placement
        self.resize(250, 280)
        self.move_to_corner()

    def move_to_corner(self):
        screen = self.screen().availableGeometry()
        x = screen.width() - self.width() - 20
        y = 20
        self.move(x, y)

    def update_stats(self, data):
        self.time_label.setText(data['time'])
        self.pomodoro_label.setText(data['pomodoro'])
        
        self.cpu_label.setText(f"CPU: {data['cpu_percent']:.1f}%")
        self.ram_label.setText(f"RAM: {data['ram_percent']:.1f}% ({data['ram_used_gb']}/{data['ram_total_gb']} GB)")
        
        if data.get('gpu'):
            gpu = data['gpu']
            self.gpu_label.setText(f"GPU: {gpu['load']}% ({gpu['mem_used']}/{gpu['mem_total']} GB)")
            self.gpu_label.show()
        else:
            self.gpu_label.hide()

        self.ping_label.setText(f"Ping: {data['ping']} ms" if data['ping'] >= 0 else "Ping: Error")
        self.down_label.setText(f"↓ {data['down_speed']}")
        self.up_label.setText(f"↑ {data['up_speed']}")

        # Processes
        for i, proc in enumerate(data['top_procs']):
            if i < len(self.proc_labels):
                self.proc_labels[i].setText(f"{proc['name'][:15]}: {proc['memory_percent']:.1f}%")
        
        # Health Alert
        if data['health_alert']:
            self.health_label.show()
        else:
            self.health_label.hide()
        
        # Auto-adjust height
        self.adjustSize()
