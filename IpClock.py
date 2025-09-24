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
        self.root.geometry("600x400")
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
            button_frame, text="Realtime Sync", command=self.toggle_realtime_sync,
            bg="red", fg="white", width=15
        )
        self.realtime_sync_btn.pack(side=tk.LEFT, padx=5)


        # Status dan format
        status_frame = tk.Frame(root, bg="black")
        status_frame.pack(pady=5)
        
        tk.Label(status_frame, text="Time Format:", font=("Arial", 10), fg="white", bg="black").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="HH:MM")
        format_options = ["HH:MM", "HH:MM:SS", "HH:MM\\r\\n", "HH:MM:SS\\r\\n", "Custom"]
        self.format_combo = tk.OptionMenu(status_frame, self.format_var, *format_options)
        self.format_combo.config(bg="gray", fg="white")
        # Add custom format entry
        self.custom_entry = tk.Entry(status_frame, font=("Arial", 10), width=20, bg="gray", fg="white")
        self.custom_entry.pack(side=tk.LEFT, padx=5)
        self.custom_entry.insert(0, "%H%M\r\n")  # Format HHMM dengan CR LF
        
        # Debug frame
        debug_frame = tk.Frame(root, bg="black")
        debug_frame.pack(pady=5)
        
        self.send_custom_btn = tk.Button(
            debug_frame, text="Send Custom", command=self.send_custom, 
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

    def log(self, message):
        """Tulis pesan ke log area."""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def toggle_realtime_sync(self):
        """Toggle realtime sync tiap detik."""
        if not self.auto_sync_active:
            self.auto_sync_active = True
            self.realtime_sync_btn.config(text="Stop Realtime", bg="gray")
            self.auto_sync_thread = threading.Thread(target=self.realtime_sync_worker, daemon=True)
            self.auto_sync_thread.start()
            self.log("Realtime sync started - kirim waktu tiap detik")
        else:
            self.auto_sync_active = False
            self.realtime_sync_btn.config(text="Realtime Sync", bg="red")
            self.log("Realtime sync stopped")

    def realtime_sync_worker(self):
        """Worker untuk realtime sync tiap detik."""
        while self.auto_sync_active:
            now = self.get_ntp_time()

            # Ambil format (support custom juga)
            if self.format_var.get() == "Custom":
                formatted_data = now.strftime(self.custom_entry.get())
            else:
                formatted_data = self.format_time(now)

            # Handle escape sequence (CR LF, hex, dll)
            if '\\r\\n' in formatted_data:
                formatted_data = formatted_data.replace('\\r\\n', '\r\n')
            if '\\r' in formatted_data:
                formatted_data = formatted_data.replace('\\r', '\r')
            if '\\n' in formatted_data:
                formatted_data = formatted_data.replace('\\n', '\n')

            import re
            def replace_hex(match):
                hex_str = match.group(1)
                return bytes.fromhex(hex_str).decode('latin1')
            formatted_data = re.sub(r'\\x([0-9a-fA-F]{2})', replace_hex, formatted_data)

            try:
                ip = self.ip_entry.get().strip()
                port = int(self.port_entry.get().strip())
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(5)
                    s.connect((ip, port))
                    data_bytes = formatted_data.encode('latin1')
                    s.send(data_bytes)
            except Exception as e:
                self.log(f"Realtime sync error: {e}")

            time.sleep(1)


    def update_clock(self):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.clock_label.config(text=now)
        self.root.after(1000, self.update_clock)

    def get_ntp_time(self):
        try:
            client = ntplib.NTPClient()
            response = client.request('id.pool.ntp.org', timeout=5)
            ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
            return ntp_time
        except Exception as e:
            self.log(f"Gagal ambil NTP time: {e}, gunakan waktu lokal")
            return datetime.datetime.now()

    def format_time(self, dt):
        format_str = self.format_var.get()
        
        if format_str == "HH:MM":
            return dt.strftime("%H:%M")
        elif format_str == "HH:MM:SS":
            return dt.strftime("%H:%M:%S")
        elif format_str == "HH:MM\\r\\n":
            return dt.strftime("%H:%M") + "\r\n"
        elif format_str == "HH:MM:SS\\r\\n":
            return dt.strftime("%H:%M:%S") + "\r\n"
        elif format_str == "Custom":
            custom_format = self.custom_entry.get()
            return dt.strftime(custom_format)  # ini tetap support leading zero
        else:
            return dt.strftime("%H:%M")

        """Format waktu sesuai pilihan."""
        format_str = self.format_var.get()
        
        if format_str == "HH:MM":
            return dt.strftime("%H:%M")
        elif format_str == "HH:MM:SS":
            return dt.strftime("%H:%M:%S")
        elif format_str == "HH:MM\\r\\n":
            return dt.strftime("%H:%M") + "\r\n"
        elif format_str == "HH:MM:SS\\r\\n":
            return dt.strftime("%H:%M:%S") + "\r\n"
        elif format_str == "Custom":
            # Use custom format with time placeholders
            custom_format = self.custom_entry.get()
            return dt.strftime(custom_format)
        else:
            return dt.strftime("%H:%M")

    def send_custom(self):
        """Kirim custom command ke NP301."""
        try:
            ip = self.ip_entry.get().strip()
            port = int(self.port_entry.get().strip())
            custom_format = self.custom_entry.get()
            
            # Get time
            now = self.get_ntp_time()
            
            # Handle special escape sequences properly
            formatted_data = now.strftime(custom_format)
            
            # Convert escape sequences to actual bytes
            if '\\r\\n' in formatted_data:
                formatted_data = formatted_data.replace('\\r\\n', '\r\n')
            if '\\r' in formatted_data:
                formatted_data = formatted_data.replace('\\r', '\r')
            if '\\n' in formatted_data:
                formatted_data = formatted_data.replace('\\n', '\n')
            
            # Handle hex sequences like \x02, \x03
            import re
            def replace_hex(match):
                hex_str = match.group(1)
                return bytes.fromhex(hex_str).decode('latin1')
            
            formatted_data = re.sub(r'\\x([0-9a-fA-F]{2})', replace_hex, formatted_data)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                s.connect((ip, port))
                
                data_bytes = formatted_data.encode('latin1')  # Use latin1 to preserve bytes
                s.send(data_bytes)
                
                self.log(f"Custom command sent: {repr(formatted_data)}")
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
                        s.settimeout(30)  # 30 second timeout
                        s.connect((ip, port))
                        
                        self.log("Monitoring NP301 for serial data...")
                        self.log("Jika ada device serial yang kirim data, akan terlihat di sini")
                        
                        start_time = time.time()
                        while time.time() - start_time < 30:  # Monitor for 30 seconds
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
                
                # Send test data
                test_data = "TEST\r\n"
                s.send(test_data.encode())
                self.log(f"Connection OK! Sent test data: {repr(test_data)}")
                
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
                data_bytes = time_str.encode('utf-8')
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