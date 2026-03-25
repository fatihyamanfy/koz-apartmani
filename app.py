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
ay_no_map = {v: str(i+1).zfill(2) for i, v in enumerate(aylar)}

# --- 2. VERİTABANI BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    try:
        raw_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all", axis=0)
        raw_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all", axis=0)
        
        def temizle(df, cols):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "daire": "Daire", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]

        return temizle(raw_gelir, ["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               temizle(raw_gider, ["Tarih", "Ay", "Tür", "Miktar"])
    except:
        return pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

df_gelir, df_gider = verileri_yukle()

# --- 3. GİRİŞ EKRANI (DARK MODE) ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align: center;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    t_in, t_up = st.tabs(["Giriş", "Kayıt"])
    with t_in:
        u_name = st.text_input("Kullanıcı Adı")
        u_pass = st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir", use_container_width=True):
            if u_name == "fatihyaman" and u_pass == "200915":
                st.session_state.logged_in_user = "admin"
                st.rerun()
            elif u_name != "" and len(u_pass) == 6:
                st.session_state.logged_in_user = "user"
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre!")
    with t_up:
        new_u = st.text_input("Yeni Kullanıcı")
        new_p = st.text_input("6 Haneli Şifre", max_chars=6)
        if st.button("Kaydı Tamamla", use_container_width=True):
            st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
    st.stop()

# --- 4. ANA PANEL VE TASARIM ---
is_admin = (st.session_state.logged_in_user == "admin")
kasa = df_gelir["Miktar"].sum() - df_gider["Miktar"].sum()

st.markdown(f"""
    <div style="background-color: #1A1C23; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; border: 1px solid #30363D;">
        <div style="color: #8B949E; font-size: 13px;">GÜNCEL BAKİYE</div>
        <div style="font-size: 30px; font-weight: bold; color: #58A6FF;">{kasa:,.2f} TL</div>
    </div>
""", unsafe_allow_html=True)

t_yon, t_borc, t_rap = st.tabs(["⚙️ Yönetim", "🔍 Borçlular", "📜 Rapor"])

with t_yon:
    secilen_ay = st.selectbox("Ay Seçin", aylar, index=datetime.now().month-1)
    
    # --- GELİR BÖLÜMÜ ---
    st.subheader(f"📥 {secilen_ay} Gelirleri")
    if is_admin:
        with st.expander("➕ Yeni Gelir Kaydet"):
            daireler = st.multiselect("Daireler", DAIRE_LISTESI)
            g_tur = st.radio("Tür", ["Aidat", "Asansör"] if secilen_ay=="Ocak" else ["Aidat"], horizontal=True)
            g_tutar = st.number_input("Tutar", value=400)
            if st.button("KAYDET"):
                tarih_fix = f"20.{ay_no_map[secilen_ay]}.2026"
                yeni = [{"Tarih": tarih_fix, "Ay": secilen_ay, "Daire": d, "Tür": g_tur, "Miktar": g_tutar} for d in daireler]
                conn.update(worksheet="Gelirler", data=pd.concat([df_gelir, pd.DataFrame(yeni)], ignore_index=True))
                st.rerun()

    # Listeleme ve Silme
    f_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]
    for idx, row in f_gelir.iterrows():
        c_del, c_txt = st.columns([0.15, 0.85])
        if is_admin and c_del.button("🗑️", key=f"g_del_{idx}"):
            conn.update(worksheet="Gelirler", data=df_gelir.drop(idx))
            st.rerun()
        c_txt.info(f"{row['Daire']} | {row['Tür']} | {row['Miktar']} TL")

    st.divider()

    # --- GİDER BÖLÜMÜ ---
    st.subheader(f"📤 {secilen_ay} Giderleri")
    if is_admin:
        with st.expander("➕ Yeni Gider Kaydet"):
            acik = st.text_input("Gider Adı")
            tut = st.number_input("Gider Tutarı", min_value=0)
            if st.button("GİDERİ KAYDET"):
                tarih_fix = f"20.{ay_no_map[secilen_ay]}.2026"
                yeni_g = pd.DataFrame([{"Tarih": tarih_fix, "Ay": secilen_ay, "Tür": acik, "Miktar": tut}])
                conn.update(worksheet="Giderler", data=pd.concat([df_gider, yeni_g], ignore_index=True))
                st.rerun()

    f_gider = df_gider[df_gider["Ay"] == secilen_ay]
    for idx, row in f_gider.iterrows():
        c_del, c_txt = st.columns([0.15, 0.85])
        if is_admin and c_del.button("🗑️", key=f_gid_del_{idx}"):
            conn.update(worksheet="Giderler", data=df_gider.drop(idx))
            st.rerun()
        c_txt.error(f"{row['Tür']} | {row['Miktar']} TL")

with t_borc:
    yapanlar = df_gelir[(df_gelir["Ay"] == secilen_ay) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in yapanlar]
    for b in borclular: st.warning(f"❌ {b}")
    if not borclular: st.success("Herkes ödedi!")

with t_rap:
    st.dataframe(pd.concat([df_gelir.assign(T="GELİR"), df_gider.assign(T="GİDER")], ignore_index=True).sort_index(ascending=False), use_container_width=True, hide_index=True)

if st.button("🚪 Çıkış", use_container_width=True):
    st.session_state.logged_in_user = None
    st.rerun()
