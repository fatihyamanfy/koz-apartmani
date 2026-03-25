import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

# --- 1. YETKİLENDİRME VE AYARLAR ---
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

DAIRE_LISTESI = [
    "EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4",
    "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"
]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. VERİTABANI BAĞLANTISI (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_cek():
    df_gelir = conn.read(worksheet="Gelirler", ttl=0)
    df_gider = conn.read(worksheet="Giderler", ttl=0)
    return df_gelir, df_gider

try:
    df_gelir, df_gider = verileri_cek()
except:
    df_gelir = pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"])
    df_gider = pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

# --- 3. GİRİŞ SİSTEMİ ---
if st.session_state.logged_in_user is None:
    st.title("🔐 Koz Apartmanı Giriş")
    u_name = st.text_input("Kullanıcı Adı")
    u_pass = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
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
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. ÜST PANEL VE BAKİYE ---
t_gelir = df_gelir["Miktar"].sum()
t_gider = df_gider["Miktar"].sum()
st.markdown(f'<div class="bakiye-container"><h2>KASA: {t_gelir - t_gider:,.2f} TL</h2></div>', unsafe_allow_html=True)

if st.button("Çıkış Yap"):
    st.session_state.logged_in_user = None
    st.rerun()

# --- 6. ANA SEKMELER ---
tab_yönetim, tab_rapor = st.tabs(["⚙️ Aylık Yönetim", "📜 Genel Hareket Raporu"])

with tab_yönetim:
    secilen_ay = st.selectbox("Ay Seçin", aylar, index=datetime.now().month-1)
    
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader(f"📥 {secilen_ay} Gelirleri")
        if is_admin:
            with st.expander("Yeni Gelir Ekle"):
                g_daire = st.selectbox("Daire", DAIRE_LISTESI)
                g_tur = st.selectbox("Tür", ["Aidat", "Yıllık Asansör Bakımı"] if secilen_ay=="Ocak" else ["Aidat"])
                g_miktar = st.number_input("Tutar", value=400)
                if st.button("Geliri Kaydet"):
                    yeni_row = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": g_daire, "Tür": g_tur, "Miktar": g_miktar}])
                    updated_df = pd.concat([df_gelir, yeni_row], ignore_index=True)
                    conn.update(worksheet="Gelirler", data=updated_df)
                    st.success("Kaydedildi!"); st.rerun()
        
        aylik_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]
        st.dataframe(aylik_gelir, use_container_width=True, hide_index=True)
        
        if is_admin and not aylik_gelir.empty:
            sil_id = st.selectbox("Silinecek Gelir Satırı (Index)", aylik_gelir.index)
            if st.button("Seçili Geliri Sil"):
                df_gelir = df_gelir.drop(sil_id)
                conn.update(worksheet="Gelirler", data=df_gelir)
                st.rerun()

    with c2:
        st.subheader(f"📤 {secilen_ay} Giderleri")
        if is_admin:
            with st.expander("Yeni Gider Ekle"):
                gd_tur = st.text_input("Açıklama")
                gd_miktar = st.number_input("Gider Tutarı", min_value=0)
                if st.button("Gideri Kaydet"):
                    yeni_row = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": gd_tur, "Miktar": gd_miktar}])
                    updated_df = pd.concat([df_gider, yeni_row], ignore_index=True)
                    conn.update(worksheet="Giderler", data=updated_df)
                    st.success("Gider Kaydedildi!"); st.rerun()

        aylik_gider = df_gider[df_gider["Ay"] == secilen_ay]
        st.dataframe(aylik_gider, use_container_width=True, hide_index=True)

        if is_admin and not aylik_gider.empty:
            sil_id_g = st.selectbox("Silinecek Gider Satırı (Index)", aylik_gider.index)
            if st.button("Seçili Gideri Sil"):
                df_gider = df_gider.drop(sil_id_g)
                conn.update(worksheet="Giderler", data=df_gider)
                st.rerun()

with tab_rapor:
    st.subheader("🗓️ 2026 Yılı Tüm Hareketler (Kronolojik)")
    
    # Gelir ve Giderleri birleştirme
    report_gelir = df_gelir.copy()
    report_gelir["Tür"] = "GELİR: " + report_gelir["Tür"] + " (" + report_gelir["Daire"] + ")"
    
    report_gider = df_gider.copy()
    report_gider["Tür"] = "GİDER: " + report_gider["Tür"]
    report_gider["Miktar"] = -report_gider["Miktar"] # Giderleri eksi göster
    
    full_report = pd.concat([report_gelir[["Tarih", "Ay", "Tür", "Miktar"]], 
                             report_gider[["Tarih", "Ay", "Tür", "Miktar"]]])
    
    st.dataframe(full_report.sort_index(ascending=False), use_container_width=True, hide_index=True)
