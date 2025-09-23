import time
import os
from at500 import get_at500_data
from mace import get_mace_data
from spectro import read_modbus_tcp
from rt200 import get_rt200_data
from sem5096 import get_sem5096_data
from config import insert_data, ambilDate, ambilDateTime
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
env_path = "/opt/logger/config/env"
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

# Configuration from environment variables
DELAY = int(os.getenv('DELAY'))
AT500_STATUS = os.getenv('AT500_STATUS')
MACE_STATUS = os.getenv('MACE_STATUS')
SPECTRO_STATUS = os.getenv('SPECTRO_STATUS')
RT200_STATUS = os.getenv('RT200_STATUS')
SEM5096_STATUS = os.getenv('SEM5096_STATUS')

def should_run():
    """Check if the script should run based on the current time and DELAY setting."""
    now = datetime.now()
    return now.minute % DELAY == 0 and now.second == 0

def main():
    current_date = ambilDate()
    print(f"[{current_date}] ⏱️ Service dimulai. Menunggu waktu eksekusi sensor setiap {DELAY} menit.")
    last_run = None
    
    # Initialize variables with default values (None)
    ph, orp, tds, conduct, do, salinity, nh3n = (None,) * 7
    battery, depth, flow, tflow = (None,) * 4
    turb, tss, cod, bod, no3, temp = (None,) * 6
    press, hum, wspeed, wdir, rain, srad = (None,) * 6
    
    try:
        while True:
            now = datetime.now()
            if should_run():
                # Ensure we don't run twice at the same time
                if last_run != now.replace(second=0, microsecond=0):
                    current_date = ambilDate()
                    current_datetime = ambilDateTime()
                    print(f"\n[{current_date}] 📡 Membaca semua sensor...")
                    
                    status_filter = True
                    
                    # === AT500 ===
                    if AT500_STATUS.lower() == "active":
                        at500_data = get_at500_data()
                        if at500_data:
                            ph, orp, tds, conduct, do, salinity, nh3n = at500_data
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data AT500.")
                    
                    # === RT200 ===
                    if RT200_STATUS.lower() == "active":
                        rt200_data = get_rt200_data()
                        if rt200_data:
                            temp_rt200, press_rt200, depth_rt200 = rt200_data
                            # Use RT200 values if not already set
                            temp = temp_rt200 if temp is None else temp
                            press = press_rt200 if press is None else press
                            depth = depth_rt200 if depth is None else depth
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data RT200.")
                    
                    # === SEM5096 ===
                    if SEM5096_STATUS.lower() == "active":
                        sem5096_data = get_sem5096_data()
                        if sem5096_data:
                            temp_sem5096, hum_sem5096, press_sem5096, wspeed_sem5096, wdir_sem5096, rain_sem5096, srad_sem5096 = sem5096_data
                            # Use SEM5096 values if not already set
                            temp = temp_sem5096 if temp is None else temp
                            hum = hum_sem5096 if hum is None else hum
                            press = press_sem5096 if press is None else press
                            wspeed = wspeed_sem5096 if wspeed is None else wspeed
                            wdir = wdir_sem5096 if wdir is None else wdir
                            rain = rain_sem5096 if rain is None else rain
                            srad = srad_sem5096 if srad is None else srad
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data SEM5096.")
                    
                    
                    # === MACE ===
                    if MACE_STATUS.lower() == "active":
                        mace_data = get_mace_data()
                        if mace_data:
                            battery_mace, depth_mace, flow_mace, tflow_mace = mace_data
                            # Use MACE values if not already set
                            battery = battery_mace if battery is None else battery
                            depth = depth_mace if depth is None else depth
                            flow = flow_mace if flow is None else flow
                            tflow = tflow_mace if tflow is None else tflow
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data MACE.")
                    
                    # === SPECTRO ===
                    if SPECTRO_STATUS.lower() == "active":
                        modbus_data = read_modbus_tcp()
                        if modbus_data:
                            turb, tss, cod, bod, no3, temp_spectro = modbus_data
                            # Use SPECTRO temperature value if not already set
                            temp = temp_spectro if temp is None else temp
                        else:
                            status_filter = False
                            print(f"[{current_date}] ⚠️ Gagal membaca data Modbus TCP.")
                    
                    
                    # Save data if all active sensors were read successfully
                    if status_filter:
                        # Check if any sensor is active
                        if all(status.lower() != "active" for status in [AT500_STATUS, MACE_STATUS, SPECTRO_STATUS, SEM5096_STATUS, RT200_STATUS]):
                            print(f"[{current_date}] ⚠️ Semua modul sensor tidak aktif. Melewati penyimpanan data.")
                        else:
                            print(f"[{current_date}] ✅ Semua data sensor berhasil terbaca.")
                            print("\n=== SENSOR DATA ===")
                            print(f"→ pH: {ph}, ORP: {orp}, TDS: {tds}, Conductivity: {conduct}, DO: {do}, Salinity: {salinity}, NH3-N: {nh3n}")
                            print(f"→ Battery: {battery}, Depth: {depth}, Flow: {flow}, TFlow: {tflow}")
                            print(f"→ Turbidity: {turb}, TSS: {tss}, COD: {cod}, BOD: {bod}, NO3: {no3}, Temp: {temp}")
                            print(f"→ Press: {press} Hum: {hum}, WSpeed: {wspeed}, WDir: {wdir}, Rain: {rain}, SRad: {srad}")
                            print("===================  \n")
                            
                            insert_data(
                                current_date,
                                current_datetime,
                                ph, orp, tds, conduct, do, salinity, nh3n,
                                battery, depth, flow, tflow,
                                turb, tss, cod, bod, no3, temp,
                                press, hum, wspeed, wdir, rain, srad
                            )
                    else:
                        print(f"[{current_date}] ❌ Tidak semua sensor berhasil terbaca. Data tidak disimpan.")
                    
                    last_run = now.replace(second=0, microsecond=0)
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print(f"\n[{current_date}] 🛑 Service dihentikan secara manual.")

if __name__ == "__main__":
    main()
