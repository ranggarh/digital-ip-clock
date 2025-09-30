import tkinter as tk
import socket
import datetime
import threading
import time

class NP301SyncTool:
    def __init__(self, root):
        self.root = root
        self.root.title("NP301 TCP/IP Sync Tool")
        self.root.geometry("600x450")
        self.root.configure(bg="black")
        
        # ===== Current Time Display =====
        self.time_label = tk.Label(root, text="", font=("Consolas", 28, "bold"), fg="cyan", bg="black")
        self.time_label.pack(pady=10)

        # update label waktu tiap detik
        self.update_clock()

        # ===== IP & Port =====
        input_frame = tk.Frame(root, bg="black")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="IP:", font=("Arial", 12), fg="lime", bg="black").pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(input_frame, font=("Arial", 14), width=15)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        self.ip_entry.insert(0, "192.168.2.246")

        tk.Label(input_frame, text="Port:", font=("Arial", 12), fg="lime", bg="black").pack(side=tk.LEFT)
        self.port_entry = tk.Entry(input_frame, font=("Arial", 14), width=6)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "1001")

        

        # ===== Buttons =====
        btn_frame = tk.Frame(root, bg="black")
        btn_frame.pack(pady=10)

        self.live_btn = tk.Button(btn_frame, text="Start Live Sync", command=self.toggle_live,
                                  bg="red", fg="white", width=15)
        self.live_btn.pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Test Connection", command=self.test_connection,
                  bg="purple", fg="white", width=15).pack(side=tk.LEFT, padx=5)

        # ===== Log Area =====
        self.log_text = tk.Text(root, height=12, bg="black", fg="white", font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, padx=10, pady=10)

        # ===== Live Sync Flag =====
        self.live_running = False

    def update_clock(self):
        """Update jam real-time di GUI"""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def log(self, msg):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] {msg}\n")
        self.log_text.see(tk.END)

    def get_ip_port(self):
        return self.ip_entry.get().strip(), int(self.port_entry.get().strip())

    def build_time_string(self):
        """Format waktu HH:MM:SS dengan : kedip tiap detik"""
        now = datetime.datetime.now()
        if now.second % 2 == 0:
            # detik genap → ada titik dua
            timestr = now.strftime("%H:%M:%S")
        else:
            # detik ganjil → titik dua hilang (diganti spasi)
            timestr = now.strftime("%H %M %S")
        return timestr + "\r"

    def live_worker(self):
        """Thread buat sync tiap detik"""
        while self.live_running:
            try:
                ip, port = self.get_ip_port()
                msg = self.build_time_string()
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((ip, port))
                    s.send(msg.encode("latin1"))
                self.log(f"Live sync sent: {repr(msg)}")
            except Exception as e:
                self.log(f"Live sync error: {e}")
            time.sleep(1)  # kirim setiap 1 detik

    def toggle_live(self):
        if not self.live_running:
            self.live_running = True
            self.live_btn.config(text="Stop Live Sync", bg="gray")
            threading.Thread(target=self.live_worker, daemon=True).start()
            self.log("Live sync started")
        else:
            self.live_running = False
            self.live_btn.config(text="Start Live Sync", bg="red")
            self.log("Live sync stopped")

    def test_connection(self):
        try:
            ip, port = self.get_ip_port()
            self.log(f"Testing {ip}:{port} ...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((ip, port))
            self.log("Connection OK!")
        except Exception as e:
            self.log(f"Test failed: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = NP301SyncTool(root)
    root.mainloop()