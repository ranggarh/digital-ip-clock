import tkinter as tk
import socket
import datetime
import threading


# Ambil IP Address lokal dari PC
def get_local_ip():
    """Ambil IP Address lokal dari PC."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "0.0.0.0"

# Cek apakah dua IP berada di segmen jaringan yang sama
def check_same_segment(ip1, ip2):
    """Cek apakah IP1 dan IP2 berada di segmen jaringan yang sama (3 oktet pertama)."""
    try:
        seg1 = ".".join(ip1.split(".")[:3])
        seg2 = ".".join(ip2.split(".")[:3])
        return seg1 == seg2
    except Exception:
        return False


# Aplikasi Tkinter GUI
# -----------------------------
class IPClock:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital IP Clock By Puterako")
        self.root.geometry("500x300")
        self.root.configure(bg="black")

        # Label jam digital
        self.clock_label = tk.Label(
            root, text="", font=("Arial", 48, "bold"), fg="lime", bg="black"
        )
        self.clock_label.pack(pady=20)

        # Hardcode IP Device
        # self.device_ip = ["192.168.2.50", "192.168.2.51"]

        # Ip Device Lewat Input
        self.ip_entry = tk.Entry(root, font=("Arial", 14), width=30)
        self.ip_entry.pack(pady=5)

        self.set_ip_btn = tk.Button(
            root, text="Set Device IP(s)", command=self.set_device_ips, bg="gray", fg="white"
        )
        self.set_ip_btn.pack(pady=2)

        self.device_ip = []

        # Tombol check
        self.check_btn = tk.Button(
            root, text="Check & Sync", command=self.check_ip, bg="gray", fg="white"
        )
        self.check_btn.pack(pady=10)
        
        # Log area
        self.log_text = tk.Text(root, height=6, bg="black", fg="white")
        self.log_text.pack(fill=tk.BOTH, padx=10, pady=10)

        # Mulai update clock
        self.update_clock()
    def set_device_ips(self):
        """Ambil IP dari entry, pisahkan dengan koma, dan simpan ke self.device_ip."""
        ip_text = self.ip_entry.get()
        self.device_ip = [ip.strip() for ip in ip_text.split(",") if ip.strip()]
        self.log(f"Daftar IP device di-set: {self.device_ip}")


    def log(self, message):
        """Tulis pesan ke log area."""
        self.log_text.insert(tk.END, f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see(tk.END)

    def update_clock(self):
        """Update tampilan jam digital setiap 1 detik."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def check_ip(self):
        """Cek apakah setiap IP device sama segmen dengan PC, kalau iya lakukan 'sync'."""
        local_ip = get_local_ip()
        self.log(f"Local IP: {local_ip}")
        for device_ip in self.device_ip:
            self.log(f"Device IP: {device_ip}")
            if check_same_segment(local_ip, device_ip):
                self.log(f"✅ IP device {device_ip} sama segmen, siap sync waktu...")
                threading.Thread(target=self.sync_time, args=(device_ip,), daemon=True).start()
            else:
                self.log(f"❌ IP {device_ip} tidak cocok segmen, periksa jaringan!")

    def sync_time(self, device_ip):
        """Kirim waktu ke device via socket TCP port 12345 (contoh)."""
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((device_ip, 123))  # Port NTP
                s.sendall(now.encode())
            self.log(f"✅ Waktu berhasil dikirim ke {device_ip}: {now}")
        except Exception as e:
            self.log(f"❌ Gagal sync ke {device_ip}: {e}")


# Main Program
# -----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = IPClock(root)
    root.mainloop()
