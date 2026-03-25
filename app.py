import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

# --- 1. AYARLAR VE VERİ YAPISI ---
st.markdown("""
    <style>
    .main-header {font-size: 25px; font-weight: bold; color: #1E3A8A;}
    .sticky-box {
        position: fixed; top: 50px; right: 20px; 
        background-color: #f0f2f6; padding: 15px; 
        border-radius: 10px; border: 2px solid #1E3A8A; 
        z-index: 100; text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# Sayfayı yenilese bile verilerin (o anlık) gitmemesi için session_state kullanıyoruz
if "gelir_verisi" not in st.session_state:
    # Her ay için 10 dairelik boş matris
    st.session_state.gelir_verisi = {ay: pd.DataFrame({"Daire No": [f"Daire {i}" for i in range(1, 11)], "Miktar (TL)": 0.0}) for ay in aylar}
if "gider_verisi" not in st.session_state:
    st.session_state.gider_verisi = {ay: pd.DataFrame(columns=["Açıklama", "Tutar (TL)"]) for ay in aylar}

# --- 2. SAĞ ÜST SABİT BAKİYE EKRANI ---
toplam_gelir_genel = sum(df["Miktar (TL)"].sum() for df in st.session_state.gelir_verisi.values())
toplam_gider_genel = sum(df["Tutar (TL)"].sum() for df in st.session_state.gider_verisi.values())
net_bakiye = toplam_gelir_genel - toplam_gider_genel

st.markdown(f"""
    <div class="sticky-box">
        <span style="color: #555; font-size: 14px;">📊 GÜNCEL KASA</span><br>
        <span style="color: #1E3A8A; font-size: 24px; font-weight: bold;">{net_bakiye:,.2f} TL</span>
    </div>
""", unsafe_allow_html=True)

# --- 3. ANA PANEL ---
st.title("🏢 Koz Apartmanı 2026 Yönetim Paneli")

# Ayları sekmeler halinde dizelim
tabs = st.tabs(aylar)

for i, ay in enumerate(aylar):
    with tabs[i]:
        st.markdown(f"<div class='main-header'>{ay} 2026 Hareketleri</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("💰 Gelirler (Aidat)")
            # Düzenlenebilir Gelir Tablosu
            edited_gelir = st.data_editor(
                st.session_state.gelir_verisi[ay], 
                key=f"gelir_edit_{ay}",
                use_container_width=True,
                hide_index=True
            )
            st.session_state.gelir_verisi[ay] = edited_gelir
            aylik_gelir_toplam = edited_gelir["Miktar (TL)"].sum()
            st.info(f"**{ay} Toplam Gelir:** {aylik_gelir_toplam:,.2f} TL")

        with col2:
            st.subheader("💸 Giderler")
            # Düzenlenebilir Gider Tablosu (Yeni satır eklenebilir)
            edited_gider = st.data_editor(
                st.session_state.gider_verisi[ay],
                key=f"gider_edit_{ay}",
                num_rows="dynamic", # Buradan artı butonuna basıp yeni gider girebilirsin
                use_container_width=True,
                hide_index=True
            )
            st.session_state.gider_verisi[ay] = edited_gider
            aylik_gider_toplam = edited_gider["Tutar (TL)"].sum()
            st.error(f"**{ay} Toplam Gider:** {aylik_gider_toplam:,.2f} TL")

        st.divider()
        st.write(f"ℹ️ {ay} ayı sonu bakiye durumu: **{aylik_gelir_toplam - aylik_gider_toplam:,.2f} TL**")

# --- 4. VERİ SAKLAMA UYARISI ---
st.sidebar.warning("""
**Dikkat:** Bu veriler şu an sadece tarayıcıda tutuluyor. Sayfayı kapatıp açtığınızda sıfırlanabilir. 
Kalıcı hale getirmek (Google Tablo'ya yazmak) için daha sonra bağlantı kuracağız.
""")
