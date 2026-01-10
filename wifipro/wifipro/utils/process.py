import subprocess
import os, time, sys
import shutil # Ditambahkan karena digunakan di cleanup_captures
from wifipro.utils.terminal import colors
from wifipro.core.scanner import WiFiScanner
from wifipro.attacks.deauth import DeauthAttack
from scapy.all import sniff, IP, TCP, UDP, DNS

class WirelessManager:
    
    def __init__(self, colors):
        """
        Upgrade: Menerima objek colors untuk dibagikan ke sub-modul
        """
        self.colors = colors
        self.iface = "None"
        self.targets = []
        
        # Lazy import tetap dipertahankan sesuai kode asli
        from wifipro.attacks.deauth import DeauthAttack
        from wifipro.core.scanner import WiFiScanner
        
        self.scanner = WiFiScanner(self)
        self.deauth = DeauthAttack(self, self.colors)
          
    def cleanup_captures(self):
        """
        Menghapus semua isi dari folder captures tanpa menghapus foldernya.
        """
        folder_path = 'captures'
    
        if not os.path.exists(folder_path):
            print(f"[-] Folder {folder_path} tidak ditemukan.")
            return

        print(f"[*] Membersihkan folder {folder_path}...")
    
        count = 0
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                # Cek jika itu file atau link, lalu hapus
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    count += 1
                # Jika ada sub-folder di dalam captures
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    count += 1
            except Exception as e:
                print(f"[-] Gagal menghapus {file_path}. Alasan: {e}")

        print(f"[+] Berhasil menghapus {count} file/folder di dalam captures.")

    def launch_mitm_attack(self, interface, ok, warn):
        """
        Jembatan untuk menjalankan serangan MITM
        """
        try:
            # Gunakan import di dalam fungsi (Lazy Import)
            from wifipro.attacks.mitm import PhantomMitmUltimate
            
            attacker = PhantomMitmUltimate()
            attacker.run(interface) 
            
        except ImportError as e:
            print(f"\n{warn} Error: Module MITM tidak ditemukan!")
            print(f"{warn} Log: {e}")
            time.sleep(2)
        except Exception as e:
            print(f"\n{warn} Terjadi kesalahan sistem: {e}")
            time.sleep(2)

    def get_interface(self):
        """Mendapatkan interface wireless aktif"""
        try:
            cmd = "iw dev | awk '/Interface/ {print $2}'"
            res = subprocess.check_output(cmd, shell=True).decode().strip().split('\n')
            return res[0] if res and res[0] != "" else "None"
        except:
            return "None"

    def set_ip_forward(self, status):
        # 0 = NetCut (Mati), 1 = MITM (Nyala)
        val = "1" if status else "0"
        os.system(f"echo {val} > /proc/sys/net/ipv4/ip_forward")
                
    def get_mac(self, iface):
        """Mendapatkan MAC Address interface"""
        if iface == "None": return "00:00:00:00:00:00"
        try:
            with open(f"/sys/class/net/{iface}/address", "r") as f:
                return f.read().strip().upper()
        except:
            return "00:00:00:00:00:00"

    def _run_cmd(self, command):
        """Helper untuk menjalankan perintah sistem"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            return result
        except Exception as e:
            return str(e)
            
    def get_mode_status(self, iface):
        """
        Mengecek apakah interface dalam mode monitor atau managed.
        Sangat penting untuk tampilan ON/OFF di menu utama.
        """
        if iface == "None" or not iface:
            return False
        
        check = self._run_cmd(f"iw dev {iface} info")
        # Jika output mengandung 'type monitor', berarti ON
        if "type monitor" in check.stdout:
            return True
        return False

    def ui_spoof_mac(self, iface):
        """Logika Spoofing MAC Address (Random)"""
        import time
        print(f"\n{self.colors.INFO} Preparing {self.colors.C}{iface}{self.colors.NC} for MAC Spoofing...")
        
        # 1. Matikan Interface (Wajib agar MAC bisa diganti)
        self._run_cmd(f"ip link set {iface} down")
        
        # 2. Jalankan macchanger
        print(f"{self.colors.INFO} Generating random MAC address...")
        res = self._run_cmd(f"macchanger -r {iface}")
        
        # 3. Nyalakan kembali
        self._run_cmd(f"ip link set {iface} up")
        
        if res.returncode == 0:
            # Ambil baris baru dari output macchanger untuk konfirmasi
            new_mac = [line for line in res.stdout.split('\n') if "New MAC" in line]
            print(f"{self.colors.OK} {self.colors.G}Success!{self.colors.NC}")
            if new_mac:
                print(f"    {self.colors.DG}{new_mac[0]}{self.colors.NC}")
        else:
            print(f"{self.colors.ERR} {self.colors.R}Failed! Make sure 'macchanger' is installed.{self.colors.NC}")
        
        input(f"\n{self.colors.INFO} Press Enter to return...")
        return
                
    def ui_select_interface(self):
        """WiFi Pro - Auto-selection Logic"""
        import time
        interfaces = self.get_all_interfaces()
        
        if not interfaces:
            print(f"  {self.colors.ERR} No wireless card found!")
            time.sleep(1.5)
            return

        # --- LOGIKA AUTO-SELECT (Anti Kesel) ---
        if len(interfaces) == 1:
            self.iface = interfaces[0]
            print(f"  {self.colors.OK} Only one interface found. {self.colors.G}Auto-selecting: {self.colors.Y}{self.iface}{self.colors.NC}")
            time.sleep(1) 
            return 

        # --- Jika lebih dari 1, baru tampilkan daftar ---
        print(f"  {self.colors.B}{self.colors.BOLD}[ AVAILABLE INTERFACES ]{self.colors.NC}\n")
        for i, name in enumerate(interfaces, 1):
            print(f"  {self.colors.W}[{i}]{self.colors.NC} {self.colors.C}{name}{self.colors.NC}")
        
        try:
            sel = input(f"\n  {self.colors.Q} Choice (1-{len(interfaces)}): ").strip()
            if sel and sel != '0':
                idx = int(sel) - 1
                if 0 <= idx < len(interfaces):
                    self.iface = interfaces[idx]
                    print(f"\n  {self.colors.OK} Target set to: {self.colors.G}{self.iface}{self.colors.NC}")
                    time.sleep(1)
        except:
            print(f"\n  {self.colors.ERR} Invalid selection!")
            time.sleep(1)
                
    def toggle_mode(self, iface):
        """
        Logika satu tombol: Jika ON matikan, jika OFF hidupkan.
        """
        if self.get_mode_status(iface):
            return self.set_managed_mode(iface)
        else:
            return self.set_monitor_mode(iface)
                   
    def set_monitor_mode(self, iface):
        """Versi Upgrade: Silent Killer + Monitor Mode + Auto Unblock"""
        # 1. Silent Killer
        self._run_cmd("airmon-ng check kill > /dev/null 2>&1")
        
        # 2. Pastikan tidak ada blokir software (RF-KILL)
        self._run_cmd("rfkill unblock wifi")

        # 3. Proses Ganti Mode (Method: iw)
        self._run_cmd(f"ip link set {iface} down")
        self._run_cmd(f"iw dev {iface} set type monitor")
        self._run_cmd(f"ip link set {iface} up")
        
        # 4. Backup Method (airmon-ng) - tetap silent
        self._run_cmd(f"airmon-ng start {iface} > /dev/null 2>&1")

        # 5. Verifikasi Dinamis
        interfaces = self.get_all_interfaces()
        for dev in interfaces:
            check = self._run_cmd(f"iw dev {dev} info")
            if "type monitor" in check.stdout:
                self.iface = dev 
                return True
        
        return False

    def set_managed_mode(self, iface):
        """Mengubah interface ke Managed Mode (Normal) & Restore Jaringan"""
        print(f"{self.colors.INFO} Reverting {self.colors.C}{iface}{self.colors.NC} to {self.colors.Y}Managed Mode{self.colors.NC}...")
        
        # 1. Deteksi dan matikan mode monitor via airmon-ng jika perlu
        clean_iface = iface.split()[0]
        
        if "mon" in clean_iface:
            print(f"{self.colors.INFO} Stopping airmon-ng on {self.colors.C}{clean_iface}{self.colors.NC}...")
            self._run_cmd(f"airmon-ng stop {clean_iface}")
            # Cari nama interface asli
            res = self._run_cmd("iw dev | awk '/Interface/ {print $2}'")
            ifres = res.stdout.strip().split('\n')
            clean_iface = ifres[0] if ifres[0] else clean_iface.replace("mon", "")

        # 2. Reset interface secara hardware
        print(f"{self.colors.INFO} Resetting interface state...")
        self._run_cmd(f"ip link set {clean_iface} down")
        self._run_cmd(f"iw dev {clean_iface} set type managed")
        self._run_cmd(f"ip link set {clean_iface} up")
        
        # 3. UNBLOCK RFKILL
        self._run_cmd(f"rfkill unblock wifi")
        
        # 4. RESTORE SERVICES
        print(f"{self.colors.INFO} Restarting NetworkManager...")
        self._run_cmd("systemctl restart NetworkManager")
        self._run_cmd("nmcli networking on")
        
        # Verifikasi akhir
        check = self._run_cmd(f"iw dev {clean_iface} info")
        if "type managed" in check.stdout:
            print(f"{self.colors.OK} Interface {self.colors.G}{clean_iface}{self.colors.NC} is now {self.colors.G}ONLINE{self.colors.NC}.")
            return True
        else:
            self._run_cmd(f"ifconfig {clean_iface} up")
            print(f"{self.colors.ERR} {self.colors.R}Failed to restore Managed Mode completely.{self.colors.NC}")
            return False
            
    def change_mac(self, iface):
        """Spoofing MAC Address menggunakan macchanger"""
        print(f"{self.colors.INFO} Randomizing MAC Address for {self.colors.C}{iface}{self.colors.NC}...")
        
        self._run_cmd(f"ip link set {iface} down")
        res = self._run_cmd(f"macchanger -r {iface}")
        self._run_cmd(f"ip link set {iface} up")
        
        if res.returncode == 0:
            print(f"{self.colors.OK} {self.colors.G}MAC Address changed successfully!{self.colors.NC}")
        else:
            print(f"{self.colors.ERR} {self.colors.R}MAC Spoofing failed. Is macchanger installed?{self.colors.NC}")

    def kill_conflicting(self):
        """Menghilangkan proses yang mengganggu"""
        print(f"{self.colors.INFO} Killing conflicting processes (NetworkConfig/wpa_supplicant)...")
        self._run_cmd("airmon-ng check kill")
        print(f"{self.colors.OK} {self.colors.G}Processes killed.{self.colors.NC}")

    def get_all_interfaces(self):
        """Mendapatkan daftar semua interface wireless"""
        res = self._run_cmd("iw dev | grep Interface | awk '{print $2}'")
        return res.stdout.strip().split('\n')