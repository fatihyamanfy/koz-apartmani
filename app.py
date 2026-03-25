import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. SAFARİ VE MOBİL OPTİMİZASYON ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide", initial_sidebar_state="collapsed")

# iPhone Safari Standalone Modu
st.markdown('<meta name="apple-mobile-web-app-capable" content="yes">', unsafe_allow_html=True)
st.markdown('<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">', unsafe_allow_html=True)

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

@st.cache_data(ttl=2)
def verileri_yukle():
    try:
        raw_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all", axis=0)
        raw_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all", axis=0)
        
        def temizle_df(df, cols):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "daire": "Daire", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]

        return temizle_df(raw_gelir, ["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               temizle_df(raw_gider, ["Tarih", "Ay", "Tür", "Miktar"])
    except:
        return pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

df_gelir, df_gider = verileri_yukle()

# --- 3. MODERN DARK DESIGN (TAM KONTROL) ---
st.markdown("""
    <style>
    /* Global Karanlık Tema */
    .stApp { background-color: #0E1117 !important; color: #FFFFFF; }
    
    /* Sayfa sünmesini engelleme (Overscroll) */
    html, body { 
        background-color: #0E1117 !important; 
        overscroll-behavior-y: contain; /* Sayfa bitince sünmeyi engeller */
    }

    /* Giriş Sekmeleri */
    .stTabs [data-baseweb="tab-list"] { background-color: #161B22; border-radius: 10px; padding: 5px; }
    .stTabs [data-baseweb="tab"] { color: #8B949E !important; }
    .stTabs [aria-selected="true"] { color: #58A6FF !important; background-color: #1A1C23; border-radius: 8px; }

    /* Kasa Kartı */
    .bakiye-kutu { 
        background: #1A1C23; border: 1px solid #30363D;
        color: #FFFFFF; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 15px;
    }
    
    /* İşlem Kartları (Mobil Uyumlu) */
    .item-card {
        background-color: #161B22; padding: 12px; border-radius: 10px;
        margin-bottom: 8px; border: 1px solid #30363D;
        display: flex; justify-content: space-between; align-items: center;
        width: 100%;
    }
    .item-info { color: #C9D1D9; font-size: 14px; flex-grow: 1; text-align: left; }
    .item-price { color: #58A6FF; font-weight: bold; font-size: 15px; min-width: 80px; text-align: right; }
    
    /* Buton ve Inputlar */
    .stButton>button { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 4. GİRİŞ VE KAYIT SİSTEMİ ---
if st.session_state.logged_in_user is None:
    # Giriş ekranında kaydırmayı tamamen kapat
    st.markdown("<style>html, body { overflow: hidden; }</style>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: white; padding-top: 50px;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    t_in, t_up = st.tabs(["Giriş", "Kayıt"])
    with t_in:
        u_name = st.text_input("Kullanıcı Adı")
        u_pass = st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir", use_container_width=True):
            if u_name == "fatihyaman" and u_pass == "200915":
                st.session_state.logged_in_user = "admin"
                st.rerun()
            elif u_name != "" and len(u_pass) == 6 and u_pass.isdigit():
                st.session_state.logged_in_user = "user"
                st.rerun()
            else: st.error("Hatalı kullanıcı adı veya şifre!")
    with t_up:
        st.info("Kayıt olanlar sadece izleme yetkisine sahip olur.")
        new_u = st.text_input("Yeni Kullanıcı Adı")
        new_p = st.text_input("6 Haneli Şifre", max_chars=6)
        if st.button("Kaydı Tamamla", use_container_width=True):
            if len(new_p) == 6 and new_p.isdigit(): st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
            else: st.error("Şifre 6 haneli rakam olmalı!")
    st.stop()

# --- 5. ANA UYGULAMA PANELİ ---
is_admin = (st.session_state.logged_in_user == "admin")

# Kasa Özeti
kasa_t = df_gelir["Miktar"].sum() - df_gider["Miktar"].sum()
st.markdown(f'<div class="bakiye-kutu"><div style="color:#8B949E; font-size:12px; letter-spacing:1px;">GÜNCEL BAKİYE</div><div style="font-size:30px; font-weight:900; color:#58A6FF;">{kasa_t:,.2f} TL</div></div>', unsafe_allow_html=True)

t_yonetim, t_borclular, t_rapor = st.tabs(["⚙️ Yönetim", "🔍 Borçlular", "📜 Rapor"])

with t_yonetim:
    secilen_ay = st.selectbox("İşlem Ayı", aylar, index=datetime.now().month-1)
    
    if is_admin:
        with st.expander(f"📥 {secilen_ay} Gelir Girişi", expanded=False):
            daireler = st.multiselect("Daireler", DAIRE_LISTESI)
            c1, c2 = st.columns(2)
            g_tur = c1.radio("Tür", ["Aidat", "Asansör"] if secilen_ay=="Ocak" else ["Aidat"], horizontal=True)
            g_tutar = c2.number_input("Tutar", value=400 if g_tur=="Aidat" else 1800)
            if st.button("Geliri Kaydet", use_container_width=True):
                kayit_tarihi = f"20.{ay_no_map[secilen_ay]}.2026"
                yeni = [{"Tarih": kayit_tarihi, "Ay": secilen_ay, "Daire": d, "Tür": g_tur, "Miktar": g_tutar} for d in daireler]
                conn.update(worksheet="Gelirler", data=pd.concat([df_gelir, pd.DataFrame(yeni)], ignore_index=True))
                st.success("Kaydedildi!"); time.sleep(0.5); st.rerun()

    # Gelirleri Listeleme ve Silme
    f_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]
    if not f_gelir.empty:
        for idx, row in f_gelir.iterrows():
            col_del, col_txt = st.columns([0.15, 0.85])
            if is_admin and col_del.button("🗑️", key=f"del_g_{idx}"):
                conn.update(worksheet="Gelirler", data=df_gelir.drop(idx))
                st.rerun()
            col_txt.markdown(f"<div class='item-card'><div class='item-info'>{row['Daire']}<br><small style='color:#8B949E'>{row['Tür']} | {row['Tarih']}</small></div><div class='item-price'>{row['Miktar']} TL</div></div>", unsafe_allow_html=True)

    st.divider()

    if is_admin:
        with st.expander(f"📤 {secilen_ay} Gider Girişi"):
            acik = st.text_input("Gider Açıklaması")
            tut = st.number_input("Gider Tutarı", min_value=0)
            if st.button("Gideri Kaydet", use_container_width=True):
                kayit_tarihi = f"20.{ay_no_map[secilen_ay]}.2026"
                yeni_g = pd.DataFrame([{"Tarih": kayit_tarihi, "Ay": secilen_ay, "Tür": acik, "Miktar": tut}])
                conn.update(worksheet="Giderler", data=pd.concat([df_gider, yeni_g], ignore_index=True))
                st.success("Gider Kaydedildi!"); time.sleep(0.5); st.rerun()

    f_gider = df_gider[df_gider["Ay"] == secilen_ay]
    if not f_gider.empty:
        for idx, row in f_gider.iterrows():
            col_del, col_txt = st.columns([0.15, 0.85])
            if is_admin and col_del.button("🗑️", key=f"del_gid_{idx}"):
                conn.update(worksheet="Giderler", data=df_gider.drop(idx))
                st.rerun()
            col_txt.markdown(f"<div class='item-card'><div class='item-info'>{row['Tür']}<br><small style='color:#8B949E'>Gider | {row['Tarih']}</small></div><div class='item-price' style='color:#EF4444;'>{row['Miktar']} TL</div></div>", unsafe_allow_html=True)

with t_borclular:
    odeme_yapanlar = df_gelir[(df_gelir["Ay"] == secilen_ay) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in odeme_yapanlar]
    for b in borclular: st.error(f"❌ {b}")
    if not borclular: st.success("Tüm aidatlar ödendi!")

with t_rapor:
    rapor_df = pd.concat([df_gelir.assign(T="GELİR"), df_gider.assign(T="GİDER")], ignore_index=True)
    rapor_df['Tarih_DT'] = pd.to_datetime(rapor_df['Tarih'], format='%d.%m.%Y', errors='coerce')
    rapor_df = rapor_df.sort_values(by='Tarih_DT', ascending=False)
    st.dataframe(rapor_df[["Tarih", "Ay", "T", "Tür", "Daire", "Miktar"]].fillna("-"), use_container_width=True, hide_index=True)

st.markdown("<br><hr>", unsafe_allow_html=True)
if st.button("🚪 Güvenli Çıkış", use_container_width=True):
    st.session_state.logged_in_user = None
    st.rerun()
