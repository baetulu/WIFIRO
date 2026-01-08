import os
import time
import socket
from wifipro.utils.terminal import colors
from wifipro.utils.renderer import format_target_table 

class Menu:
    def __init__(self):
        self.colors = colors 
        self.version = "3.0"
        self.wifi = None
        self.targets = []

    def set_wifi_engine(self, engine):
        """Menerima object WirelessManager"""
        self.wifi = engine

    # --- FUNGSI BARU: STATUS SISTEM ---
    def _display_system_status(self):
        """Mencetak baris status sistem: Monitor Mode, Interface, MAC, dan Version"""
        # 1. Ambil data interface
        iface = getattr(self.wifi, 'iface', "None") if self.wifi else "None"
        mac_addr = self.wifi.get_mac(iface) if self.wifi else "00:00:00:00:00:00"
        
        # 2. Cek Status Monitor Mode
        is_mon = self.wifi.get_mode_status(iface) if self.wifi else False
        
        # 3. Logika Tampilan Status (OFF = Merah + Blink)
        if is_mon:
            mon_status = f"{colors.G}ON{colors.NC}"
        else:
            # Menggunakan kode ANSI Blink (\033[5m)
            BLINK = "\033[5m"
            mon_status = f"{colors.R}{BLINK}OFF{colors.NC}"

        # 4. Susun Baris Status
        status_line = (
            f"  {colors.DG}Monitor Mode:  {mon_status}  "
            f"{colors.DG}│  Iface:  {colors.C}[{iface}]  "
            f"{colors.DG}│  MAC:  {colors.Y}{mac_addr}{colors.NC}  "
            f"{colors.DG}│  Ver: {colors.W}{self.version}{colors.NC}"
        )
        
        print(status_line)
        colors.draw_line(colors.W)

    # --- FUNGSI BARU: TABEL TARGET ---
    def _display_target_table(self):
        """Mencetak tabel target hasil scan jika tersedia"""
        line_width = 78 # Sesuaikan dengan lebar banner kamu
        
        if hasattr(self, 'targets') and self.targets:
            # Memanggil renderer yang sudah di-import di atas
            print(format_target_table(self.targets, colors, line_width))
            colors.draw_line(colors.W)

    def _display_banner(self):
        """WiFi Pro - Natural Random Spectrum Style"""
        # Padding kiri agar agak ke tengah
        side_pad = "            " 
        
        # Spektrum dibuat acak (Randomized feeling)
        # Baris 1: Puncak tertinggi (Hanya muncul sekali/dua kali)
        # Baris 2: Gelombang menengah
        # Baris 3: Noise floor / Garis tengah
        # Baris 4: Lembah (Lekukan bawah)
        icon = [
            f"{colors.B}          _                      ", 
            f"{colors.B}    _    / \\         _   _       ", 
            f"{colors.W}───{colors.B}/{colors.W}─{colors.B}\\{colors.W}──{colors.B}/{colors.W}───{colors.B}\\{colors.W}───{colors.B}_{colors.W}───{colors.B}/{colors.W}─{colors.B}\\{colors.W}─{colors.B}/{colors.W}─{colors.B}\\{colors.W}──────", 
            f"{colors.B}  V   V      \\ / \\ /   V   V     ", 
            f"{colors.B}              v   v             ",
            f"                                 ",
            f"                                 "
        ]
        
        # Jarak antara spektrum dan info
        gap = "         " 
        info = [
            f"{colors.B}{colors.BOLD}WiFi-PRO FRAMEWORK{colors.NC}",
            f"{colors.DG}──────────────────────────{colors.NC}",
            f"{colors.W}Version  : {colors.G}{self.version}{colors.NC}",
            f"{colors.W}Engine   : {colors.C}Aircrack-ng Suite{colors.NC}",
            f"{colors.W}Author   : {colors.P}kang-anom{colors.NC}",
            f"{colors.W}Codename : {colors.Y}Phantom-Scanner{colors.NC}",
            f"{colors.DG}──────────────────────────{colors.NC}"
        ]

        print("") 
        for i in range(len(icon)):
            print(f"{side_pad}{icon[i]}{gap}{info[i]}")
            
        print(f"{side_pad}            {colors.DG}Passive Air-Interface Monitoring{colors.NC}\n")
        colors.draw_line(colors.W)

    def display_header(self):
        """Header dinamis: Banner muncul hanya jika tabel kosong"""
        os.system('clear')
        
        # 1. Jika tabel KOSONG, tampilkan Banner Logo
        if not self.targets:
            self._display_banner()
        
        # 2. STATUS SISTEM selalu muncul paling atas (atau setelah banner)
        self._display_system_status()

        # 3. TABEL TARGET tampil jika ada isinya
        if self.targets:
            self._display_target_table()
            
    def run(self):
        if self.wifi is None:
            print(f"\033[1;31m[-] Critical Error: Wireless Engine not injected!\033[0m")
            return

        while True:
            # Sync status interface terbaru
            system_iface = self.wifi.get_interface() 
            current_iface = getattr(self.wifi, 'iface', "None")

            if (current_iface == "None" or not current_iface) and system_iface != "None":
                self.wifi.iface = system_iface
                current_iface = system_iface

            # Tampilkan Header (MAC & Monitor status tetep kelihatan di atas meski menu dihapus)
            self.display_header()

            # --- REKONSTRUKSI UI MENU (Lebih Padat) ---
            # --- Bagian ATTACK SUITE ---
            print(f"  {colors.B}{colors.BOLD}[ SCAN & RECON ]                 {colors.R}{colors.BOLD}[ ATTACK SUITE ]{colors.NC}")
            print(f"  {colors.W}[01]{colors.NC} %-27s {colors.W}[04]{colors.NC} %-25s" % ("Scanner (Auto-Target)", "DoS Attacks Menu"))
            print(f"  {colors.W}[02]{colors.NC} %-27s {colors.W}[05]{colors.NC} %-25s" % ("MITM & Sniffing", "Handshake & WPS Capture"))
            print(f"  {colors.W}[03]{colors.NC} %-27s" % ("Evil Twin Attacks"))
            
            # --- Bagian POST-EXPLOITATION ---
            print(f"\n  {colors.P}{colors.BOLD}[ POST-EXPLOITATION ]            {colors.G}{colors.BOLD}[ UTILITIES & EXIT ]{colors.NC}")
            print(f"  {colors.W}[06]{colors.NC} %-27s {colors.W}[08]{colors.NC} %-25s" % ("Offline Decrypt (Cracker)", "System Utilities"))
            print(f"  {colors.W}[07]{colors.NC} %-27s {colors.W}[00]{colors.NC} {colors.R}%-25s{colors.NC}" % ("Network Analysis", "Exit Script"))
            colors.draw_line(colors.W)
            
            try:
                choice = input(f"  {colors.Q} {colors.BOLD}Select an option: {colors.NC}").strip()

                # --- LOGIKA INPUT FLEKSIBEL (Handle 01, 1, dst) ---
                if choice in ['0', '00']: 
                    print(f"\n{colors.G}[!] Cleaning up and exiting...{colors.NC}")
                    self.wifi.set_managed_mode(current_iface)
                    break

                # Membersihkan angka 0 di depan untuk mempermudah elif
                cmd = choice.lstrip('0')

                # [01] SCANNER
                if cmd == '1':
                    self.wifi.ui_select_interface()
                    current_iface = getattr(self.wifi, 'iface', "None")
                    if current_iface != "None":
                        # Di sini lo bisa tambahin self.wifi.ui_spoof_mac(current_iface) kalau mau silent spoof
                        self.wifi.launch_airodump(current_iface, colors.OK, colors.WARN)
                        self.targets = getattr(self.wifi, 'targets', [])

                # [02] MITM
                elif cmd == '2':
                    if current_iface != "None":
                        self.processor.launch_mitm_attack(current_iface, colors.OK, colors.WARN)
                    else:
                        print(f"\n{colors.ERR} Select interface first (01)!")
                        time.sleep(1)

                # [03] EVIL TWIN
                elif cmd == '3':
                    print(f"\n{colors.INFO} Evil Twin Module coming soon...")
                    time.sleep(2)

                # [04] DOS ATTACKS (Pindahan dari 05 lama)
                elif cmd == '4':
                    if not self.targets:
                        print(f"\n{colors.WARN} Tabel Kosong! Jalankan Scan (01) dulu.")
                        time.sleep(2)
                    else:
                        # Logic Auto-Monitor & Restore sudah ada di dalam start_dos
                        self.wifi.deauth.start_dos(self.targets)

                # [05] HANDSHAKE/PMKID TOOLS
                elif cmd == '5':
                    # 1. Cek apakah interface sudah dipilih
                    if not current_iface or current_iface == "None":
                        print(f"\n{colors.ERR} Error: Pilih interface dulu (01)!")
                        time.sleep(1.5)
                    
                    # 2. Cek apakah sudah ada hasil scan (target)
                    elif not getattr(self, 'targets', []):
                        print(f"\n{colors.WARN} Tabel Kosong! Jalankan Scan (01) dulu untuk cari target.")
                        time.sleep(2)
                    
                    else:
                        # Membersihkan layar sebelum masuk ke sub-menu handshake
                        self.display_header()
                        
                        # Memanggil modul Handshake
                        # Sesuai struktur: self.wifi.handshake (pastikan sudah di-inject di __init__)
                        try:
                            from wifipro.attacks.handshake import HandshakeCapture
                            attacker = HandshakeCapture(self.wifi, colors)
                            attacker.start_capture(self.targets)
                        except Exception as e:
                            print(f"\n{colors.ERR} Gagal memuat Modul Handshake: {e}")
                            time.sleep(2)

                # [09] UTILITIES
                elif cmd == '9':
                    new_host = input(f"\n{colors.Q} Enter new hostname: ")
                    self.wifi.change_hostname(new_host)

            except KeyboardInterrupt:
                # Cek status terakhir sebelum exit
                if self.wifi.get_mode_status(current_iface):
                    print(f"\n{colors.G}[!] Monitor Mode detected. Restoring system...{colors.NC}")
                    self.wifi.set_managed_mode(current_iface)
                else:
                    print(f"\n{colors.OK} {colors.G}System already clean. Exiting...{colors.NC}")
                
                break
            except Exception as e:
                print(f"\n{colors.ERR} Error: {e}")
                time.sleep(2)
