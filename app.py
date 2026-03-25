import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

st.set_page_config(page_title="Koz Apartmanı Kasa", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# --- VERİTABANI BAĞLANTISI ---
try:
    # Bağlantıyı oluştur
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Sayfaları oku
    df_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all")
    df_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all")
    
    st.success("✅ Veritabanı bağlantısı başarıyla sağlandı!")
except Exception as e:
    st.error(f"❌ Bağlantı Hatası: {e}")
    st.warning("İpucu: Eğer 'PEM' hatası alıyorsanız, Secrets kısmındaki private_key başında ve sonunda 3 adet tırnak (\"\"\") olduğundan emin olun.")
    st.stop()

# --- AYARLAR ---
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
daireler = [f"Daire {i}" for i in range(1, 9)]
kategoriler_gelir = ["Aidat", "Asansör", "Diğer"]
kategoriler_gider = ["Temizlik", "Asansör Bakım", "Elektrik", "Tamirat", "Diğer"]
mevcut_ay = aylar[datetime.now().month - 1]

# --- SEKMELİ ARAYÜZ ---
tab1, tab2, tab3 = st.tabs(["📊 Aylık Özet", "📥 Gelir Ekle", "📤 Gider Ekle"])

with tab1:
    st.subheader("Finansal Durum Panosu")
    secilen_ay = st.selectbox("İncelemek istediğiniz ayı seçin:", aylar, index=aylar.index(mevcut_ay))
    
    # Filtreleme
    aylik_gelir = df_gelir[df_gelir['İlgili Ay'] == secilen_ay] if not df_gelir.empty else pd.DataFrame()
    aylik_gider = df_gider[df_gider['İlgili Ay'] == secilen_ay] if not df_gider.empty else pd.DataFrame()
    
    t_gelir = aylik_gelir['Tutar (TL)'].sum() if not aylik_gelir.empty else 0
    t_gider = aylik_gider['Tutar (TL)'].sum() if not aylik_gider.empty else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Gelir", f"{t_gelir} TL")
    c2.metric("Toplam Gider", f"{t_gider} TL")
    c3.metric("Kalan Bakiye", f"{t_gelir - t_gider} TL")
    
    st.divider()
    st.write(f"**{secilen_ay} Ayı Hareketleri**")
    st.dataframe(aylik_gelir, use_container_width=True, hide_index=True)
    st.dataframe(aylik_gider, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Tahsilat Kaydı")
    with st.form("gelir_f", clear_on_submit=True):
        g_tarih = st.date_input("İşlem Tarihi").strftime("%d.%m.%Y")
        g_daire = st.selectbox("Ödeyen Daire", daireler)
        g_ay = st.selectbox("Hangi Ayın Aidatı?", aylar, index=aylar.index(mevcut_ay))
        g_kat = st.selectbox("Ödeme Türü", kategoriler_gelir)
        g_tutar = st.number_input("Tutar (TL)", min_value=0, step=100)
        
        if st.form_submit_button("Geliri Kaydet"):
            yeni = pd.DataFrame([{"Tarih": g_tarih, "Daire No": g_daire, "İlgili Ay": g_ay, "Kategori": g_kat, "Tutar (TL)": g_tutar}])
            guncel = pd.concat([df_gelir, yeni], ignore_index=True)
            conn.update(worksheet="Gelirler", data=guncel)
            st.success("Kayıt E-Tabloya gönderildi! Sayfayı yenileyebilirsiniz.")

with tab3:
    st.subheader("Harcama Kaydı")
    with st.form("gider_f", clear_on_submit=True):
        gd_tarih = st.date_input("Harcama Tarihi").strftime("%d.%m.%Y")
        gd_ay = st.selectbox("Harcama Ayı", aylar, index=aylar.index(mevcut_ay))
        gd_kat = st.selectbox("Harcama Türü", kategoriler_gider)
        gd_acik = st.text_input("Açıklama")
        gd_tutar = st.number_input("Tutar (TL)", min_value=0, step=100)
        
        if st.form_submit_button("Gideri Kaydet"):
            yeni_g = pd.DataFrame([{"Tarih": gd_tarih, "İlgili Ay": gd_ay, "Kategori": gd_kat, "Açıklama": gd_acik, "Tutar (TL)": gd_tutar}])
            guncel_g = pd.concat([df_gider, yeni_g], ignore_index=True)
            conn.update(worksheet="Giderler", data=guncel_g)
            st.success("Gider kaydı E-Tabloya işlendi!")
