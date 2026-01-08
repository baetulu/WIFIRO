#!/usr/bin/env python3
import os
import sys
import time

# Memastikan script bisa membaca folder wifipro sebagai package
sys.path.insert(0, os.path.abspath(os.getcwd()))

try:
    from wifipro.core.config import Menu
    from wifipro.utils.process import WirelessManager
    from wifipro.utils.terminal import colors
except ImportError as e:
    print(f"\033[91m[!] Error: Struktur folder tidak lengkap.\033[0m")
    print(f"Log: {e}")
    sys.exit(1)

def check_root():
    """Memastikan script dijalankan dengan hak akses root"""
    if os.geteuid() != 0:
        print(f"{colors.R}[!] Script ini memerlukan hak akses root.{colors.NC}")
        try:
            # Otomatis mencoba menjalankan ulang dengan sudo
            os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
        except Exception:
            print(f"{colors.R}[!] Gagal mendapatkan hak akses root. Gunakan: sudo python3 main.py{colors.NC}")
            sys.exit(1)

def main():
    # 1. Cek Root (Wajib untuk aircrack & scapy)
    check_root()

    # 2. Inisialisasi Objek Menu (Tampilan UI)
    app = Menu()
    
    # 3. Inisialisasi Objek Engine (Logika Eksekusi)
    # Kita kirim objek 'colors' agar WirelessManager bisa menggunakannya
    wifi_engine = WirelessManager(colors)
    
    # 4. PROSES INJEKSI & SINKRONISASI
    # Mengisi 'self.wifi' di dalam class Menu
    app.set_wifi_engine(wifi_engine)
    
    # MENGISI 'self.processor' agar Menu [04] MITM tidak error
    # Ini adalah solusi untuk error 'Menu' object has no attribute 'processor'
    app.processor = wifi_engine 
    
    # 5. Eksekusi Aplikasi
    os.system('clear')
    try:
        app.run()
    except KeyboardInterrupt:
        print(f"\n\n{colors.Y}[!] Terdeteksi CTRL+C. Membersihkan proses...{colors.NC}")
        # Jika perlu, tambahkan fungsi cleanup di sini
        time.sleep(1)
        print(f"{colors.G}[*] Keluar dengan aman. Sampai jumpa!{colors.NC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{colors.R}[!] Fatal Error: {e}{colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main()
