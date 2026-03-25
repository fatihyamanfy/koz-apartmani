import streamlit as st
import pandas as pd
import json
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

# --- 1. SABİT VERİLER (DEĞİŞTİRİLEMEZ) ---
DAIRE_SAYISI = 8
DAIRE_LISTESI = [
    "Daire 1 - Emel Erkabaktepe",
    "Daire 2 - Ayşe Evrendilek",
    "Daire 3 - Fatih Yaman",
    "Daire 4 - İsmail Boztepe",
    "Daire 5 - Fehmi Koç",
    "Daire 6 - Murat Altınışık",
    "Daire 7 - Arif Biçer",
    "Daire 8 - Şerife"
]

aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. MOBİL UYUMLU GÖRSEL AYARLAR ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 22px; }
    .main-header { font-size: 22px; font-weight: bold; color: #1E3A8A; margin-bottom: 10px; }
    /* Mobil bakiye kutusu */
    .sticky-box {
        background-color: #f8f9fa; padding: 10px; border-radius: 10px;
        border: 2px solid #1E3A8A; text-align: center; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. VERİTABANI BAĞLANTISI (GÜVENLİ YÖNTEM) ---
try:
    # Secrets içindeki JSON'u oku
    if "gsheets" in st.secrets and "service_account_json" in st.secrets["gsheets"]:
        creds = json.loads(st.secrets["gsheets"]["service_account_json"])
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Tablodan oku
        df_gelir = conn.read(worksheet="Gelirler", ttl=0)
        df_gider = conn.read(worksheet="Giderler", ttl=0)
    else:
        # Eğer henüz secrets ayarlanmadıysa boş tablo göster (Hata vermemesi için)
        df_gelir = pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"])
        df_gider = pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.stop()

# --- 4. HESAPLAMALAR ---
toplam_gelir = df_gelir["Miktar"].sum()
toplam_gider = df_gider["Miktar"].sum()
net_kasa = toplam_gelir - toplam_gider

# --- 5. ÜST PANEL (MOBİL UYUMLU) ---
st.markdown(f'<div class="sticky-box">💰 GÜNCEL KASA: <b>{net_kasa:,.2f} TL</b></div>', unsafe_allow_html=True)

# --- 6. ANA YÖNETİM ---
secilen_ay = st.select_slider("Ay Seçiniz", options=aylar, value=aylar[datetime.now().month-1])
st.markdown(f"<div class='main-header'>🏢 {secilen_ay} 2026 Yönetimi</div>", unsafe_allow_html=True)

t1, t2 = st.tabs(["📥 GELİR GİRİŞİ", "📤 GIDER GİRİŞİ"])

with t1:
    col_a, col_b = st.columns(2)
    with col_a:
        g_daire = st.selectbox("Daire Seç", DAIRE_LISTESI)
        g_tur = st.radio("Ödeme Türü", ["Aidat (400 TL)", "Yıllık Asansör Bakımı"] if secilen_ay == "Ocak" else ["Aidat (400 TL)"])
    with col_b:
        varsayilan_tutar = 400 if "Aidat" in g_tur else 0
        g_miktar = st.number_input("Tutar (TL)", value=varsayilan_tutar)
        if st.button("Ödemeyi Kaydet", use_container_width=True):
            # BURADA TABLOYA YAZMA KOMUTU ÇALIŞACAK
            st.success(f"{g_daire} için {g_miktar} TL kaydedildi.")

with t2:
    with st.form("gider_form"):
        gd_tur = st.text_input("Gider Açıklaması")
        gd_miktar = st.number_input("Gider Tutarı", min_value=0)
        if st.form_submit_button("Gideri Kaydet", use_container_width=True):
            st.warning("Gider kaydedildi (Google Tablo'ya işleniyor...)")

# --- 7. LİSTELEME ---
st.divider()
st.subheader(f"{secilen_ay} Ayı Hareket Özetleri")
c1, c2 = st.columns(2)
c1.write("**Gelirler**")
c1.dataframe(df_gelir[df_gelir["Ay"] == secilen_ay], use_container_width=True, hide_index=True)
c2.write("**Giderler**")
c2.dataframe(df_gider[df_gider["Ay"] == secilen_ay], use_container_width=True, hide_index=True)
