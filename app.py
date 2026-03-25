import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Koz Apartmanı Yönetim", layout="wide")

# --- AYARLAR ---
AIDAT_MIKTARI = 400
DAIRE_SAYISI = 10 # Apartmanınızdaki daire sayısına göre güncelleyin

st.title("🏢 Koz Apartmanı Dijital Karar Defteri")

# --- SIDEBAR (Gider Girişi) ---
st.sidebar.header("💸 Gider Yönetimi")
gider_aciklama = st.sidebar.text_input("Gider Açıklaması", placeholder="Örn: Asansör Bakımı")
gider_tutari = st.sidebar.number_input("Gider Tutarı (TL)", min_value=0, step=10)

if st.sidebar.button("Gideri Sisteme İşle"):
    st.sidebar.success(f"{gider_aciklama} için {gider_tutari} TL kaydedildi! (E-Tabloya manuel eklemeyi unutmayın)")

# --- ANA PANEL ---
tab1, tab2 = st.tabs(["💰 Aidat Takibi (Gelir)", "📊 Kasa Özeti"])

with tab1:
    st.subheader(f"{datetime.now().strftime('%B %Y')} Ayı Tahsilat Listesi")
    st.info("Daire ödemesini yapınca yanındaki kutucuğu işaretleyin. Sistem otomatik 400 TL hesaplar.")
    
    # Daire listesi oluşturma
    veriler = []
    for i in range(1, DAIRE_SAYISI + 1):
        veriler.append({"Daire No": f"Daire {i}", "Ödeme Durumu": False})
    
    # İnteraktif Tablo
    df_aidat = pd.DataFrame(veriler)
    edited_df = st.data_editor(df_aidat, use_container_width=True, hide_index=True)
    
    # Hesaplamalar
    odenen_daire_sayisi = edited_df["Ödeme Durumu"].sum()
    toplam_gelir = odenen_daire_sayisi * AIDAT_MIKTARI

with tab2:
    st.subheader("Genel Kasa Durumu")
    
    # Örnek statik gider (Şimdilik manuel girilen değeri buraya çekiyoruz)
    toplam_gider = gider_tutari # Sidebar'dan gelen değer
    kalan_bakiye = toplam_gelir - toplam_gider
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Tahsilat", f"{toplam_gelir} TL", f"{odenen_daire_sayisi} Daire")
    c2.metric("Toplam Gider", f"{toplam_gider} TL", delta_color="inverse")
    c3.metric("Kasadaki Net Bakiye", f"{kalan_bakiye} TL")

    st.divider()
    if kalan_bakiye < 0:
        st.error("⚠️ Dikkat! Kasa eksi bakiyede.")
    else:
        st.success("✅ Kasa durumu sağlıklı.")

st.caption("Not: Bu paneldeki değişikliklerin kalıcı olması için verileri ay sonunda Google Tablo'ya aktarmanız önerilir.")
