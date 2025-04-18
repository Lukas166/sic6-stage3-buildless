import network
import time
import machine
import ubinascii
import json
import dht
import urequests
from umqtt.simple import MQTTClient

# WiFi Credentials
WIFI_SSID = "AS-SYIFA_G"
WIFI_PASS = "Marhaban2002"

# API Endpoint
API_URL = "http://192.168.6.81:5000/api/sensor"  # Ganti sesuai IP backend kamu

# Ubidots MQTT Credentials
UBIDOTS_TOKEN = "BBUS-Wmhmg1XVKEEsq7NND8YtODkT1w6lqU"
MQTT_BROKER = "industrial.api.ubidots.com"
MQTT_PORT = 1883
DEVICE_LABEL = "esp32_device"

# Pin Konfigurasi
LDR_PIN = 34      # LDR Sensor (Analog)
LED_GREEN_PIN = 27 # LED Output
LED_YELLOW_PIN = 26
LED_RED_PIN = 25
DHT_PIN = 4       # DHT11 Sensor
PIR_PIN = 14      # PIR Sensor (Gerakan)
BUZZER_PIN = 18   # Buzzer

# Setup Perangkat
led_green = machine.Pin(LED_GREEN_PIN, machine.Pin.OUT)
led_yellow = machine.Pin(LED_YELLOW_PIN, machine.Pin.OUT)
led_red = machine.Pin(LED_RED_PIN, machine.Pin.OUT)
dht_sensor = dht.DHT11(machine.Pin(DHT_PIN))
ldr_sensor = machine.ADC(machine.Pin(LDR_PIN))
ldr_sensor.atten(machine.ADC.ATTN_11DB)  # Full range 0-3.3V
pir_sensor = machine.Pin(PIR_PIN, machine.Pin.IN)
buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)

# Unique MQTT Client ID
CLIENT_ID = ubinascii.hexlify(machine.unique_id()).decode()

# Koneksi WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)

    attempt = 0
    while not wlan.isconnected():
        time.sleep(2)
        attempt += 1
        print(f"Connecting to WiFi... Attempt {attempt}")
        if attempt > 10:
            print("❌ WiFi Connection Failed! Restarting...")
            machine.reset()
    
    print("✅ Connected to WiFi!")
    ip_info = wlan.ifconfig()
    print(f'IP Address: {ip_info[0]}')

# Connect to Ubidots MQTT Broker
def connect_mqtt():
    try:
        client = MQTTClient(CLIENT_ID, MQTT_BROKER, MQTT_PORT, user=UBIDOTS_TOKEN, password="")
        client.connect()
        print("✅ Connected to Ubidots MQTT!")
        return client
    except Exception as e:
        print(f"❌ MQTT Connection Failed: {e}")
        time.sleep(5)
        return None

# Publish Data to Ubidots
def publish_ubidots(client, data):
    if not client:
        print("⚠️ MQTT Client Not Connected!")
        return

    topic = f"/v1.6/devices/{DEVICE_LABEL}"
    payload = json.dumps(data)

    try:
        client.publish(topic, payload)
        print("✅ Sent data to Ubidots")
    except Exception as e:
        print(f"❌ Failed to Publish to Ubidots: {e}")

# Kirim Data ke API
def send_to_api(ldr, temperature, humidity, motion, led_status):
    data = {
        "light": ldr,
        "temperature": temperature,
        "humidity": humidity,
        "motion": motion,
        "led_status": led_status
    }

    try:
        headers = {"Content-Type": "application/json"}
        print(f"Sending data: {data}")
        response = urequests.post(API_URL, json=data, headers=headers)
        
        if response.status_code == 201:
            print("✅ Data sent successfully to local API")
            response.close()
            return True
        else:
            print(f"⚠️ Server error: {response.status_code}")
            response.close()
            return False

    except Exception as e:
        print(f"❌ Failed to send data to local API: {e}")
        return False

# Program Utama
def main():
    connect_wifi()
    mqtt_client = connect_mqtt()

    while True:
        try:
            # Baca sensor
            ldr_value = ldr_sensor.read()
            dht_sensor.measure()
            temperature = dht_sensor.temperature()
            humidity = dht_sensor.humidity()
            motion_detected = pir_sensor.value()

            # Kontrol LED berdasarkan cahaya
            if ldr_value < 2500:
                led_red.value(1)
                led_green.value(0)
                led_status = 1
                print("⚠️ Cahaya rendah - LED ON")
            else:
                led_red.value(0)
                led_green.value(1)
                led_status = 0
                print("✅ Cahaya cukup - LED OFF")

            # Kontrol buzzer berdasarkan gerakan
            buzzer.value(1 if motion_detected else 0)

            # Siapkan data untuk dikirim
            sensor_data = {
                "light": ldr_value,
                "temperature": temperature,
                "humidity": humidity,
                "motion": motion_detected,
                "led_status": led_status
            }

            # Kirim ke API lokal
            send_to_api(ldr_value, temperature, humidity, motion_detected, led_status)

            # Kirim ke Ubidots
            if mqtt_client:
                publish_ubidots(mqtt_client, sensor_data)
            else:
                # Coba reconnect jika koneksi hilang
                mqtt_client = connect_mqtt()

            time.sleep(5)  # Interval pengiriman data

        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)
            # Coba reconnect jika terjadi error
            if mqtt_client:
                mqtt_client.disconnect()
            mqtt_client = connect_mqtt()

# Jalankan Program
main()
