import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Koz Apartmanı Kasa", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# Bağlantıyı kurmayı dene (Hata ayıklama modu açık)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Sayfa isimlerini tam burada kontrol ediyoruz
    df_gelir = conn.read(worksheet="Gelirler", ttl=0)
    df_gider = conn.read(worksheet="Giderler", ttl=0)
    st.success("Veritabanı bağlantısı başarılı!")
except Exception as e:
    st.error(f"Bağlantı Hatası Detayı: {e}")
    st.info("İpucu: Google E-Tablo'daki sayfa isimlerinin 'Gelirler' ve 'Giderler' olduğundan emin olun.")
    st.stop()

# --- Uygulama Mantığı Buradan Devam Ediyor ---
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
daireler = [f"Daire {i}" for i in range(1, 9)] # 1'den 8'e kadar daireler

tab1, tab2, tab3 = st.tabs(["📊 Özet", "💰 Gelir Ekle", "💸 Gider Ekle"])

with tab1:
    st.subheader("Aylık Durum")
    # Tablo boşsa hata vermemesi için kontrol
    if not df_gelir.empty:
        st.dataframe(df_gelir, use_container_width=True)
    else:
        st.warning("Henüz hiç gelir kaydı yok.")

with tab2:
    with st.form("gelir"):
        tarih = st.date_input("Tarih")
        daire = st.selectbox("Daire", daireler)
        tutar = st.number_input("Tutar", min_value=0)
        if st.form_submit_button("Kaydet"):
            st.info("Kayıt fonksiyonu aktif ediliyor...")
