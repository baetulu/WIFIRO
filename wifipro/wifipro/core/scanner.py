import os
import time
import csv
import subprocess

class WiFiScanner:
    def __init__(self, manager):
        """
        Menerima instance WirelessManager (self dari process.py) 
        agar bisa memanggil fungsi monitor mode.
        """
        self.manager = manager
        self.output_file = "/tmp/wifipro_scan"
        self.csv_path = f"{self.output_file}-01.csv"

    def launch_airodump(self, interface, ok_simbol, warn_simbol):
        """Master Scan: Mengambil data lengkap untuk Dashboard & Menu Lain"""
        try:
            # 1. Cek & Auto-Switch Monitor Mode via Manager
            is_monitor = self.manager.get_mode_status(interface)
            if not is_monitor:
                print(f"  {ok_simbol} Mengaktifkan mode monitor otomatis...")
                self.manager.toggle_mode(interface)
                time.sleep(2)
                # Ambil interface terbaru (mungkin berubah nama setelah airmon-ng)
                interface = getattr(self.manager, 'iface', interface)

            # Bersihkan file sampah scan sebelumnya
            os.system(f"rm -f {self.output_file}*")
            
            # Perintah scanner
            cmd = f"airodump-ng {interface} --wps --manufacturer --beacons -w {self.output_file} --write-interval 1"
            geometry = "110x35+950+50"

            print(f"  {ok_simbol} Membuka Master Scanner di jendela baru...")
            print(f"  {warn_simbol} TEKAN CTRL+C PADA JENDELA SCANNER ATAU DI SINI UNTUK BERHENTI.")
            
            # Membuka terminal eksternal
            if os.system("which gnome-terminal > /dev/null 2>&1") == 0:
                proc = subprocess.Popen(["gnome-terminal", f"--geometry={geometry}", "--title=SCANNING...", "--", "bash", "-c", cmd])
            elif os.system("which xfce4-terminal > /dev/null 2>&1") == 0:
                proc = subprocess.Popen(["xfce4-terminal", f"--geometry={geometry}", "--title=SCANNING...", "-e", f"bash -c '{cmd}'"])
            else:
                proc = subprocess.Popen(["xterm", "-geometry", geometry, "-T", "SCANNING...", "-e", f"bash -c '{cmd}'"])

            # Tunggu sampai terminal ditutup atau CTRL+C
            while proc.poll() is None:
                time.sleep(0.5)

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"  {warn_simbol} Error Scanner: {e}")

        # --- PROSES CLEANUP & DATA HARVESTING ---
        return self._harvest_data(ok_simbol, warn_simbol)

    def _harvest_data(self, ok_simbol, warn_simbol):
        """Internal logic untuk membaca CSV dan mengonversi ke list of dict"""
        print(f"\n  {ok_simbol} Menutup Scanner & Menyelaraskan Data Dashboard...")
        os.system("pkill -f airodump-ng > /dev/null 2>&1")
        time.sleep(1.5)
        
        found_targets = []

        if not os.path.exists(self.csv_path):
            print(f"  {warn_simbol} File data scan tidak ditemukan.")
            return []

        try:
            with open(self.csv_path, 'r') as f:
                content = f.read()
                parts = content.split('\n\n')
                
                # BAGIAN 1: ACCESS POINTS
                if len(parts) > 0:
                    ap_list = csv.reader(parts[0].splitlines())
                    for row in ap_list:
                        if len(row) >= 14 and row[0].strip() not in ["BSSID", ""]:
                            found_targets.append({
                                'bssid': row[0].strip(),
                                'ch': row[3].strip(),
                                'pwr': row[8].strip(),
                                'data': row[10].strip(),
                                'enc': row[5].strip(),
                                'essid': row[13].strip(),
                                'clients': "0",
                                'beacons': row[9].strip(),
                                'auth': row[7].strip(),
                                'wps': "YES" if len(row) > 15 and row[15].strip() else "NO"
                            })

                # BAGIAN 2: STATIONS (Menghitung Client)
                if len(parts) > 1:
                    st_list = csv.reader(parts[1].splitlines())
                    for row in st_list:
                        if len(row) >= 6 and row[0].strip() not in ["Station MAC", ""]:
                            target_bssid = row[5].strip()
                            for t in found_targets:
                                if t['bssid'] == target_bssid:
                                    t['clients'] = str(int(t['clients']) + 1)

            print(f"  {ok_simbol} Berhasil menyinkronkan {len(found_targets)} Access Points.")
            return found_targets

        except Exception as e:
            print(f"  {warn_simbol} Gagal memproses tabel: {e}")
            return []
