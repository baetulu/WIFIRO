import subprocess
import os, time, sys
from wifipro.utils.terminal import colors
from wifipro.core.scanner import WiFiScanner # Import class baru
from wifipro.attacks.deauth import DeauthAttack # Import modul attack
from scapy.all import sniff, IP, TCP, UDP, DNS
class WirelessManager:
    
    def __init__(self, colors):
        """
        Upgrade: Menerima objek colors untuk dibagikan ke sub-modul
        """
        self.colors = colors
        self.iface = "None"
        self.targets = []
        from wifipro.attacks.deauth import DeauthAttack
        self.deauth = DeauthAttack(self, self.colors)
        
        from wifipro.core.scanner import WiFiScanner
        from wifipro.attacks.deauth import DeauthAttack
        
        self.scanner = WiFiScanner(self)
        self.deauth = DeauthAttack(self, self.colors)
        
    def launch_airodump(self, interface, ok, warn):
        # Delegate (serahkan) tugas ke class scanner
        self.targets = self.scanner.launch_airodump(interface, ok, warn)
        
    def start_dos(self, targets):
        """Memanggil mesin serangan Deauth"""
        self.deauth.ui_dos_menu(targets)    
    
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
        print(f"\n{colors.INFO} Preparing {colors.C}{iface}{colors.NC} for MAC Spoofing...")
        
        # 1. Matikan Interface (Wajib agar MAC bisa diganti)
        self._run_cmd(f"ip link set {iface} down")
        
        # 2. Jalankan macchanger
        print(f"{colors.INFO} Generating random MAC address...")
        res = self._run_cmd(f"macchanger -r {iface}")
        
        # 3. Nyalakan kembali
        self._run_cmd(f"ip link set {iface} up")
        
        if res.returncode == 0:
            # Ambil baris baru dari output macchanger untuk konfirmasi
            new_mac = [line for line in res.stdout.split('\n') if "New MAC" in line]
            print(f"{colors.OK} {colors.G}Success!{colors.NC}")
            if new_mac:
                print(f"    {colors.DG}{new_mac[0]}{colors.NC}")
        else:
            print(f"{colors.ERR} {colors.R}Failed! Make sure 'macchanger' is installed.{colors.NC}")
        
        input(f"\n{colors.INFO} Press Enter to return...")
        return
                
    def ui_select_interface(self):
        """WiFi Pro - Auto-selection Logic"""
        import time
        interfaces = self.get_all_interfaces()
        
        if not interfaces:
            print(f"  {colors.ERR} No wireless card found!")
            time.sleep(1.5)
            return

        # --- LOGIKA AUTO-SELECT (Anti Kesel) ---
        if len(interfaces) == 1:
            self.iface = interfaces[0]
            print(f"  {colors.OK} Only one interface found. {colors.G}Auto-selecting: {colors.Y}{self.iface}{colors.NC}")
            time.sleep(1) # Beri jeda sebentar biar user sempat baca
            return # Langsung keluar, lanjut ke menu berikutnya

        # --- Jika lebih dari 1, baru tampilkan daftar ---
        print(f"  {colors.B}{colors.BOLD}[ AVAILABLE INTERFACES ]{colors.NC}\n")
        for i, name in enumerate(interfaces, 1):
            print(f"  {colors.W}[{i}]{colors.NC} {colors.C}{name}{colors.NC}")
        
        try:
            sel = input(f"\n  {colors.Q} Choice (1-{len(interfaces)}): ").strip()
            if sel and sel != '0':
                idx = int(sel) - 1
                if 0 <= idx < len(interfaces):
                    self.iface = interfaces[idx]
                    print(f"\n  {colors.OK} Target set to: {colors.G}{self.iface}{colors.NC}")
                    time.sleep(1)
        except:
            print(f"\n  {colors.ERR} Invalid selection!")
            time.sleep(1)
    def change_hostname(self, new_name):
        """Mengubah hostname sistem secara instan"""
        import time
        try:
            # Ganti untuk sesi saat ini
            self._run_cmd(f"hostname {new_name}")
            # Ganti secara permanen di systemd
            self._run_cmd(f"hostnamectl set-hostname {new_name}")
            
            print(f"\n  {colors.OK} Hostname identity changed to: {colors.W}{new_name}{colors.NC}")
        except Exception as e:
            print(f"\n  {colors.ERR} Failed to change hostname: {e}")
        
        time.sleep(1.5)
                
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
        # 1. Silent Killer: Matikan proses pengganggu tanpa banyak tanya
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
                # Update variabel global engine ke nama dev baru (misal wlan0 -> wlan0mon)
                self.iface = dev 
                return True
        
        return False

    def launch_handshake_capture(self, targets):
        """Jembatan menuju modul Handshake"""
        from wifipro.attacks.handshake import HandshakeCapture
        attacker = HandshakeCapture(self, self.colors)
        attacker.start_capture(targets)
        
    def set_managed_mode(self, iface):
        """Mengubah interface ke Managed Mode (Normal) & Restore Jaringan"""
        print(f"{colors.INFO} Reverting {colors.C}{iface}{colors.NC} to {colors.Y}Managed Mode{colors.NC}...")
        
        # 1. Deteksi dan matikan mode monitor via airmon-ng jika perlu
        # Kita hapus spasi atau info tambahan jika ada (seperti 'wlan0 [MON]')
        clean_iface = iface.split()[0]
        
        if "mon" in clean_iface:
            print(f"{colors.INFO} Stopping airmon-ng on {colors.C}{clean_iface}{colors.NC}...")
            self._run_cmd(f"airmon-ng stop {clean_iface}")
            # Setelah stop, kita cari nama interface aslinya lagi
            res = self._run_cmd("iw dev | awk '/Interface/ {print $2}'")
            ifres = res.stdout.strip().split('\n')
            clean_iface = ifres[0] if ifres[0] else clean_iface.replace("mon", "")

        # 2. Reset interface secara hardware
        print(f"{colors.INFO} Resetting interface state...")
        self._run_cmd(f"ip link set {clean_iface} down")
        self._run_cmd(f"iw dev {clean_iface} set type managed")
        self._run_cmd(f"ip link set {clean_iface} up")
        
        # 3. UNBLOCK RFKILL (Mencegah hardware disabled)
        self._run_cmd(f"rfkill unblock wifi")
        
        # 4. RESTORE SERVICES (NetworkManager harus hidup kembali)
        print(f"{colors.INFO} Restarting NetworkManager...")
        # Kita jalankan keduanya untuk memastikan kompatibilitas berbagai versi Kali
        self._run_cmd("systemctl restart NetworkManager")
        self._run_cmd("nmcli networking on")
        
        # Verifikasi akhir
        check = self._run_cmd(f"iw dev {clean_iface} info")
        if "type managed" in check.stdout:
            print(f"{colors.OK} Interface {colors.G}{clean_iface}{colors.NC} is now {colors.G}ONLINE{colors.NC}.")
            return True
        else:
            # Jika masih gagal, coba paksa up sekali lagi
            self._run_cmd(f"ifconfig {clean_iface} up")
            print(f"{colors.ERR} {colors.R}Failed to restore Managed Mode completely.{colors.NC}")
            return False
            
    def change_mac(self, iface):
        """Spoofing MAC Address menggunakan macchanger"""
        print(f"{colors.INFO} Randomizing MAC Address for {colors.C}{iface}{colors.NC}...")
        
        self._run_cmd(f"ip link set {iface} down")
        res = self._run_cmd(f"macchanger -r {iface}")
        self._run_cmd(f"ip link set {iface} up")
        
        if res.returncode == 0:
            print(f"{colors.OK} {colors.G}MAC Address changed successfully!{colors.NC}")
        else:
            print(f"{colors.ERR} {colors.R}MAC Spoofing failed. Is macchanger installed?{colors.NC}")

    def kill_conflicting(self):
        """Menghilangkan proses yang mengganggu (seperti airmon-ng check kill)"""
        print(f"{colors.INFO} Killing conflicting processes (NetworkManager/wpa_supplicant)...")
        self._run_cmd("airmon-ng check kill")
        print(f"{colors.OK} {colors.G}Processes killed.{colors.NC}")

    def get_all_interfaces(self):
        """Mendapatkan daftar semua interface wireless"""
        res = self._run_cmd("iw dev | grep Interface | awk '{print $2}'")
        return res.stdout.strip().split('\n')
