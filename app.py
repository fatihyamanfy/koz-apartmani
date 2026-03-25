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

# --- 3. GİRİŞ KONTROLÜ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align: center; color: white;'>🏢 Koz Apartmanı Yönetim</h2>", unsafe_allow_html=True)
    u_name = st.text_input("Kullanıcı Adı")
    u_pass = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap", use_container_width=True):
        if u_name == "fatihyaman" and u_pass == "200915":
            st.session_state.logged_in_user = "admin"
            st.rerun()
        elif u_name != "" and len(u_pass) == 6:
            st.session_state.logged_in_user = "user"
            st.rerun()
        else: st.error("Hatalı giriş!")
    st.stop()

# Verileri çek
df_gelir, df_gider = verileri_yukle()
is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. TASARIM ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    .bakiye-kutu { background: #1A1C23; border: 1px solid #30363D; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

kasa = df_gelir["Miktar"].sum() - df_gider["Miktar"].sum()
st.markdown(f'<div class="bakiye-kutu"><div style="color:#8B949E; font-size:12px;">GÜNCEL BAKİYE</div><div style="font-size:30px; font-weight:bold; color:#58A6FF;">{kasa:,.2f} TL</div></div>', unsafe_allow_html=True)

# --- 5. ANA İŞLEMLER ---
t_yon, t_borc, t_rap = st.tabs(["⚙️ Yönetim", "🔍 Borçlular", "📜 Rapor"])

with t_yon:
    secilen_ay = st.selectbox("İşlem Yapılacak Ay", aylar, index=datetime.now().month-1)
    
    # --- GELİR EKLEME ---
    st.markdown(f"### 📥 {secilen_ay} Gelir Girişi")
    if is_admin:
        with st.form(key=f"gelir_formu_{secilen_ay}"):
            daireler = st.multiselect("Ödeme Yapan Daireler", DAIRE_LISTESI)
            g_tur = st.radio("Tür", ["Aidat", "Asansör Bakımı"] if secilen_ay=="Ocak" else ["Aidat"], horizontal=True)
            g_tutar = st.number_input("Daire Başı Tutar", value=400)
            submit_gelir = st.form_submit_button("VERİLERİ KAYDET", use_container_width=True)
            
            if submit_gelir:
                if daireler:
                    tarih_fix = f"20.{ay_no_map[secilen_ay]}.2026"
                    yeni_kayitlar = [{"Tarih": tarih_fix, "Ay": secilen_ay, "Daire": d, "Tür": g_tur, "Miktar": g_tutar} for d in daireler]
                    yeni_df = pd.concat([df_gelir, pd.DataFrame(yeni_kayitlar)], ignore_index=True)
                    conn.update(worksheet="Gelirler", data=yeni_df)
                    st.success("Gelirler başarıyla kaydedildi!")
                    time.sleep(1)
                    st.rerun()
                else: st.warning("Lütfen daire seçin!")

    # Gelir Listesi ve Silme
    f_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]
    for idx, row in f_gelir.iterrows():
        c1, c2 = st.columns([0.2, 0.8])
        if is_admin and c1.button("🗑️", key=f"g_sil_{idx}"):
            conn.update(worksheet="Gelirler", data=df_gelir.drop(idx))
            st.rerun()
        c2.info(f"{row['Daire']} | {row['Tür']} | {row['Miktar']} TL")

    st.divider()

    # --- GİDER EKLEME ---
    st.markdown(f"### 📤 {secilen_ay} Gider Girişi")
    if is_admin:
        with st.form(key=f"gider_formu_{secilen_ay}"):
            aciklama = st.text_input("Gider Açıklaması")
            gider_tutar = st.number_input("Tutar", min_value=0)
            submit_gider = st.form_submit_button("GİDERİ KAYDET", use_container_width=True)
            
            if submit_gider:
                if aciklama:
                    tarih_fix = f"20.{ay_no_map[secilen_ay]}.2026"
                    yeni_g = pd.DataFrame([{"Tarih": tarih_fix, "Ay": secilen_ay, "Tür": aciklama, "Miktar": gider_tutar}])
                    conn.update(worksheet="Giderler", data=pd.concat([df_gider, yeni_g], ignore_index=True))
                    st.success("Gider kaydedildi!")
                    time.sleep(1)
                    st.rerun()
                else: st.warning("Açıklama girin!")

    f_gider = df_gider[df_gider["Ay"] == secilen_ay]
    for idx, row in f_gider.iterrows():
        c1, c2 = st.columns([0.2, 0.8])
        if is_admin and c1.button("🗑️", key=f"gid_sil_{idx}"):
            conn.update(worksheet="Giderler", data=df_gider.drop(idx))
            st.rerun()
        c2.error(f"{row['Tür']} | {row['Miktar']} TL")

with t_borc:
    yapanlar = df_gelir[(df_gelir["Ay"] == secilen_ay) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in yapanlar]
    for b in borclular: st.warning(f"❌ {b}")
    if not borclular: st.success("Bu ay herkes ödedi!")

with t_rap:
    st.dataframe(pd.concat([df_gelir.assign(Tip="GELİR"), df_gider.assign(Tip="GİDER")], ignore_index=True).sort_index(ascending=False), use_container_width=True, hide_index=True)

if st.button("🚪 Çıkış Yap", use_container_width=True):
    st.session_state.logged_in_user = None
    st.rerun()
