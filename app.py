import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

DAIRE_LISTESI = [
    "EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4",
    "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"
]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. VERİTABANI BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def verileri_yukle():
    try:
        raw_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all", axis=0)
        raw_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all", axis=0)
        
        def temizle_gelir(df):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "daire": "Daire", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            for col in ["Tarih", "Ay", "Daire", "Tür", "Miktar"]:
                if col not in df.columns: df[col] = ""
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            return df[["Tarih", "Ay", "Daire", "Tür", "Miktar"]]

        def temizle_gider(df):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            for col in ["Tarih", "Ay", "Tür", "Miktar"]:
                if col not in df.columns: df[col] = ""
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            return df[["Tarih", "Ay", "Tür", "Miktar"]]

        return temizle_gelir(raw_gelir), temizle_gider(raw_gider)
    except Exception:
        return pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

df_gelir, df_gider = verileri_yukle()

# --- 3. GİRİŞ SİSTEMİ ---
if st.session_state.logged_in_user is None:
    st.title("🔐 Koz Apartmanı Giriş")
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
    .row-style { background-color: #ffffff; color: #000000 !important; padding: 10px; border-radius: 8px; margin-bottom: 5px; border-left: 6px solid #1E3A8A; font-weight: bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);}
    .borclu-style { background-color: #ffebee; color: #c62828; padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #c62828; font-size: 14px;}
    </style>
""", unsafe_allow_html=True)

# --- 5. ÜST PANEL ---
st.write(f"Hoş geldin, **{st.session_state.logged_in_user}**")
if st.button("Çıkış Yap"):
    st.session_state.logged_in_user = None
    st.rerun()

# Yıllık Durum
cols = st.columns(12)
for idx, ay_adi in enumerate(aylar):
    gelir_toplam = df_gelir[df_gelir["Ay"] == ay_adi]["Miktar"].sum()
    renk = "bg-green" if gelir_toplam >= 3200 else "bg-red"
    cols[idx].markdown(f'<div class="month-card {renk}">{ay_adi}</div>', unsafe_allow_html=True)

t_gelir = df_gelir["Miktar"].sum()
t_gider = df_gider["Miktar"].sum()
st.markdown(f'<div class="bakiye-container"><h3>GÜNCEL KASA: {t_gelir - t_gider:,.2f} TL</h3></div>', unsafe_allow_html=True)

# --- 6. SEKMELER ---
t_aylik, t_borclular, t_rapor = st.tabs(["⚙️ Aylık Yönetim", "🔍 Ödemeyenler", "📜 Genel Rapor"])

with t_aylik:
    secilen_ay = st.selectbox("İşlem Yapılacak Ayı Seçin", aylar, index=datetime.now().month-1)
    
    # --- GELİR EKLEME ---
    st.subheader(f"📥 {secilen_ay} Ayı Gelir Girişi")
    if is_admin:
        with st.expander(f"➕ {secilen_ay} Ayı Yeni Gelir Ekle", expanded=True):
            secilen_daireler = st.multiselect("Ödeme Yapan Daireleri Seçin", DAIRE_LISTESI)
            c1, c2 = st.columns(2)
            g_tur_coklu = c1.radio("Ödeme Türü", ["Aidat", "Asansör Bakımı"] if secilen_ay=="Ocak" else ["Aidat"], key="coklu_tur")
            g_miktar_coklu = c2.number_input("Tutar (TL)", value=400 if g_tur_coklu == "Aidat" else 1800)
            
            if st.button(f"Seçili Kayıtları {secilen_ay} Ayına İşle", use_container_width=True):
                if secilen_daireler:
                    yeni_kayitlar = [{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": d, "Tür": g_tur_coklu, "Miktar": g_miktar_coklu} for d in secilen_daireler]
                    conn.update(worksheet="Gelirler", data=pd.concat([df_gelir, pd.DataFrame(yeni_kayitlar)], ignore_index=True))
                    st.success("İşlem başarılı!"); time.sleep(1); st.rerun()

    # Gelir Listesi
    f_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]
    for idx, row in f_gelir.iterrows():
        c_del, c_txt = st.columns([0.1, 0.9])
        if is_admin and c_del.button("🗑️", key=f"g_{idx}"):
            conn.update(worksheet="Gelirler", data=df_gelir.drop(idx))
            st.rerun()
        c_txt.markdown(f"<div class='row-style'>{row['Daire']} | {row['Tür']} | {row['Miktar']} TL</div>", unsafe_allow_html=True)

    st.divider()

    # --- GİDERLER ---
    st.subheader(f"📤 {secilen_ay} Ayı Gider Girişi")
    if is_admin:
        with st.expander(f"➕ {secilen_ay} Ayı Yeni Gider Ekle"):
            gd_acik = st.text_input("Gider Açıklaması")
            gd_miktar = st.number_input("Gider Tutarı", min_value=0)
            if st.button("Gideri Kaydet"):
                yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": gd_acik, "Miktar": gd_miktar}])
                conn.update(worksheet="Giderler", data=pd.concat([df_gider, yeni_g], ignore_index=True))
                st.rerun()
    
    f_gider = df_gider[df_gider["Ay"] == secilen_ay]
    for idx, row in f_gider.iterrows():
        c_del, c_txt = st.columns([0.1, 0.9])
        if is_admin and c_del.button("🗑️", key=f"gid_{idx}"):
            conn.update(worksheet="Giderler", data=df_gider.drop(idx))
            st.rerun()
        c_txt.markdown(f"<div class='row-style'>{row['Tür']} | {row['Miktar']} TL</div>", unsafe_allow_html=True)

with t_borclular:
    st.subheader(f"🚩 {secilen_ay} Ayı Aidat Borçluları")
    odeme_yapanlar = df_gelir[(df_gelir["Ay"] == secilen_ay) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in odeme_yapanlar]
    if not borclular: st.success("Harika! Bu ay tüm daireler aidatını ödedi.")
    else:
        for b in borclular: st.markdown(f"<div class='borclu-style'>❌ {b}</div>", unsafe_allow_html=True)

with t_rapor:
    st.subheader("🗓️ 2026 Genel Raporu")
    rapor = pd.concat([df_gelir.assign(Tip="GELİR"), df_gider.assign(Tip="GİDER")], ignore_index=True).sort_index(ascending=False)
    st.dataframe(rapor[["Tarih", "Ay", "Tip", "Tür", "Daire", "Miktar"]].fillna("-"), use_container_width=True, hide_index=True)
