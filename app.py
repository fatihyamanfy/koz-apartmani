import streamlit as st
import pandas as pd
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

# --- 1. DAİRE LİSTESİ (SABİT VE DÜZENLENEMEZ) ---
DAIRE_LISTESI = [
    "Daire 1 - Emel Erkabaktepe",
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

# --- 2. MOBİL TASARIM (CSS) ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1E3A8A; color: white; }
    .bakiye-kutu {
        background-color: #1E3A8A; color: white; padding: 20px; border-radius: 15px;
        text-align: center; margin-bottom: 20px; box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    .ay-baslik { font-size: 24px; font-weight: bold; color: #1E3A8A; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 3. VERİ SAKLAMA (SESSION STATE) ---
# Uygulama açık kaldığı sürece verileri burada tutar
if "kasa_gelir" not in st.session_state:
    st.session_state.kasa_gelir = pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"])
if "kasa_gider" not in st.session_state:
    st.session_state.kasa_gider = pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

# --- 4. ÜST BAKİYE PANELİ ---
t_gelir = st.session_state.kasa_gelir["Miktar"].sum()
t_gider = st.session_state.kasa_gider["Miktar"].sum()
net_kasa = t_gelir - t_gider

st.markdown(f"""
    <div class="bakiye-kutu">
        <div style="font-size: 16px; opacity: 0.8;">TOPLAM KASA BAKİYESİ</div>
        <div style="font-size: 32px; font-weight: bold;">{net_kasa:,.2f} TL</div>
    </div>
""", unsafe_allow_html=True)

# --- 5. AY SEÇİMİ (MOBİL SLIDER) ---
simdiki_ay_index = datetime.now().month - 1
secilen_ay = st.select_slider("📅 İşlem Yapılacak Ayı Kaydırın", options=aylar, value=aylar[simdiki_ay_index])

st.markdown(f"<div class='ay-baslik'>{secilen_ay} 2026 Yönetimi</div>", unsafe_allow_html=True)

# --- 6. GELİR VE GİDER GİRİŞ ALANLARI ---
col1, col2 = st.columns(2)

with col1:
    with st.expander("📥 GELİR EKLE (Aidat/Ek)", expanded=True):
        g_daire = st.selectbox("Daire", DAIRE_LISTESI, key="d_sec")
        
        # Ocak ayı için özel seçenek
        gelir_turleri = ["Aidat", "Yıllık Asansör Bakımı"] if secilen_ay == "Ocak" else ["Aidat"]
        g_tur = st.radio("Ödeme Türü", gelir_turleri, horizontal=True)
        
        g_miktar = st.number_input("Tutar (TL)", min_value=0, value=400 if g_tur == "Aidat" else 0)
        
        if st.button("Geliri İşle"):
            yeni_gelir = pd.DataFrame([{
                "Tarih": datetime.now().strftime("%d.%m.%Y"),
                "Ay": secilen_ay,
                "Daire": g_daire,
                "Tür": g_tur,
                "Miktar": g_miktar
            }])
            st.session_state.kasa_gelir = pd.concat([st.session_state.kasa_gelir, yeni_gelir], ignore_index=True)
            st.success("Gelir eklendi!")
            st.rerun()

with col2:
    with st.expander("📤 GİDER EKLE", expanded=True):
        gd_tur = st.text_input("Gider Açıklaması", placeholder="Örn: Temizlik malzemesi")
        gd_miktar = st.number_input("Gider Tutarı (TL)", min_value=0, key="gd_tutar")
        
        if st.button("Gideri İşle"):
            yeni_gider = pd.DataFrame([{
                "Tarih": datetime.now().strftime("%d.%m.%Y"),
                "Ay": secilen_ay,
                "Tür": gd_tur,
                "Miktar": gd_miktar
            }])
            st.session_state.kasa_gider = pd.concat([st.session_state.kasa_gider, yeni_gider], ignore_index=True)
            st.error("Gider eklendi!")
            st.rerun()

# --- 7. ÖZET LİSTELER ---
st.divider()
st.subheader(f"📊 {secilen_ay} Ayı Hareketleri")

c1, c2 = st.columns(2)
with c1:
    st.write("**Gelen Ödemeler**")
    aylik_g = st.session_state.kasa_gelir[st.session_state.kasa_gelir["Ay"] == secilen_ay]
    st.dataframe(aylik_g[["Daire", "Tür", "Miktar"]], use_container_width=True, hide_index=True)

with c2:
    st.write("**Yapılan Harcamalar**")
    aylik_h = st.session_state.kasa_gider[st.session_state.kasa_gider["Ay"] == secilen_ay]
    st.dataframe(aylik_h[["Tür", "Miktar"]], use_container_width=True, hide_index=True)
