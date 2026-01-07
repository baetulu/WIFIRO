#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.abspath(os.getcwd()))
# Import dari struktur package baru
from wifipro.core.config import Menu
from wifipro.utils.process import WirelessManager
from wifipro.utils.terminal import colors


def check_root():
    if os.geteuid() != 0:
        print(f"{colors.R}[!] Script ini memerlukan hak akses root.{colors.NC}")
        try:
            os.execvp('sudo', ['sudo', sys.executable] + sys.argv)
        except Exception as e:
            sys.exit(1)

def main():
    # 0. Cek Root
    check_root()

    # 1. Inisialisasi Menu (Objek Tampilan)
    app = Menu()
    
    # 2. Inisialisasi Engine (Objek Eksekusi/Interface)
    # UPGRADE: Masukkan objek 'colors' ke dalam WirelessManager
    wifi_engine = WirelessManager(colors)
    
    # 3. PROSES INJEKSI
    # Masukkan engine yang sudah berisi 'colors' ke dalam Menu
    app.set_wifi_engine(wifi_engine)
    
    try:
        # 4. Jalankan aplikasi
        app.run()
    except KeyboardInterrupt:
        print(f"\n{colors.Y}[!] Keluar...{colors.NC}")
        sys.exit(0)

if __name__ == "__main__":
    main()
