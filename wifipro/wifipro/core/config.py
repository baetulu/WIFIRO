import os
import time
import socket
from wifipro.utils.terminal import colors
from wifipro.utils.renderer import format_target_table 

class Menu:
    def __init__(self):
        self.colors = colors 
        self.version = "2.0"
        self.wifi = None
        self.targets = []

    def set_wifi_engine(self, engine):
        """Menerima object WirelessManager"""
        self.wifi = engine

    # --- FUNGSI BARU: STATUS SISTEM ---
    def _display_system_status(self):
        """Mencetak baris status sistem: Host, Interface, MAC, dan Version"""
        iface = getattr(self.wifi, 'iface', "None") if self.wifi else "None"
        mac_addr = self.wifi.get_mac(iface) if self.wifi else "00:00:00:00:00:00"
        
        try:
            current_host = socket.gethostname()
        except:
            current_host = "Unknown"

        status_line = (
            f"  {colors.DG}Host:  {colors.W}[{current_host}]  "
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
            f"{colors.W}───/─\\──/───\\───_───/─\\─/─\\──────", 
            f"{colors.B}  V   V      \\ / \\ V   V   V     ", 
            f"{colors.B}              v                  ",
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
            f"{colors.W}Author   : {colors.P}kang-nom{colors.NC}",
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
            system_iface = self.wifi.get_interface() 
            current_iface = getattr(self.wifi, 'iface', "None")

            if (current_iface == "None" or not current_iface) and system_iface != "None":
                self.wifi.iface = system_iface
                current_iface = system_iface

            is_mon = self.wifi.get_mode_status(current_iface)
            status_text = f"{colors.G}ON{colors.NC}" if is_mon else f"{colors.R}{colors.BOLD}OFF{colors.NC}"

            # Panggil Header (Sekarang sudah mencakup status dan tabel)
            self.display_header()
            

            # --- UI MENU ---
            print(f"  {colors.B}{colors.BOLD}[ SYSTEM & INTERFACE ]{colors.NC}           {colors.R}{colors.BOLD}[ ATTACK SUITE ]{colors.NC}")
            print(f"  {colors.W}[01]{colors.NC} %-26s  {colors.W}[05]{colors.NC} %-25s" % ("Refresh Target/Intf", "DoS Attacks Menu"))
            print(f"  {colors.W}[02]{colors.NC} Monitor Mode [{status_text}]          {colors.W}[06]{colors.NC} %-25s" % ("Handshake/PMKID Tools"))
            print(f"  {colors.W}[03]{colors.NC} %-26s  {colors.W}[07]{colors.NC} %-25s" % ("Spoof MAC Address", "Offline Decrypt Menu"))
            print(f"  {colors.W}[04]{colors.NC} %-26s  {colors.W}[08]{colors.NC} %-25s" % ("Sniffing ", "Evil Twin Attacks"))
            print(f"\n  {colors.P}{colors.BOLD}[ ADVANCED ATTACKS ]{colors.NC}                {colors.G}{colors.BOLD}[ UTILITIES & EXIT ]{colors.NC}")
            print(f"  {colors.W}[09]{colors.NC} %-26s  {colors.W}[00]{colors.NC} {colors.R}%-25s{colors.NC}" % ("WPS Attacks Menu", "Exit Script"))
            colors.draw_line(colors.W)
            
            
            try:
                choice = input(f"  {colors.Q} {colors.BOLD}Select an option: {colors.NC}").strip()

                if choice in ['0', '00']: 
                    break

                elif choice in ['01', '1']:
                    self.wifi.ui_select_interface()
                    current_iface = getattr(self.wifi, 'iface', "None")
                    if current_iface and current_iface != "None":
                        self.wifi.launch_airodump(current_iface, colors.OK, colors.WARN)
                        self.targets = getattr(self.wifi, 'targets', [])
                    else:
                        print(f"\n{colors.ERR} Batal: Interface tidak dipilih.")
                        time.sleep(1)

                elif choice == '02':
                    if current_iface != "None":
                        self.wifi.toggle_mode(current_iface)
                    else:
                        print(f"\n{colors.ERR} Select interface first!")
                        time.sleep(1)

                elif choice in ['03', '3']:
                    if not current_iface or current_iface == "None":
                        print(f"\n{colors.ERR} Error: Pilih interface dulu (01)!")
                        time.sleep(1.5)
                    else:
                        self.display_header()
                        self.wifi.ui_spoof_mac(current_iface)

                elif choice == "04":
                    if not current_iface or current_iface == "None":
                        print(f"\n{colors.ERR} Error: Pilih interface dulu (01)!")
                        time.sleep(1.5)
                    elif "ON" not in status_text:
                        print(f"\n{colors.ERR} Error: Monitor Mode harus ON!")
                        time.sleep(1.5)
                    elif not self.targets:
                        print(f"\n{colors.WARN} Tabel Kosong! Jalankan Scan (01) dulu.")
                        time.sleep(2)
                    else:
                        # Alur pemilihan target mirip Deauth
                        try:
                            print(f"\n{colors.Q} Select Target ID to Sniff (1-{len(self.targets)}):")
                            val = input(f"  {colors.DG}Selection (Enter for ALL) > {colors.NC}").strip()
                            
                            if not val:
                                # Jika user langsung enter, sniff semua
                                self.wifi._packet_sniffing(None)
                            else:
                                target = self.targets[int(val) - 1]
                                # Ambil bssid dan channel dari tabel
                                bssid = target.get('bssid')
                                channel = target.get('ch')
                                
                                # LOCK CHANNEL target agar trafik tertangkap
                                os.system(f"iw dev {current_iface} set channel {channel}")
                                
                                # Jalankan sniffer dengan filter MAC
                                self.wifi._packet_sniffing(bssid)
                        except (ValueError, IndexError):
                            print(f"{colors.ERR} Invalid Target ID.")
                            time.sleep(1)
                        
                elif choice in ['05', '5']:
                    if not current_iface or current_iface == "None":
                        print(f"\n{colors.ERR} Error: Pilih interface dulu (01)!")
                        time.sleep(1.5)
                    elif not self.targets:
                        print(f"\n{colors.WARN} Tabel Kosong! Jalankan Scan (01) dulu.")
                        time.sleep(2)
                    else:
                        self.display_header()
                        self.wifi.deauth.ui_dos_menu(self.targets)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n{colors.ERR} Error: {e}")
                time.sleep(2)
