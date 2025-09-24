import tkinter as tk
import socket
import datetime
import threading
import subprocess
import ntplib
import binascii
import time


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


def scan_active_ips(base_ip):
    """Scan IP di segmen yang sama, return list IP yang aktif."""
    active_ips = []
    threads = []
    lock = threading.Lock()

    def ping(ip):
        try:
            result = subprocess.run(
                ["ping", "-n", "1", "-w", "300", ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if result.returncode == 0:
                with lock:
                    active_ips.append(ip)
        except Exception:
            pass

    for i in range(1, 255):
        ip = f"{base_ip}.{i}"
        t = threading.Thread(target=ping, args=(ip,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return active_ips


class NPClockSync:
    def __init__(self, root):
        self.root = root
        self.root.title("NP301 Clock Sync - By Puterako")
        self.root.geometry("600x450")
        self.root.configure(bg="black")

        # Label jam digital
        self.clock_label = tk.Label(
            root, text="", font=("Arial", 48, "bold"), fg="lime", bg="black"
        )
        self.clock_label.pack(pady=20)

        # Frame untuk input
        input_frame = tk.Frame(root, bg="black")
        input_frame.pack(pady=10)
        
        tk.Label(input_frame, text="NP301 IP:", font=("Arial", 12), fg="white", bg="black").pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(input_frame, font=("Arial", 14), width=20)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        self.ip_entry.insert(0, "192.168.2.246")  # Default IP
        
        tk.Label(input_frame, text="Port:", font=("Arial", 12), fg="white", bg="black").pack(side=tk.LEFT, padx=(10,0))
        self.port_entry = tk.Entry(input_frame, font=("Arial", 14), width=8)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        self.port_entry.insert(0, "1001")  # Default port

        # Frame untuk tombol
        button_frame = tk.Frame(root, bg="black")
        button_frame.pack(pady=10)
        
        self.test_btn = tk.Button(
            button_frame, text="Test Connection", command=self.test_connection, 
            bg="blue", fg="white", width=15
        )
        self.test_btn.pack(side=tk.LEFT, padx=5)
        
        self.realtime_sync_btn = tk.Button(
            button_frame, text="Live Custom Sync", command=self.toggle_realtime_sync,
            bg="red", fg="white", width=15
        )
        self.realtime_sync_btn.pack(side=tk.LEFT, padx=5)

        # Status dan format
        status_frame = tk.Frame(root, bg="black")
        status_frame.pack(pady=5)
        
        tk.Label(status_frame, text="Format: HHMM + CR LF", font=("Arial", 12), fg="lime", bg="black").pack(side=tk.LEFT)
        
        # Format entry (fixed format)
        self.custom_entry = tk.Entry(status_frame, font=("Arial", 10), width=15, bg="gray", fg="white")
        self.custom_entry.pack(side=tk.LEFT, padx=10)
        self.custom_entry.insert(0, "%H%M\r\n")  # Format HHMM dengan CR LF
        self.custom_entry.config(state="readonly")  # Make it readonly so user can't change
        
        # Debug frame
        debug_frame = tk.Frame(root, bg="black")
        debug_frame.pack(pady=5)
        
        self.send_custom_btn = tk.Button(
            debug_frame, text="Send Once", command=self.send_custom, 
            bg="purple", fg="white", width=12
        )
        self.send_custom_btn.pack(side=tk.LEFT, padx=5)
        
        self.monitor_btn = tk.Button(
            debug_frame, text="Monitor Serial", command=self.monitor_serial, 
            bg="teal", fg="white", width=12
        )
        self.monitor_btn.pack(side=tk.LEFT, padx=5)

        # Log area
        self.log_text = tk.Text(root, height=15, bg="black", fg="white", font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, padx=10, pady=10)

        # Auto sync control
        self.auto_sync_active = False
        self.auto_sync_thread = None
        
        # Mulai update clock display
        self.update_clock()
        
        # Log initial info
        self.log("=== NP301 Serial Device Server Clock Sync ===")
        self.log("PENTING: NP301 harus terhubung ke device clock/display di serial port")
        self.log("Program ini mengirim waktu ke NP301, lalu NP301 teruskan ke serial device")
        self.log("Gunakan 'Live Custom Sync' untuk mengirim format HHMM + CRLF secara live")

    def log(self, message):
        """Tulis pesan ke log area."""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def toggle_realtime_sync(self):
        """Toggle realtime sync tiap detik dengan format custom."""
        if not self.auto_sync_active:
            self.auto_sync_active = True
            self.realtime_sync_btn.config(text="Stop Live Sync", bg="gray")
            self.auto_sync_thread = threading.Thread(target=self.realtime_sync_worker, daemon=True)
            self.auto_sync_thread.start()
            
            # Log format yang akan digunakan
            current_format = self.get_current_format_string()
            self.log(f"Live Custom Sync started - format: {repr(current_format)}")
        else:
            self.auto_sync_active = False
            self.realtime_sync_btn.config(text="Live Custom Sync", bg="red")
            self.log("Live Custom Sync stopped")

    def get_current_format_string(self):
        """Dapatkan format string yang sedang aktif (fixed format)."""
        return self.custom_entry.get()

    def process_format_string(self, format_str, dt):
        """Proses format string dan konversi escape sequences."""
        # First apply datetime formatting
        formatted_data = dt.strftime(format_str)
        
        # Handle escape sequences - convert \r\n to actual CR LF
        if '\\r\\n' in formatted_data:
            formatted_data = formatted_data.replace('\\r\\n', '\r\n')
        elif '\r\n' not in formatted_data and ('\\r' in formatted_data or '\\n' in formatted_data):
            if '\\r' in formatted_data:
                formatted_data = formatted_data.replace('\\r', '\r')
            if '\\n' in formatted_data:
                formatted_data = formatted_data.replace('\\n', '\n')
        
        return formatted_data

    def realtime_sync_worker(self):
        """Worker untuk realtime sync tiap detik dengan format yang dipilih."""
        last_sent_data = ""
        last_minute = -1
        
        while self.auto_sync_active:
            try:
                now = self.get_ntp_time()
                
                # Ambil format yang sedang aktif
                current_format = self.get_current_format_string()
                formatted_data = self.process_format_string(current_format, now)
                
                # Kirim data setiap menit (saat menit berubah)
                current_minute = now.minute
                if current_minute != last_minute or formatted_data != last_sent_data:
                    ip = self.ip_entry.get().strip()
                    port = int(self.port_entry.get().strip())
                    
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(5)
                        s.connect((ip, port))
                        data_bytes = formatted_data.encode('latin1')
                        s.send(data_bytes)
                        
                        # Log setiap kali kirim data
                        self.log(f"Live sync: {repr(formatted_data)} -> {binascii.hexlify(data_bytes).decode('ascii')}")
                    
                    last_sent_data = formatted_data
                    last_minute = current_minute
                    
            except Exception as e:
                self.log(f"Live sync error: {e}")
                # Jangan berhenti, coba lagi
                
            time.sleep(1)

    def update_clock(self):
        """Update tampilan jam digital di interface."""
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def get_ntp_time(self):
        """Ambil waktu dari NTP server, fallback ke waktu lokal."""
        try:
            client = ntplib.NTPClient()
            response = client.request('id.pool.ntp.org', timeout=5)
            ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
            return ntp_time
        except Exception as e:
            # Hanya log error pertama kali, tidak spam log
            if not hasattr(self, '_ntp_error_logged'):
                self.log(f"NTP unavailable: {e}, using local time")
                self._ntp_error_logged = True
            return datetime.datetime.now()

    def format_time(self, dt):
        """Format waktu dengan format fixed HHMM + CRLF."""
        return self.process_format_string(self.custom_entry.get(), dt)

    def send_custom(self):
        """Kirim custom command ke NP301 sekali."""
        try:
            ip = self.ip_entry.get().strip()
            port = int(self.port_entry.get().strip())
            
            # Get time
            now = self.get_ntp_time()
            
            # Use current format
            current_format = self.get_current_format_string()
            formatted_data = self.process_format_string(current_format, now)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((ip, port))
                
                data_bytes = formatted_data.encode('latin1')
                s.send(data_bytes)
                
                self.log(f"Single send: {repr(formatted_data)}")
                self.log(f"Hex: {binascii.hexlify(data_bytes).decode('ascii')}")
                self.log(f"Raw bytes: {data_bytes}")
                
        except Exception as e:
            self.log(f"Send custom failed: {e}")

    def monitor_serial(self):
        """Monitor data yang diterima dari NP301 (jika ada response dari serial device)."""
        try:
            ip = self.ip_entry.get().strip()
            port = int(self.port_entry.get().strip())
            
            def monitor_worker():
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(30)
                        s.connect((ip, port))
                        
                        self.log("Monitoring NP301 for serial data...")
                        self.log("Jika ada device serial yang kirim data, akan terlihat di sini")
                        
                        start_time = time.time()
                        while time.time() - start_time < 30:
                            try:
                                s.settimeout(1)
                                data = s.recv(1024)
                                if data:
                                    self.log(f"Serial data received: {data}")
                                    self.log(f"Hex: {binascii.hexlify(data).decode('ascii')}")
                                    self.log(f"ASCII: {data.decode('utf-8', errors='ignore')}")
                            except socket.timeout:
                                continue
                            except Exception as e:
                                self.log(f"Monitor error: {e}")
                                break
                        
                        self.log("Monitor completed")
                        
                except Exception as e:
                    self.log(f"Monitor failed: {e}")
            
            threading.Thread(target=monitor_worker, daemon=True).start()
            
        except Exception as e:
            self.log(f"Monitor setup failed: {e}")

    def test_connection(self):
        """Test koneksi ke NP301."""
        try:
            ip = self.ip_entry.get().strip()
            port = int(self.port_entry.get().strip())
            
            self.log(f"Testing connection to {ip}:{port}...")
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((ip, port))
                
                # Send test data dengan format yang sama
                now = self.get_ntp_time()
                test_data = self.process_format_string(self.custom_entry.get(), now)
                data_bytes = test_data.encode('latin1')
                s.send(data_bytes)
                
                self.log(f"Connection OK! Sent test data: {repr(test_data)}")
                self.log(f"Hex: {binascii.hexlify(data_bytes).decode('ascii')}")
                
                # Try to receive response (optional)
                try:
                    s.settimeout(2)
                    response = s.recv(1024)
                    if response:
                        self.log(f"Received response: {response}")
                except socket.timeout:
                    self.log("No response from device (normal for NP301)")
                    
        except ValueError:
            self.log("Error: Port harus berupa angka")
        except ConnectionRefusedError:
            self.log(f"Connection refused - cek apakah NP301 dalam mode TCP Server")
        except socket.timeout:
            self.log("Connection timeout - cek IP dan network")
        except Exception as e:
            self.log(f"Test connection failed: {e}")

    def sync_time_to_np301(self):
        """Kirim waktu ke NP301 yang akan diteruskan ke serial device."""
        try:
            ip = self.ip_entry.get().strip()
            port = int(self.port_entry.get().strip())
            
            # Get NTP time
            ntp_time = self.get_ntp_time()
            time_str = self.format_time(ntp_time)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)
                s.connect((ip, port))
                
                # Convert to bytes
                data_bytes = time_str.encode('latin1')
                hex_data = binascii.hexlify(data_bytes).decode('ascii')
                
                self.log(f"Syncing time to {ip}:{port}")
                self.log(f"  Time: {time_str.strip()}")
                self.log(f"  Bytes: {data_bytes}")
                self.log(f"  Hex: {hex_data}")
                
                # Send data
                bytes_sent = s.send(data_bytes)
                self.log(f"  Sent {bytes_sent} bytes to NP301")
                self.log("  NP301 akan teruskan ke serial device yang terhubung")
                
                return True
                
        except ValueError:
            self.log("Error: Port harus berupa angka")
            return False
        except Exception as e:
            self.log(f"Sync failed: {e}")
            return False


if __name__ == "__main__":
    root = tk.Tk()
    app = NPClockSync(root)
    root.mainloop()