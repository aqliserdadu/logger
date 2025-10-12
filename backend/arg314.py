#!/usr/bin/env python3
import RPi.GPIO as GPIO
import time
import sys
import os
import sqlite3
from dotenv import load_dotenv
import random

# =============================
# Load Environment
# =============================
env_path = "/opt/logger/config/env"  # env file path
if not load_dotenv(dotenv_path=env_path):
    print(f"Error: env file not found at {env_path}")
    exit(1)

DB_PATH = os.getenv("SQLITE_DB_PATH", "/opt/logger/data/gpio_logger.db")

# =============================
# Fungsi Database
# =============================
def connect_db():
    """Membuka koneksi ke database SQLite."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def cekTable():
    """Cek dan buat tabel jika belum ada."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gpio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATETIME,
            sensor TEXT,
            nilai REAL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def insert_data_gpio(date, sensor, nilai):
    """Masukkan data sensor ke tabel gpio."""
    cekTable()  # Pastikan tabel ada
    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = """
            INSERT INTO gpio (date, sensor, nilai)
            VALUES (?, ?, ?);
        """
        values = (date, sensor, nilai)
        cursor.execute(query, values)
        conn.commit()
        print(f"[INFO] Data GPIO berhasil dimasukkan: {values}")
    except Exception as e:
        print(f"[ERROR] Gagal memasukkan data ke database: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

# =============================
# Konfigurasi Parameter
# =============================
ARG314_STATUS = os.getenv('ARG314_STATUS')
RAIN_SENSOR_PIN = int(os.getenv('RAIN_SENSOR_PIN', 18))
RESOLUTION = float(os.getenv('RESOLUTION', 0.202))
DEFAULT_INTERVAL = int(os.getenv('DELAY', 60))  # detik
DEBOUNCE_MS = int(os.getenv('DEBOUNCE_MS', 200))
DEMO_MODE = os.getenv('DEMO_MODE')

# =============================
# Variabel Global
# =============================
tipping_count = 0
last_interval = time.time()

# =============================
# Callback saat tipping terdeteksi
# =============================
def tipping_callback(channel):
    global tipping_count
    tipping_count += 1
    print(f"Tipping terdeteksi! Total: {tipping_count}")

# =============================
# Inisialisasi GPIO
# =============================
GPIO.setmode(GPIO.BCM)
GPIO.setup(RAIN_SENSOR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(RAIN_SENSOR_PIN, GPIO.FALLING,
                      callback=tipping_callback, bouncetime=DEBOUNCE_MS)

print("=== Rain Gauge Monitor ===")

# =============================
# Baca argumen interval dari command line
# =============================
if len(sys.argv) > 1:
    try:
        interval = int(sys.argv[1])
    except ValueError:
        interval = DEFAULT_INTERVAL
else:
    interval = DEFAULT_INTERVAL

print(f"Interval pembacaan: {interval} Menit")

# =============================
# Loop utama
# =============================
try:
    last_logged_minute = -1
    interval_minutes = interval

    while True:
        now = time.localtime()
        current_minute = now.tm_min
        current_second = now.tm_sec

        if ARG314_STATUS.lower() != "active":
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sensor ARG314 tidak aktif. Menunggu...")
            time.sleep(10)
            

        # Setiap menit ke-n sesuai interval
        if current_second == 0 and (current_minute % interval_minutes == 0) and current_minute != last_logged_minute:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            
            if DEMO_MODE == "active":
                tipping_count = random.randint(0, 60)  # Simulasi tipping acak antara 0-60
                print(f"[DEMO MODE] Simulasi tipping count: {tipping_count}")
                
            rainfall_mm = tipping_count * RESOLUTION 
            print(f"[{timestamp}] Tipping: {tipping_count} | Curah hujan: {rainfall_mm:.3f} mm")
            # Simpan ke database
            insert_data_gpio(timestamp, "rain_sensor", rainfall_mm)
            # Reset counter
            tipping_count = 0
            last_logged_minute = current_minute

        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nDihentikan oleh user.")

finally:
    GPIO.cleanup()
    print("GPIO dibersihkan dan program dihentikan.")
