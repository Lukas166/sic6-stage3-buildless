import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
import google.generativeai as genai
from datetime import datetime
from PIL import Image
from twilio.rest import Client
import time
from streamlit_autorefresh import st_autorefresh

# Atur layout ke wide mode
st.set_page_config(layout="wide")
    
# ------------------ 🎨 Konfigurasi Tema ------------------ #
warna_utama = "#2C3E50"  # Biru tua
warna_sekunder = "#1E8449"  # Hijau tua
warna_teks = "#FFFFFF"  # Putih
warna_aksen = "#27AE60"  # Hijau terang

tema_kustom = f"""
<style>
:root {{
    --warna-utama: {warna_utama};
    --warna-sekunder: {warna_sekunder};
    --warna-teks: {warna_teks};
    --warna-aksen: {warna_aksen};
}}

[data-testid="stAppViewContainer"] {{
    background-color: var(--warna-utama);
    color: var(--warna-teks);
}}

[data-testid="stSidebar"] {{
    background-color: var(--warna-utama) !important;
}}

.st-bb, .st-at, .st-ae, .st-af, .st-ag, .st-ah, .st-ai, .st-aj, .st-ak, .st-al, .st-am, .st-an, .st-ao, .st-ap, .st-aq, .st-ar, .st-as {{
    background-color: var(--warna-utama);
}}

.css-1aumxhk {{
    background-color: var(--warna-utama);
    background-image: none;
}}

.st-bh, .st-bi, .st-bj, .st-bk, .st-bl, .st-bm, .st-bn, .st-bo, .st-bp, .st-bq, .st-br, .st-bs, .st-bt, .st-bu, .st-bv, .st-bw {{
    color: var(--warna-teks);
}}

.css-1v3fvcr {{
    color: var(--warna-teks);
}}

.stButton>button {{
    background-color: var(--warna-sekunder);
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 24px;
}}

.stButton>button:hover {{
    background-color: var(--warna-aksen);
    color: white;
}}

.stTextInput>div>div>input, .stTextArea>div>div>textarea {{
    background-color: #34495E;
    color: white;
}}

.stSelectbox>div>div>select {{
    background-color: #34495E;
    color: white;
}}

.stDateInput>div>div>input {{
    background-color: #34495E;
    color: white;
}}

.stMetric {{
    background-color: #34495E;
    border-radius: 10px;
    padding: 15px;
}}

.stExpander {{
    background-color: #34495E;
    border-radius: 20px;
}}

.stTabs [data-baseweb="tab-list"] {{
    gap: 20px;
}}

.stTabs [data-baseweb="tab"] {{
    background-color: #34495E;
    border-radius: 5px 5px 0px 0px;
    padding: 10px 80px;
}}

.stTabs [aria-selected="true"] {{
    background-color: var(--warna-sekunder);
}}

/* Membuat konten full width */
.main .block-container {{
    max-width: 100%;
    padding-left: 5rem;
    padding-right: 5rem;
}}
</style>
"""

st.markdown(tema_kustom, unsafe_allow_html=True)

# ------------------ 🔌 Konfigurasi API ------------------ #
kunci_api = 'AIzaSyD8xS-ZaADNTU2iItF6z-JmSehi_Z9gb7Q'  # Untuk produksi, gunakan st.secrets
genai.configure(api_key=kunci_api)
model = genai.GenerativeModel("gemini-1.5-flash")

konfigurasi_generasi = {
    "max_output_tokens": 500,
    "temperature": 1,
    "top_k": 1
}

# ------------------ 🖼️ Bagian Hero ------------------ #
def bagian_hero():
    st.markdown(
        f"""
        <div style="background-color:{warna_sekunder};padding:2rem;border-radius:10px;margin-bottom:2rem;text-align:center;">
            <h1 style="color:{warna_teks};font-size:3.5rem;margin-bottom:0.5rem;">🌿 PlantVeillance</h1>
            <p style="color:{warna_teks};font-size:1.2rem;">Sistem Monitoring & Perawatan Tanaman Cerdas</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# ------------------ 📡 Fungsi Ambil Data ------------------ #
@st.cache_data(ttl=300)  # Cache selama 5 menit
def ambil_data_sensor_terbaru():
    try:
        response = requests.get("http://localhost:5000/api/sensor/latest", timeout=5)
        return response.json() if response.status_code == 200 else {}
    except requests.exceptions.RequestException:
        return {}

@st.cache_data(ttl=300)  # Cache selama 5 menit
def ambil_semua_data_sensor():
    try:
        response = requests.get("http://localhost:5000/api/sensor/all", timeout=5)
        return response.json() if response.status_code == 200 else []
    except requests.exceptions.RequestException:
        return []

# ------------------ 📊 Fungsi Visualisasi ------------------ #
def buat_metrik_sensor(data):
    if not data:
        return st.warning("Tidak ada data sensor yang tersedia")
    
    kolom = st.columns(5)
    metrik = [
        ("🌡️ Suhu", f"{data.get('temperature', 'N/A')} °C", "#E74C3C"),
        ("💧 Kelembaban", f"{data.get('humidity', 'N/A')} %", "#3498DB"),
        ("☀️ Cahaya", f"{data.get('light', 'N/A')} Lux", "#F1C40F"),
        ("🚶 Gerakan", "Terdeteksi" if data.get('motion') else "Tidak Ada", "#9B59B6"),
        ("💡 LED", "HIDUP" if data.get('led_status') else "MATI", "#2ECC71")
    ]
    
    for col, (label, nilai, warna), in zip(kolom, metrik):
        with col:
            st.markdown(
                f"""
                <div style="background-color:#34495E;padding:1rem;border-radius:10px;text-align:center;">
                    <p style="color:{warna};font-size:1.5rem;margin-bottom:0.2rem;">{label}</p>
                    <p style="color:white;font-size:1.8rem;font-weight:bold;margin-top:0;">{nilai}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

def plot_tren_sensor(df):
    if 'timestamp' not in df.columns:
        st.warning("Tidak ada data timestamp untuk tren")
        return
    
    tab = st.tabs(["📈 Grafik Garis", "📊 Distribusi", "🔗 Korelasi"])
    
    with tab[0]:
        st.subheader("Tren Sensor dari Waktu ke Waktu")
        fig, ax = plt.subplots(3, 1, figsize=(10, 12), sharex=True)
        
        # Suhu
        ax[0].plot(df['timestamp'], df['temperature'], color='#E74C3C')
        ax[0].set_ylabel('Suhu (°C)')
        ax[0].grid(True, alpha=0.3)
        
        # Kelembaban
        ax[1].plot(df['timestamp'], df['humidity'], color='#3498DB')
        ax[1].set_ylabel('Kelembaban (%)')
        ax[1].grid(True, alpha=0.3)
        
        # Cahaya
        ax[2].plot(df['timestamp'], df['light'], color='#F1C40F')
        ax[2].set_ylabel('Cahaya (Lux)')
        ax[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with tab[1]:
        st.subheader("Distribusi Data Sensor")
        fig, ax = plt.subplots(1, 3, figsize=(15, 4))
        
        ax[0].hist(df['temperature'], bins=15, color='#E74C3C')
        ax[0].set_title('Distribusi Suhu')
        
        ax[1].hist(df['humidity'], bins=15, color='#3498DB')
        ax[1].set_title('Distribusi Kelembaban')
        
        ax[2].hist(df['light'], bins=15, color='#F1C40F')
        ax[2].set_title('Distribusi Cahaya')
        
        plt.tight_layout()
        st.pyplot(fig)
    
    with tab[2]:
        st.subheader("Korelasi Sensor")
        fig, ax = plt.subplots(1, 2, figsize=(12, 5))
        
        ax[0].scatter(df['temperature'], df['humidity'], alpha=0.6, color='#9B59B6')
        ax[0].set_xlabel('Suhu (°C)')
        ax[0].set_ylabel('Kelembaban (%)')
        
        ax[1].scatter(df['light'], df['temperature'], alpha=0.6, color='#27AE60')
        ax[1].set_xlabel('Cahaya (Lux)')
        ax[1].set_ylabel('Suhu (°C)')
        
        plt.tight_layout()
        st.pyplot(fig)

# ------------------ 🧠 Fungsi Analisis AI ------------------ #
def analisis_kondisi_tanaman(data_sensor, info_tanaman):
    with st.spinner("🔍 Menganalisis kondisi tanaman..."):
        prompt = f"""
Analisis kondisi tanaman secara singkat (maksimal 1500 character) dan berikan rekomendasi yang dapat ditindaklanjuti:

🌿 Profil Tanaman:
- Jenis: {info_tanaman['jenis']}
- Tahap Pertumbuhan: {info_tanaman['tahap']}
- Terakhir Disiram: {info_tanaman['terakhir_siram']}
- Media Tanam: {info_tanaman['media']}
- Gejala: {info_tanaman['gejala']}

📊 Pembacaan Sensor:
- Suhu: {data_sensor.get('temperature', 'N/A')}°C
- Kelembaban: {data_sensor.get('humidity', 'N/A')}%
- Cahaya: {data_sensor.get('light', 'N/A')} lux
- Gerakan: {"Terdeteksi" if data_sensor.get('motion') else "Tidak Ada"}
- Status LED: {"HIDUP" if data_sensor.get('led_status') else "MATI"}

Berikan:
1. Penilaian kondisi saat ini
2. Rekomendasi perawatan segera
3. Status saat ini baik, butuh perawatan, atau krisis

Format respons dengan heading jelas dan poin-poin.
"""
        try:
            response = model.generate_content(prompt, generation_config=konfigurasi_generasi)
            return response.text
        except Exception as e:
            return f"Error dalam analisis: {str(e)}"

# ------------------ 🏠 Halaman Beranda ------------------ #
def halaman_beranda():
    st.markdown("""
    ## Selamat Datang di PlantVeillance
    
    Sistem monitoring tanaman cerdas yang menggabungkan sensor IoT dengan analisis AI untuk menjaga tanaman Anda tumbuh subur.
    
    ### Fitur Utama:
    - 🌡️ Monitoring lingkungan real-time
    - 🔍 Analisis kesehatan tanaman berbasis AI
    - 💧 Rekomendasi penyiraman cerdas
    - 📊 Pelacakan data historis
    - ⚠️ Sistem peringatan untuk kondisi abnormal
    
    ### Memulai:
    1. Anda bisa mihat data sensor real-time di tab **Monitoring**
    2. Dapatkan saran perawatan di tab **Analisis**
    3. Silahkan cari pertanyaan anda pada tab **FAQ**
    4. Anda bisa mengirim hasil analisis ke SMS lewat tab **Kirim Hasil Analisis**
    """)

    # Placeholder untuk video demo
    st.markdown("""
    <div style="background-color:#34495E;padding:2rem;border-radius:10px;text-align:center;">
        <p style="color:white;font-size:1.2rem;">📹 Video Demo Produk</p>
        <div style="background-color:#2C3E50;height:600px;width:100%;display:flex;align-items:center;justify-content:center;border-radius:5px;">
            <iframe width="80%" height="80%" src="https://www.youtube.com/embed/aZqCFE_9U9o" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ------------------ 📊 Halaman Monitoring ------------------ #
def halaman_monitoring():
    st.header("Monitoring Tanaman Real-time")

    data_terbaru = ambil_data_sensor_terbaru()
    semua_data = ambil_semua_data_sensor()

    st.subheader("Status Tanaman Saat Ini")
    buat_metrik_sensor(data_terbaru)

    st.subheader("Data Historis")
    if semua_data:
        df = pd.DataFrame(semua_data)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            df = df.tail(20)  # Ambil 20 data terakhir

        with st.expander("Lihat Data Mentah"):
            st.dataframe(df, use_container_width=True)

        plot_tren_sensor(df)
    else:
        st.info("Belum ada data historis yang tersedia.")

# ------------------ 🔍 Halaman Analisis ------------------ #
def halaman_analisis():
    st.header("Analisis Kesehatan Tanaman")
    
    # Form informasi tanaman
    with st.form("form_info_tanaman"):
        st.subheader("Informasi Tanaman")
        
        kol1, kol2 = st.columns(2)
        with kol1:
            jenis_tanaman = st.text_input("Jenis Tanaman", placeholder="Contoh: Tomat, Mawar, Lidah Mertua")
            tahap_pertumbuhan = st.selectbox("Tahap Pertumbuhan", ["Bibit", "Tanaman Muda", "Dewasa", "Berbunga/Berbuah"])
            terakhir_siram = st.date_input("Tanggal Terakhir Disiram")
        
        with kol2:
            media_tanam = st.selectbox("Media Tanam", ["Tanah", "Sekam Bakar", "Cocopeat", "Hydroton", "Campuran"])
            gejala = st.text_area("Gejala yang Diamati", placeholder="Contoh: Daun menguning, bercak coklat, batang layu")
        
        submitted = st.form_submit_button("Analisis Kesehatan Tanaman")
    
    if submitted:
        if not jenis_tanaman:
            st.warning("Harap masukkan jenis tanaman")
            return
        
        # Siapkan data
        data_sensor = ambil_data_sensor_terbaru()
        info_tanaman = {
            'jenis': jenis_tanaman,
            'tahap': tahap_pertumbuhan,
            'terakhir_siram': terakhir_siram.strftime("%Y-%m-%d"),
            'media': media_tanam,
            'gejala': gejala if gejala else "Tidak ada gejala yang dilaporkan"
        }
        
        # Lakukan analisis
        hasil_analisis = analisis_kondisi_tanaman(data_sensor, info_tanaman)

        # ✅ Simpan ke session_state agar bisa diakses dari tab laporan
        st.session_state['last_analysis'] = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'analysis': hasil_analisis
        }
        st.session_state['last_sensor_data'] = data_sensor

        # Tampilkan hasil
        st.subheader("Hasil Analisis")
        with st.expander("🔍 Analisis Detail", expanded=True):
            st.markdown(hasil_analisis)
        
        # Rekomendasi
        st.subheader("Tindakan yang Direkomendasikan")
        st.markdown("""
        - 💧 **Penyiraman**: Sesuaikan berdasarkan kelembaban tanah (pertimbangkan sistem penyiraman cerdas)
        - 🌞 **Pencahayaan**: Optimalkan paparan cahaya berdasarkan kebutuhan tanaman
        - 🌡️ **Suhu**: Pertahankan dalam kisaran ideal untuk spesies tanaman Anda
        - 🌱 **Nutrisi**: Pertimbangkan jadwal pemupukan
        """)

# ------------------ ❓ Halaman FAQ ------------------ #
def halaman_faq():
    st.header("Pertanyaan yang Sering Diajukan")
    
    with st.expander("Seberapa sering saya harus menyiram tanaman?"):
        st.markdown("""
        Frekuensi penyiraman tergantung pada:
        - Jenis tanaman
        - Tahap pertumbuhan
        - Kondisi lingkungan
        - Media tanam
        
        Sistem kami menganalisis faktor-faktor ini untuk memberikan rekomendasi yang dipersonalisasi.
        """)
    
    with st.expander("Berapa suhu ideal untuk tanaman saya?"):
        st.markdown("""
        Kebanyakan tanaman hias tumbuh subur antara 18-24°C, tetapi:
        - Tanaman tropis menyukai suhu lebih hangat
        - Sukulen dapat mentolerir kisaran lebih luas
        - Bibit membutuhkan kehangatan yang konsisten
        
        Periksa kebutuhan spesifik tanaman Anda di database kami.
        """)
    
    with st.expander("Bagaimana cara membaca data sensor cahaya?"):
        st.markdown("""
        - **< 1000 lux**: Cahaya rendah (cocok untuk tanaman teduh)
        - **1000-5000 lux**: Cahaya sedang (sebagian besar tanaman hias)
        - **5000-10000 lux**: Cahaya terang (sukulen, tanaman berbuah)
        - **> 10000 lux**: Sinar matahari langsung (hanya untuk tanaman yang menyukai matahari)
        """)
        
    with st.expander("Seberapa sering saya harus menyiram tanaman pot?"):
        st.markdown("""
        Frekuensi penyiraman tergantung pada jenis tanaman, ukuran pot, media tanam, dan kondisi lingkungan.

        **Panduan umum:**
        - Tanaman tropis: Setiap hari atau dua hari sekali.
        - Sukulen dan kaktus: Seminggu sekali atau saat media benar-benar kering.
        - Tanaman berbunga: Lebih sering saat berbunga.

        Pastikan pot memiliki lubang drainase agar akar tidak membusuk.
        """)

    with st.expander("Media tanam apa yang terbaik untuk pot?"):
        st.markdown("""
        Media tanam ideal harus ringan, memiliki drainase baik, dan kaya nutrisi.

        **Campuran umum:**
        - Tanah taman + kompos + perlite/pasir kasar.
        - Hindari tanah kebun langsung karena terlalu padat dan miskin sirkulasi udara.
        """)

    with st.expander("Apakah saya perlu memupuk tanaman pot?"):
        st.markdown("""
        Ya, karena nutrisi di pot cepat habis akibat penyiraman.

        **Tips pemupukan:**
        - Pupuk cair: 2–4 minggu sekali.
        - Pupuk slow-release: 2–3 bulan sekali.
        - Sesuaikan pupuk dengan fase pertumbuhan (daun/bunga/buah).
        """)

    with st.expander("Bagaimana cara mengetahui tanaman saya kekurangan air?"):
        st.markdown("""
        **Tanda-tanda umum:**
        - Daun layu dan menggulung
        - Media tanam sangat kering dan terlepas dari tepi pot
        - Warna daun menguning dari bawah

        Lakukan penyiraman perlahan sampai air keluar dari dasar pot.
        """)

    with st.expander("Apakah sinar matahari langsung baik untuk semua tanaman pot?"):
        st.markdown("""
        Tidak semua tanaman menyukai sinar matahari langsung.

        **Umum:**
        - Tanaman tropis: Cahaya terang tidak langsung.
        - Sukulen/kaktus: Sinar matahari langsung.
        - Tanaman indoor: Cahaya redup hingga sedang.

        Cek kebutuhan cahaya berdasarkan jenis tanaman.
        """)

    with st.expander("Berapa kali saya harus mengganti media tanam?"):
        st.markdown("""
        Media tanam sebaiknya diganti setiap 6–12 bulan untuk menjaga kualitas dan mencegah penyakit.

        Tandanya perlu ganti:
        - Drainase buruk
        - Bau tidak sedap
        - Tanaman tumbuh lambat meski dipupuk
        """)

    with st.expander("Kapan waktu terbaik untuk menyiram tanaman pot?"):
        st.markdown("""
        **Pagi hari** adalah waktu terbaik agar air tidak menguap terlalu cepat dan akar menyerap maksimal.

        Hindari menyiram malam hari karena bisa meningkatkan risiko jamur dan pembusukan akar.
        """)

    with st.expander("Kenapa daun tanaman saya menguning?"):
        st.markdown("""
        **Penyebab umum:**
        - Terlalu banyak/kurang air
        - Kekurangan nutrisi (misal nitrogen)
        - Tanaman stres karena suhu/angin
        - Serangan hama

        Periksa kondisi lingkungan dan media tanam untuk menentukan penyebabnya.
        """)

    with st.expander("Bagaimana cara memilih pot yang tepat?"):
        st.markdown("""
        **Hal yang perlu diperhatikan:**
        - Ukuran: Sesuaikan dengan ukuran akar.
        - Bahan: Plastik (ringan), tanah liat (lebih poros), keramik (estetik).
        - Drainase: Harus ada lubang di bawah pot.

        Hindari pot terlalu besar karena bisa membuat akar mudah membusuk.
        """)

    with st.expander("Apakah tanaman pot bisa ditanam kembali di luar ruangan?"):
        st.markdown("""
        Bisa, namun harus disesuaikan dengan jenis tanaman dan kondisi cuaca.

        **Tips:**
        - Aklimatisasi secara bertahap (kenalkan sinar matahari pelan-pelan)
        - Pastikan tanah luar sesuai kebutuhan tanaman
        - Perhatikan hama/serangga di luar ruangan
        """)


# Fungsi kirim SMS ke nomor tetap
def kirim_whatsapp_terverifikasi(subjek, konten):
    account_sid = 'AC1dec4e4e9496a315c560519f55c9df0a'
    auth_token = '784d236f4d29ff78bb5a096c6bf1cb03'

    client = Client(account_sid, auth_token)

    from_whatsapp_number = 'whatsapp:+14155238886'  # Nomor WhatsApp Twilio
    to_whatsapp_number = 'whatsapp:+62895611336368'  # Nomor tujuan yang sudah diverifikasi

    message = client.messages.create(
        body=f"{subjek}\n\n{konten}",
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )

    return message.sid


# Halaman laporan
def halaman_laporan():
    st.header("📩 Kirim Laporan Tanaman via WhatsApp")
    
    if st.button("🔄 Refresh Status Analisis"):
        st.rerun()

    # Ambil data analisis terakhir
    analisis_terakhir = st.session_state.get('last_analysis', None)
    data_sensor_terakhir = st.session_state.get('last_sensor_data', 'Tidak tersedia')

    if not analisis_terakhir:
        st.warning("🔍 Anda belum melakukan analisis tanaman. Silakan ke tab Analisis terlebih dahulu.")
        return

    st.success("✅ Anda telah melakukan analisis pada: " + analisis_terakhir['timestamp'])

    with st.form("form_laporan_whatsapp"):
        st.text("Nomor tujuan: +62895611336368 (verifikasi Twilio WhatsApp)")

        submitted = st.form_submit_button("Kirim WhatsApp")

        if submitted:
            konten = f"""
Laporan Kondisi Tanaman - {datetime.now().strftime('%d/%m/%Y')}

{analisis_terakhir['analysis']}
            """
    try:
        sid = kirim_whatsapp_terverifikasi("Laporan Tanaman", konten)
        st.success("✅ Laporan berhasil dikirim ke +62895611336368.")
    except Exception as e:
        st.error(f"")
                
# ------------------ 📱 Struktur Utama Aplikasi ------------------ #
def main():
    # Bagian hero
    bagian_hero()
    
    # Navigasi utama
    tab = st.tabs(["🏠 Beranda", "📊 Monitoring", "🔍 Analisis", "❓ FAQ", "📩 Kirim Hasil Analisis"])
    
    with tab[0]:
        halaman_beranda()
    
    with tab[1]:
        halaman_monitoring()
    
    with tab[2]:
        halaman_analisis()
    
    with tab[3]:
        halaman_faq()
    
    with tab[4]:
        halaman_laporan()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align:center;color:#7F8C8D;padding:1rem;">
            <p>PlantVeillance™ | Sistem Monitoring Tanaman Cerdas | © 2025</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()