import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Koz Apartmanı Kasa", layout="centered")
st.title("Koz Apartmanı Yönetim")

# Google Sheets Bağlantısını Kur
conn = st.connection("gsheets", type=GSheetsConnection)

# Verileri Çek (ttl=0 anında güncellenmesini sağlar)
try:
    df_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all")
    df_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all")
except:
    st.error("Tablo bağlantısı kurulamadı. Ayarları kontrol edin.")
    st.stop()

aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
daireler = ["1-Emel", "2-Ayşe", "3-Fatih", "4-İsmail", "5-Fehmi", "6-Murat", "7-Arif", "8-Şerife"]
kategoriler_gelir = ["Aidat", "Asansör", "Diğer"]
kategoriler_gider = ["Temizlik", "Asansör Bakım", "Elektrik", "Tamirat", "Diğer"]

mevcut_ay = aylar[datetime.now().month - 1]

tab1, tab2, tab3 = st.tabs(["Aylık Özet", "Gelir Ekle", "Gider Ekle"])

# --- SEKME 1: AYLIK ÖZET ---
with tab1:
    st.subheader("Aylık Finansal Durum")
    secilen_ay = st.selectbox("İncelemek istediğiniz ayı seçin:", aylar, index=aylar.index(mevcut_ay))
    
    # Pandas ile veriyi ilgili aya göre filtrele
    aylik_gelir = df_gelir[df_gelir['İlgili Ay'] == secilen_ay] if 'İlgili Ay' in df_gelir.columns else pd.DataFrame()
    aylik_gider = df_gider[df_gider['İlgili Ay'] == secilen_ay] if 'İlgili Ay' in df_gider.columns else pd.DataFrame()
    
    toplam_gelir = aylik_gelir['Tutar (TL)'].sum() if not aylik_gelir.empty else 0.0
    toplam_gider = aylik_gider['Tutar (TL)'].sum() if not aylik_gider.empty else 0.0
    kalan_bakiye = toplam_gelir - toplam_gider
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Toplam Gelir", f"{toplam_gelir} TL")
    col2.metric("Toplam Gider", f"{toplam_gider} TL")
    col3.metric("Aylık Bakiye", f"{kalan_bakiye} TL", delta=f"{kalan_bakiye} TL" if kalan_bakiye != 0 else None)
    
    st.divider()
    st.write(f"**{secilen_ay} Ayı Gelir Listesi**")
    st.dataframe(aylik_gelir, hide_index=True, use_container_width=True)
    
    st.write(f"**{secilen_ay} Ayı Gider Listesi**")
    st.dataframe(aylik_gider, hide_index=True, use_container_width=True)

# --- SEKME 2: GELİR EKLE ---
with tab2:
    st.subheader("Yeni Gelir (Tahsilat) Ekle")
    with st.form("gelir_formu", clear_on_submit=True):
        g_tarih = st.date_input("Tarih").strftime("%d.%m.%Y")
        g_daire = st.selectbox("Daire", daireler)
        g_ay = st.selectbox("İlgili Ay", aylar, index=aylar.index(mevcut_ay))
        g_kat = st.selectbox("Kategori", kategoriler_gelir)
        g_tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
        
        if st.form_submit_button("Geliri Kaydet"):
            yeni_kayit = pd.DataFrame([{"Tarih": g_tarih, "Daire No": g_daire, "İlgili Ay": g_ay, "Kategori": g_kat, "Tutar (TL)": g_tutar}])
            guncel_df = pd.concat([df_gelir, yeni_kayit], ignore_index=True)
            conn.update(worksheet="Gelirler", data=guncel_df)
            st.success(f"{g_daire} dairesinden {g_tutar} TL tahsilat E-Tabloya eklendi!")

# --- SEKME 3: GİDER EKLE ---
with tab3:
    st.subheader("Yeni Gider (Harcama) Ekle")
    with st.form("gider_formu", clear_on_submit=True):
        gd_tarih = st.date_input("Harcama Tarihi").strftime("%d.%m.%Y")
        gd_ay = st.selectbox("İlgili Ay", aylar, index=aylar.index(mevcut_ay))
        gd_kat = st.selectbox("Kategori", kategoriler_gider)
        gd_aciklama = st.text_input("Açıklama (Örn: Ocak temizlik)")
        gd_tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
        
        if st.form_submit_button("Gideri Kaydet"):
            yeni_gider = pd.DataFrame([{"Tarih": gd_tarih, "İlgili Ay": gd_ay, "Kategori": gd_kat, "Açıklama": gd_aciklama, "Tutar (TL)": gd_tutar}])
            guncel_gider_df = pd.concat([df_gider, yeni_gider], ignore_index=True)
            conn.update(worksheet="Giderler", data=guncel_gider_df)
            st.success(f"{gd_tutar} TL harcama E-Tabloya eklendi!")
