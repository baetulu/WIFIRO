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
        iface = getattr(self.wifi, 'iface', "None") if self.wifi else "None"
        mac_addr = self.wifi.get_mac(iface) if self.wifi else "00:00:00:00:00:00"
        
        is_mon = self.wifi.get_mode_status(iface) if self.wifi else False
        
        if is_mon:
            mon_status = f"{colors.G}ON{colors.NC}"
        else:
            BLINK = "\033[5m"
            mon_status = f"{colors.R}{BLINK}OFF{colors.NC}"

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
        line_width = 78 
        if hasattr(self, 'targets') and self.targets:
            print(format_target_table(self.targets, colors, line_width))
            colors.draw_line(colors.W)

    def _display_banner(self):
        """WiFi Pro - Natural Random Spectrum Style"""
        side_pad = "            " 
        icon = [
            f"{colors.B}          _                     ", 
            f"{colors.B}    _    / \\         _   _       ", 
            f"{colors.W}───{colors.B}/{colors.W}─{colors.B}\\{colors.W}──{colors.B}/{colors.W}───{colors.B}\\{colors.W}───{colors.B}_{colors.W}───{colors.B}/{colors.W}─{colors.B}\\{colors.W}─{colors.B}/{colors.W}─{colors.B}\\{colors.W}──────", 
            f"{colors.B}  V   V      \\ / \\ /   V   V     ", 
            f"{colors.B}              v   v             ",
            f"                                 ",
            f"                                 "
        ]
        
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

    def _display_saved_passwords(self):
        """Menampilkan hasil panen password dari file log"""
        c = self.colors
        result_file = "data/evil_results.txt"
        
        os.system('clear')
        self._display_system_status()
        print(f"\n  {c.P}{c.BOLD}[ HARVESTED PASSWORDS ARCHIVE ]{c.NC}")
        c.draw_line(c.W)
        
        if not os.path.exists(result_file) or os.stat(result_file).st_size == 0:
            print(f"  {c.R} Belum ada password yang tertangkap. Terus semangat, Bro!{c.NC}")
        else:
            print(f"  {c.W}{'WAKTU':<22} | {'PASSWORD':<20}{c.NC}")
            print(f"  {'-'*45}")
            with open(result_file, "r") as f:
                for line in f:
                    if "Password:" in line:
                        parts = line.split(" Password: ")
                        time_str = parts[0].replace("[", "").replace("]", "")
                        pwd = parts[1].strip()
                        print(f"  {c.G}{time_str:<22}{c.NC} | {c.Y}{pwd:<20}{c.NC}")
        
        print("")
        c.draw_line(c.W)
        input(f"  {c.OK} Tekan Enter untuk kembali ke Menu Utama...")

    def display_header(self):
        """Header dinamis: Banner muncul hanya jika tabel kosong"""
        os.system('clear')
        if not self.targets:
            self._display_banner()
        self._display_system_status()
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

            self.display_header()

            print(f"  {colors.B}{colors.BOLD}[ CORE ATTACKS ]                  {colors.R}{colors.BOLD}[ DATA & CRACKING ]{colors.NC}")
            print(f"  {colors.W}[01]{colors.NC} %-27s {colors.W}[04]{colors.NC} %-25s" % ("Scanner (Auto-Target)", "NetCut (ARP Spoof)"))
            print(f"  {colors.W}[02]{colors.NC} %-27s {colors.W}[05]{colors.NC} %-25s" % ("Handshake & WPS Capture", "Saved Passwords"))
            print(f"  {colors.W}[03]{colors.NC} %-27s {colors.W}[06]{colors.NC} %-25s" % ("DoS Attacks Menu", "Evil Twin Attacks"))
            
            print(f"\n  {colors.P}{colors.BOLD}[ EXPERIMENTAL & SYSTEM ]        {colors.G}{colors.BOLD}[ MAINTENANCE ]{colors.NC}")
            print(f"  {colors.W}[07]{colors.NC} %-27s {colors.W}[09]{colors.NC} %-25s" % ("MITM & Sniffing (BETA)", "Cleanup & Reset"))
            print(f"  {colors.W}[08]{colors.NC} %-27s {colors.W}[00]{colors.NC} {colors.R}%-25s{colors.NC}" % ("System Utilities", "Exit Script"))
            colors.draw_line(colors.W)
            
            try:
                choice = input(f"  {colors.Q} {colors.BOLD}Select an option: {colors.NC}").strip()
                if choice in ['0', '00']: 
                    self.wifi.set_managed_mode(current_iface)
                    break

                cmd = choice.lstrip('0')

                # [01] SCANNER
                if cmd == '1':
                    self.wifi.ui_select_interface()
                    current_iface = getattr(self.wifi, 'iface', "None")
                    if current_iface != "None":
                        self.targets = self.wifi.scanner.launch_airodump(
                            current_iface, 
                            colors.OK, 
                            colors.WARN
                        )

                # [02] HANDSHAKE CAPTURE
                elif cmd == '2':
                    if not current_iface or current_iface == "None":
                        print(f"\n{colors.ERR} Error: Pilih interface dulu (01)!")
                        time.sleep(1.5)
                    elif not self.targets:
                        print(f"\n{colors.WARN} Tabel Kosong! Jalankan Scan (01) dulu.")
                        time.sleep(2)
                    else:
                        from wifipro.attacks.handshake import HandshakeCapture
                        attacker = HandshakeCapture(self.wifi, colors)
                        attacker.start_capture(self.targets)

                # [03] DOS ATTACKS
                elif cmd == '3':
                    if not self.targets:
                        print(f"\n{colors.WARN} Tabel Kosong! Jalankan Scan (01) dulu.")
                        time.sleep(2)
                    else:
                        self.wifi.deauth.start_dos(self.targets)

                # [04] NETCUT
                elif cmd == '4':
                    from wifipro.attacks.netcut import NetCut
                    cutter = NetCut(self.wifi, colors)
                    cutter.start_attack()
                    
                # [05] SAVED PASSWORDS
                elif cmd == '5':
                    self._display_saved_passwords()
                    
                # [06] EVIL TWIN ATTACK
                elif cmd == '6':
                    if not self.targets:
                        print(f"\n{colors.WARN} Tabel Kosong! Jalankan Scan (01) dulu.")
                        time.sleep(2)
                    else:
                        try:
                            from wifipro.attacks.eviltwin import EvilTwin
                            val = input(f"\n{colors.Q} Select Target ID (1-{len(self.targets)}): ").strip()
                            if val:
                                target = self.targets[int(val)-1]
                                et = EvilTwin(self.wifi, colors)
                                et.start(target['essid'], target['ch'], target['bssid'])
                        except (ValueError, IndexError):
                            print(f"\n{colors.R}[!] ID tidak valid.{colors.NC}")
                            time.sleep(1)

                # [07] MITM
                elif cmd == '7':
                    if current_iface != "None":
                        self.processor.launch_mitm_attack(current_iface, colors.OK, colors.WARN)
                    else:
                        print(f"\n{colors.ERR} Select interface first!")
                        time.sleep(1)

                # [09] CLEANUP
                elif cmd == '9':
                    self.processor.cleanup_captures()

            except Exception as e:
                print(f"\n{colors.ERR} Error: {e}")
                time.sleep(2)