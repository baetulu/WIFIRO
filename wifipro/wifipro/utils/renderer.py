def format_target_table(targets, colors, line_width=105):
    """Fungsi khusus untuk me-render tabel target WiFi"""
    output = []
    
    # Header Tabel
    header_fmt = (f"  {colors.Y}{colors.BOLD}%-3s %-17s %-2s %-4s %-5s %-4s %-5s %-7s %-4s %-5s %-25s{colors.NC}")
    output.append(header_fmt % ("ID", "BSSID", "CH", "PWR", "DATA", "CLNT", "ENC", "AUTH", "WPS", "BEAC", "ESSID"))
    output.append(f"  {colors.DG}{'─' * line_width}{colors.NC}")

    # Baris Data
    for idx, t in enumerate(targets[:8]):
        try:
            pwr = int(t.get('pwr', 0))
        except: pwr = 0
        
        p_col = colors.G if pwr >= -60 else (colors.Y if pwr >= -75 else colors.R)
        wps_status = t.get('wps', 'NO')
        wps_col = colors.G if wps_status == "YES" else colors.NC

        row_fmt = f"  %-3s %-17s %-2s {p_col}%-4s{colors.NC} %-5s %-4s %-5s %-7s {wps_col}%-4s{colors.NC} %-5s %-25s"
        
        row = row_fmt % (
            str(idx+1), t.get('bssid', '-'), t.get('ch', '-'), str(pwr), 
            t.get('data', '0'), t.get('clients', '0'), t.get('enc', '-')[:5], 
            t.get('auth', '-')[:7], wps_status, t.get('beacons', '0'), t.get('essid', '-')[:25]
        )
        output.append(row)
        
    return "\n".join(output)
