import psutil
import time
import socket
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import pynvml
    HAS_NVML = True
except ImportError:
    HAS_NVML = False

class SystemStatsWorker(QThread):
    stats_updated = pyqtSignal(dict)

    def __init__(self, update_interval=1.0):
        super().__init__()
        self.update_interval = update_interval
        self._is_running = True
        self.last_net_io = psutil.net_io_counters()
        
        # Pomodoro variables
        self.pomodoro_mode = "Work" # Work or Break
        self.pomodoro_time_left = 25 * 60
        self.last_pomodoro_update = time.time()

        # Health reminder (3 hours)
        self.session_start_time = time.time()
        
        self.has_gpu = False
        if HAS_NVML:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
                if self.gpu_count > 0:
                    self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    self.has_gpu = True
            except Exception:
                self.has_gpu = False

    def get_ping(self, host="8.8.8.8", port=53, timeout=1):
        try:
            start = time.perf_counter()
            socket.setdefaulttimeout(timeout)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            return int((time.perf_counter() - start) * 1000)
        except Exception:
            return -1

    def get_top_processes(self, count=3):
        processes = []
        for proc in psutil.process_iter(['name', 'memory_percent']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        return processes[:count]

    def update_pomodoro(self):
        now = time.time()
        elapsed = now - self.last_pomodoro_update
        self.last_pomodoro_update = now
        
        self.pomodoro_time_left -= elapsed
        if self.pomodoro_time_left <= 0:
            if self.pomodoro_mode == "Work":
                self.pomodoro_mode = "Break"
                self.pomodoro_time_left = 5 * 60
            else:
                self.pomodoro_mode = "Work"
                self.pomodoro_time_left = 25 * 60

    def run(self):
        while self._is_running:
            try:
                # Digital Clock
                current_time = datetime.now().strftime("%H:%M:%S")

                # CPU and RAM
                cpu_usage = psutil.cpu_percent(interval=None)
                ram_info = psutil.virtual_memory()
                
                # Network speeds
                current_net_io = psutil.net_io_counters()
                download_speed = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / self.update_interval
                upload_speed = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / self.update_interval
                self.last_net_io = current_net_io

                # Ping
                ping = self.get_ping()

                # GPU Stats
                gpu_data = None
                if self.has_gpu:
                    try:
                        util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
                        temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
                        mem = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
                        gpu_data = {
                            "load": util.gpu,
                            "temp": temp,
                            "mem_used": round(mem.used / (1024**3), 2),
                            "mem_total": round(mem.total / (1024**3), 2)
                        }
                    except Exception:
                        gpu_data = None
                
                # Top Processes
                top_procs = self.get_top_processes()

                # Pomodoro
                self.update_pomodoro()
                mins, secs = divmod(int(self.pomodoro_time_left), 60)
                pomodoro_str = f"{self.pomodoro_mode}: {mins:02d}:{secs:02d}"

                # Health Reminder
                session_duration = time.time() - self.session_start_time
                health_alert = session_duration > (3 * 3600) # 3 hours

                data = {
                    "time": current_time,
                    "cpu_percent": cpu_usage,
                    "ram_percent": ram_info.percent,
                    "ram_used_gb": round(ram_info.used / (1024**3), 2),
                    "ram_total_gb": round(ram_info.total / (1024**3), 2),
                    "down_speed": self.format_bytes(download_speed),
                    "up_speed": self.format_bytes(upload_speed),
                    "ping": ping,
                    "gpu": gpu_data,
                    "top_procs": top_procs,
                    "pomodoro": pomodoro_str,
                    "health_alert": health_alert
                }
                
                self.stats_updated.emit(data)
                
            except Exception as e:
                print(f"Worker Error: {e}")
                
            time.sleep(self.update_interval)

    def format_bytes(self, n):
        for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB/s"

    def stop(self):
        if HAS_NVML and self.has_gpu:
            try:
                pynvml.nvmlShutdown()
            except Exception:
                pass
        self._is_running = False
        self.wait()
