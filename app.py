import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

DAIRE_LISTESI = [
    "EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4",
    "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"
]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. VERİTABANI BAĞLANTISI VE TEMİZLİK ---
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    try:
        df_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all", axis=0)
        df_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all", axis=0)
        
        # "None" ve "Unnamed" sütunlarını tamamen kaldır
        df_gelir = df_gelir.loc[:, ~df_gelir.columns.str.contains('^Unnamed|^None|none', case=False, na=False)]
        df_gider = df_gider.loc[:, ~df_gider.columns.str.contains('^Unnamed|^None|none', case=False, na=False)]
        
        # Sütun isimlerini standartlaştır
        df_gelir.columns = [c.strip().capitalize() for c in df_gelir.columns]
        df_gider.columns = [c.strip().capitalize() for c in df_gider.columns]
        
        return df_gelir, df_gider
    except:
        return pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

df_gelir, df_gider = verileri_yukle()

# --- 3. GİRİŞ KONTROLÜ ---
if st.session_state.logged_in_user is None:
    st.title("🔐 Koz Apartmanı Yönetim Sistemi")
    u_name = st.text_input("Kullanıcı Adı")
    u_pass = st.text_input("Şifre", type="password")
    if st.button("Sisteme Gir"):
        if u_name == "fatihyaman" and u_pass == "200915":
            st.session_state.logged_in_user = "admin"
            st.rerun()
        elif u_name != "" and len(u_pass) == 6:
            st.session_state.logged_in_user = "user"
            st.rerun()
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .bakiye-container { background-color: #1E3A8A; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .month-card { padding: 8px; border-radius: 5px; text-align: center; color: white; font-weight: bold; font-size: 11px; margin-bottom: 5px;}
    .bg-green { background-color: #28a745; }
    .bg-red { background-color: #dc3545; opacity: 0.7; }
    </style>
""", unsafe_allow_html=True)

# --- 5. ÜST PANEL ---
st.write(f"Hoş geldin, **{st.session_state.logged_in_user}**")
if st.button("Çıkış Yap"):
    st.session_state.logged_in_user = None
    st.rerun()

# Yıllık Durum Panosu
cols = st.columns(12)
for idx, ay_adi in enumerate(aylar):
    if "Ay" in df_gelir.columns and "Miktar" in df_gelir.columns:
        gelir_toplam = df_gelir[df_gelir["Ay"] == ay_adi]["Miktar"].sum()
        renk = "bg-green" if gelir_toplam >= 3200 else "bg-red"
    else:
        renk = "bg-red"
    cols[idx].markdown(f'<div class="month-card {renk}">{ay_adi}</div>', unsafe_allow_html=True)

# Bakiye Hesaplama
t_gelir = pd.to_numeric(df_gelir["Miktar"], errors='coerce').sum() if "Miktar" in df_gelir.columns else 0
t_gider = pd.to_numeric(df_gider["Miktar"], errors='coerce').sum() if "Miktar" in df_gider.columns else 0
st.markdown(f'<div class="bakiye-container"><h3>GÜNCEL KASA: {t_gelir - t_gider:,.2f} TL</h3></div>', unsafe_allow_html=True)

# --- 6. SEKMELER ---
t_aylik, t_rapor = st.tabs(["⚙️ Aylık Yönetim", "📜 Genel Rapor"])

with t_aylik:
    secilen_ay = st.selectbox("Ay Seçin", aylar, index=datetime.now().month-1)
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📥 Gelirler")
        if is_admin:
            with st.expander("➕ Yeni Gelir Ekle"):
                g_daire = st.selectbox("Daire", DAIRE_LISTESI)
                g_tur = st.radio("Tür", ["Aidat", "Asansör Bakımı"] if secilen_ay=="Ocak" else ["Aidat"], horizontal=True)
                g_miktar = st.number_input("Miktar", value=400)
                if st.button("Kaydet"):
                    yeni = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": g_daire, "Tür": g_tur, "Miktar": g_miktar}])
                    # Sadece ana sütunları göndererek tabloyu temizle
                    temiz_gelir = pd.concat([df_gelir, yeni], ignore_index=True)[["Tarih", "Ay", "Daire", "Tür", "Miktar"]]
                    conn.update(worksheet="Gelirler", data=temiz_gelir)
                    st.rerun()
        
        if "Ay" in df_gelir.columns:
            st.dataframe(df_gelir[df_gelir["Ay"] == secilen_ay], use_container_width=True, hide_index=True)

    with c2:
        st.subheader("📤 Giderler")
        if is_admin:
            with st.expander("➕ Yeni Gider Ekle"):
                gd_acik = st.text_input("Açıklama")
                gd_miktar = st.number_input("Tutar", min_value=0)
                if st.button("Gider Kaydet"):
                    yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": gd_acik, "Miktar": gd_miktar}])
                    # Sadece ana sütunları göndererek tabloyu temizle
                    temiz_gider = pd.concat([df_gider, yeni_g], ignore_index=True)[["Tarih", "Ay", "Tür", "Miktar"]]
                    conn.update(worksheet="Giderler", data=temiz_gider)
                    st.rerun()
        
        if "Ay" in df_gider.columns:
            st.dataframe(df_gider[df_gider["Ay"] == secilen_ay], use_container_width=True, hide_index=True)

with t_rapor:
    st.subheader("🗓️ 2026 Genel Raporu")
    if not df_gelir.empty or not df_gider.empty:
        r_gelir = df_gelir.copy()
        r_gelir["Tip"] = "GELİR"
        r_gider = df_gider.copy()
        r_gider["Tip"] = "GİDER"
        rapor = pd.concat([r_gelir, r_gider], ignore_index=True).sort_index(ascending=False)
        st.dataframe(rapor[["Tarih", "Ay", "Tip", "Tür", "Miktar"]], use_container_width=True, hide_index=True)
