import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

# --- 1. GÖRSELDEKİ VERİLER VE AYARLAR ---
DAIRE_SAYISI = 8
DAIRE_ISIMLERI = [
    "Daire 1 - Mehmet Atasoy",
    "Daire 2 - Fatih Yaman",
    "Daire 3 - Hasan Çetin",
    "Daire 4 - Erkan Kılıç",
    "Daire 5 - Süleyman Karaca",
    "Daire 6 - Mustafa Sönmez",
    "Daire 7 - Hüseyin Aydın",
    "Daire 8 - Ömer Koç"
]

aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# Görselden okunan Ocak, Şubat, Mart Aidat Verileri (Hepsini 400 TL girdim)
varsayilan_gelir = {ay: pd.DataFrame({"Daire": DAIRE_ISIMLERI, "Miktar (TL)": 400.0 if i < 3 else 0.0}) for i, ay in enumerate(aylar)}

# Görselden okunan Gider Verileri
varsayilan_gider = {ay: pd.DataFrame(columns=["Açıklama", "Tutar (TL)"]) for ay in aylar}
varsayilan_gider["Ocak"] = pd.DataFrame([{"Açıklama": "Merdiven Temizlik", "Tutar (TL)": 150.0}, {"Açıklama": "Elektrik", "Tutar (TL)": 85.0}])
varsayilan_gider["Şubat"] = pd.DataFrame([{"Açıklama": "Asansör Bakım", "Tutar (TL)": 200.0}, {"Açıklama": "Merdiven Temizlik", "Tutar (TL)": 150.0}])
varsayilan_gider["Mart"] = pd.DataFrame([{"Açıklama": "Ortak Alan Lamba Değişimi", "Tutar (TL)": 60.0}, {"Açıklama": "Merdiven Temizlik", "Tutar (TL)": 150.0}])

# Session State Başlatma
if "gelir_verisi" not in st.session_state:
    st.session_state.gelir_verisi = varsayilan_gelir
if "gider_verisi" not in st.session_state:
    st.session_state.gider_verisi = varsayilan_gider

# --- 2. GÖRSEL TASARIM (STYLING) ---
st.markdown("""
    <style>
    .sticky-box {
        position: fixed; top: 50px; right: 20px; 
        background-color: #ffffff; padding: 20px; 
        border-radius: 15px; border: 3px solid #1E3A8A; 
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        z-index: 1000; text-align: center; min-width: 150px;
    }
    .main-header {font-size: 28px; font-weight: bold; color: #1E3A8A; margin-bottom: 20px;}
    </style>
""", unsafe_allow_html=True)

# --- 3. ÜST SABİT BAKİYE HESABI ---
toplam_gelir_genel = sum(df["Miktar (TL)"].sum() for df in st.session_state.gelir_verisi.values())
toplam_gider_genel = sum(df["Tutar (TL)"].sum() for df in st.session_state.gider_verisi.values())
net_bakiye = toplam_gelir_genel - toplam_gider_genel

st.markdown(f"""
    <div class="sticky-box">
        <div style="color: #666; font-size: 14px; margin-bottom: 5px;">💰 TOPLAM KASA</div>
        <div style="color: #1E3A8A; font-size: 26px; font-weight: bold;">{net_bakiye:,.2f} TL</div>
    </div>
""", unsafe_allow_html=True)

# --- 4. ANA PANEL ---
st.title("🏢 Koz Apartmanı 2026 Yönetim Paneli")

tabs = st.tabs(aylar)

for i, ay in enumerate(aylar):
    with tabs[i]:
        st.markdown(f"<div class='main-header'>{ay} 2026 Tablosu</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📥 Aidat Tahsilatı")
            edited_gelir = st.data_editor(
                st.session_state.gelir_verisi[ay], 
                key=f"gelir_{ay}",
                use_container_width=True,
                hide_index=True
            )
            st.session_state.gelir_verisi[ay] = edited_gelir
            ay_gelir = edited_gelir["Miktar (TL)"].sum()
            st.info(f"**Aylık Toplam Gelir:** {ay_gelir:,.2f} TL")

        with col2:
            st.subheader("📤 Apartman Giderleri")
            edited_gider = st.data_editor(
                st.session_state.gider_verisi[ay],
                key=f"gider_{ay}",
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True
            )
            st.session_state.gider_verisi[ay] = edited_gider
            ay_gider = edited_gider["Tutar (TL)"].sum()
            st.error(f"**Aylık Toplam Gider:** {ay_gider:,.2f} TL")

        # Aylık Özet Alanı
        st.divider()
        aylik_fark = ay_gelir - ay_gider
        color = "green" if aylik_fark >= 0 else "red"
        st.markdown(f"### {ay} Ayı Bilançosu: <span style='color:{color}'>{aylik_fark:,.2f} TL</span>", unsafe_allow_html=True)

# --- BİLGİ NOTU ---
st.sidebar.markdown(f"""
### Yönetici Bilgileri
**Yönetici:** Fatih Yaman  
**Bina:** Koz Apartmanı  
**Daire Sayısı:** {DAIRE_SAYISI}  

---
*Not: Veriler şimdilik geçicidir. Kalıcı kayıt için 'Verileri Kaydet' butonu eklenecektir.*
""")
