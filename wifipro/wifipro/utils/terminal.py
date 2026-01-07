#!/usr/bin/env python3
from colorama import Fore, Back, Style, init

# Inisialisasi Colorama
init(autoreset=False)

class Color:
    def __init__(self):
        # --- [ PALET WARNA ] ---
        self.R = Fore.LIGHTRED_EX          
        self.G = Fore.LIGHTGREEN_EX        
        self.Y = Fore.LIGHTYELLOW_EX       
        self.B = Fore.LIGHTBLUE_EX         
        self.P = Fore.LIGHTMAGENTA_EX      
        self.C = Fore.LIGHTCYAN_EX         
        self.W = Fore.LIGHTWHITE_EX        

        # Warna Gelap/Redup
        self.DG = Fore.BLACK + Style.BRIGHT 
        self.DR = Fore.RED                  
        self.DC = Fore.CYAN                 

        # Efek Khusus
        self.NC = Style.RESET_ALL           
        self.BOLD = Style.BRIGHT            
        self.UNDERLINE = '\033[4m'          
        self.BLINK = '\033[5m'              

        # --- [ SIMBOL KONSISTEN ] ---
        self.OK   = f"{self.G}[+]{self.NC}"   
        self.ERR  = f"{self.R}[-]{self.NC}"   
        self.WARN = f"{self.Y}[!]{self.NC}"   
        self.INFO = f"{self.C}[*]{self.NC}"   
        self.Q    = f"{self.Y}[?]{self.NC}"   
        
        # --- [ CONFIG GLOBAL TAMPILAN ] ---
        self.LINE_WIDTH = 78
        self.BANNER_CHAR = "─"

    def _display_system_status(self):
        """Mencetak baris status sistem: Host, Interface, MAC, dan Version"""
        import socket
        
        # Ambil data dari engine
        iface = getattr(self.wifi, 'iface', "None") if self.wifi else "None"
        mac_addr = self.wifi.get_mac(iface) if self.wifi else "00:00:00:00:00:00"
        
        try:
            current_host = socket.gethostname()
        except:
            current_host = "Unknown"

        # Cetak baris status
        status_line = (
            f"  {colors.DG}Host:  {colors.W}[{current_host}]  "
            f"{colors.DG}│  Iface:  {colors.C}[{iface}]  "
            f"{colors.DG}│  MAC:  {colors.Y}{mac_addr}{colors.NC}  "
            f"{colors.DG}│  Ver: {colors.W}{self.version}{colors.NC}"
        )
        print(status_line)
        colors.draw_line(colors.W)
    
            
    def _display_target_table(self):
        """Mencetak tabel target hasil scan jika tersedia"""
        line_width = 78 # Konsisten dengan lebar garis draw_line
        
        if hasattr(self, 'targets') and self.targets:
            from wifipro.utils.renderer import format_target_table
            # Cetak tabel menggunakan renderer eksternal
            print(format_target_table(self.targets, colors, line_width))
            colors.draw_line(colors.W)
            
    def draw_line(self, color_code=None):
        """Fungsi untuk menggambar garis konsisten menggunakan LINE_WIDTH global"""
        if color_code is None:
            color_code = self.W
        print(f"  {color_code}{self.BANNER_CHAR * self.LINE_WIDTH}{self.NC}")

# Membuat instance agar bisa langsung dipakai di modul lain
colors = Color()
