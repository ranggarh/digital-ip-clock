import tkinter as tk
import socket
import datetime
import threading
import time
import pickle
import os
import sys
from concurrent.futures import ThreadPoolExecutor


def resource_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, filename)

IP_LIST_FILE = "ip_list.pkl"

# Warna perusahaan
COLOR_RED = "#D9252A"
COLOR_GREEN = "#8CC63F"
COLOR_WHITE = "#FFFFFF"

class NP301SyncTool:
    def __init__(self, root):
        self.root = root
        icon_path = resource_path("assets/favicon.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
        self.root.title("Digital IP Clock By Puterako")
        self.root.geometry("600x450")
        self.root.configure(bg=COLOR_WHITE)

        # ===== IP List =====
        self.ip_list = self.load_ip_list()
        self.port = 1001

        # ===== Current Time Display =====
        self.time_label = tk.Label(root, text="", font=("Consolas", 28, "bold"),
                                   fg=COLOR_RED, bg=COLOR_WHITE)
        self.time_label.pack(pady=10)
        self.update_clock()

        # ===== IP & Port Input =====
        input_frame = tk.Frame(root, bg=COLOR_WHITE)
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="IP Device:", font=("Arial", 12, "bold"),
                 fg=COLOR_GREEN, bg=COLOR_WHITE).pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(input_frame, font=("Arial", 14), width=15, fg=COLOR_RED)
        self.ip_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(input_frame, text="Port:", font=("Arial", 12, "bold"),
                 fg=COLOR_GREEN, bg=COLOR_WHITE).pack(side=tk.LEFT)
        self.port_entry = tk.Entry(input_frame, font=("Arial", 14), width=6, fg=COLOR_RED)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, str(self.port))

        tk.Button(input_frame, text="Tambah IP", command=self.add_ip,
                  bg=COLOR_GREEN, fg="white", width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(input_frame, text="Hapus IP", command=self.delete_ip,
                  bg=COLOR_RED, fg="white", width=10).pack(side=tk.LEFT, padx=5)

        # ===== Listbox IP =====
        self.ip_listbox = tk.Listbox(root, font=("Consolas", 12), height=5,
                                     selectmode=tk.SINGLE, bg=COLOR_WHITE)
        self.ip_listbox.pack(fill=tk.X, padx=10)
        self.refresh_ip_listbox()

        # ===== Log Area =====
        self.log_text = tk.Text(root, height=12, bg=COLOR_WHITE, fg="black", font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, padx=10, pady=10)

        self.live_running = False
        self.toggle_live()

    def load_ip_list(self):
        local_file = os.path.join(os.getcwd(), IP_LIST_FILE)
        if os.path.exists(local_file):
            try:
                with open(local_file, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return ["192.168.2.246"]
        ip_file_path = resource_path(IP_LIST_FILE)
        if os.path.exists(ip_file_path):
            try:
                with open(ip_file_path, "rb") as f:
                    return pickle.load(f)
            except Exception:
                return ["192.168.2.246"]
        return ["192.168.2.246"]

    def save_ip_list(self):
        local_file = os.path.join(os.getcwd(), IP_LIST_FILE)
        with open(local_file, "wb") as f:
            pickle.dump(self.ip_list, f)

    def update_clock(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def log(self, msg):
        self.root.after(0, lambda: self._append_log(msg))

    def _append_log(self, msg):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{now}] : {msg}\n")
        self.log_text.see(tk.END)

    def refresh_ip_listbox(self):
        self.ip_listbox.delete(0, tk.END)
        for ip in self.ip_list:
            self.ip_listbox.insert(tk.END, ip)

    def add_ip(self):
        ip = self.ip_entry.get().strip()
        if ip and ip not in self.ip_list:
            self.ip_list.append(ip)
            self.save_ip_list()
            self.refresh_ip_listbox()
            self.log(f"IP {ip} ditambahkan.")
        else:
            self.log("IP sudah ada atau kosong.")

    def delete_ip(self):
        selected = self.ip_listbox.curselection()
        if selected:
            ip = self.ip_listbox.get(selected[0])
            self.ip_list.remove(ip)
            self.save_ip_list()
            self.refresh_ip_listbox()
            self.log(f"IP {ip} dihapus.")
        else:
            self.log("Pilih IP yang mau dihapus di list.")

    def get_port(self):
        return int(self.port_entry.get().strip())

    def build_time_string(self):
        now = datetime.datetime.now()
        if now.second % 2 == 0:
            timestr = now.strftime("%H:%M:%S")
        else:
            timestr = now.strftime("%H %M %S")
        return timestr + "\r"

    def send_time_to_ip(self, ip, port, msg):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                s.connect((ip, port))
                s.sendall(msg.encode("latin1"))
        except Exception:
            pass

    def live_worker(self):
        executor = ThreadPoolExecutor(max_workers=min(50, len(self.ip_list) + 10))
        
        # Sinkronisasi awal ke detik genap
        while datetime.datetime.now().microsecond > 100000:
            time.sleep(0.01)
        
        next_tick = time.time() + 1.0
        
        try:
            while self.live_running:
                # Hitung waktu target berikutnya (setiap detik genap)
                current = time.time()
                
                # Kirim ke semua device secara parallel (fire and forget)
                msg = self.build_time_string()
                port = self.get_port()
                
                for ip in self.ip_list:
                    executor.submit(self.send_time_to_ip, ip, port, msg)
                
                # Tunggu hingga tepat 1 detik berikutnya tanpa menunggu hasil
                next_tick += 1.0
                sleep_time = next_tick - time.time()
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # Jika terlambat, reset ke tick berikutnya
                    next_tick = time.time() + 1.0
                    
        finally:
            executor.shutdown(wait=False)

    def toggle_live(self):
        if not self.live_running:
            self.live_running = True
            threading.Thread(target=self.live_worker, daemon=True).start()
            self.log("Live sync dimulai")
        else:
            self.live_running = False
            self.log("Live sync dihentikan")

if __name__ == "__main__":
    root = tk.Tk()
    app = NP301SyncTool(root)
    root.mainloop()