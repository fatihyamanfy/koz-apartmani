import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. SAFARİ TAM EKRAN VE MOBİL AYARLAR ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide", initial_sidebar_state="collapsed")

# iPhone Safari Standalone Meta Etiketleri
st.markdown('<meta name="apple-mobile-web-app-capable" content="yes">', unsafe_allow_html=True)
st.markdown('<meta name="apple-mobile-web-app-status-bar-style" content="black">', unsafe_allow_html=True)

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
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            return df[["Tarih", "Ay", "Daire", "Tür", "Miktar"]]

        def temizle_gider(df):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            return df[["Tarih", "Ay", "Tür", "Miktar"]]

        return temizle_gelir(raw_gelir), temizle_gider(raw_gider)
    except Exception:
        return pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

df_gelir, df_gider = verileri_yukle()

# --- 3. GİRİŞ VE KAYIT ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align: center; color: white;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    tab_giris, tab_kayit = st.tabs(["Giriş", "Kayıt"])
    with tab_giris:
        u_name = st.text_input("Kullanıcı Adı")
        u_pass = st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir", use_container_width=True):
            if u_name == "fatihyaman" and u_pass == "200915":
                st.session_state.logged_in_user = "admin"
                st.rerun()
            elif u_name != "" and len(u_pass) == 6:
                st.session_state.logged_in_user = "user"
                st.rerun()
            else: st.error("Hatalı giriş!")
    with tab_kayit:
        new_u = st.text_input("Kullanıcı Adı ")
        new_p = st.text_input("6 Haneli Şifre", max_chars=6)
        if st.button("Kaydı Tamamla", use_container_width=True):
            if len(new_p) == 6 and new_p.isdigit(): st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
            else: st.error("Şifre 6 haneli rakam olmalı!")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. MINIMALIST DARK DESIGN (CSS) ---
st.markdown("""
    <style>
    /* Ana Arka Plan */
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Bakiye Kartı */
    .bakiye-kutu { 
        background-color: #1A1C23; 
        border: 1px solid #30363D;
        color: #FFFFFF; padding: 25px; border-radius: 15px; text-align: center; 
        margin-bottom: 20px;
    }
    
    /* Ay Kartları */
    .month-card { padding: 6px; border-radius: 6px; text-align: center; color: white; font-weight: bold; font-size: 10px; }
    .bg-green { background-color: #0E4429; border: 1px solid #26a641; }
    .bg-red { background-color: #490E0E; border: 1px solid #f85149; }
    
    /* Liste Elemanları */
    .item-card {
        background-color: #161B22; padding: 12px; border-radius: 10px;
        margin-bottom: 8px; border: 1px solid #30363D;
        display: flex; justify-content: space-between; align-items: center;
    }
    .item-info { color: #C9D1D9; font-size: 14px; line-height: 1.4; }
    .item-price { color: #58A6FF; font-weight: bold; font-size: 15px; }
    
    /* Tab ve Selectbox Renkleri */
    .stTabs [data-baseweb="tab-list"] { background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #8B949E; }
    .stTabs [aria-selected="true"] { color: #58A6FF !important; }
    </style>
""", unsafe_allow_html=True)

# --- 5. ÜST PANEL ---
kasa_net = df_gelir["Miktar"].sum() - df_gider["Miktar"].sum()
st.markdown(f'<div class="bakiye-kutu"><div style="color: #8B949E; font-size:13px; letter-spacing:1px;">KASA BAKİYESİ</div><div style="font-size:30px; font-weight:700; color:#58A6FF;">{kasa_net:,.2f} TL</div></div>', unsafe_allow_html=True)

cols = st.columns(12)
for idx, ay_adi in enumerate(aylar):
    gelir_toplam = df_gelir[df_gelir["Ay"] == ay_adi]["Miktar"].sum()
    renk = "bg-green" if gelir_toplam >= 3200 else "bg-red"
    cols[idx].markdown(f'<div class="month-card {renk}">{ay_adi[:3]}</div>', unsafe_allow_html=True)

# --- 6. SEKMELER ---
st.write("")
t_aylik, t_borclular, t_rapor = st.tabs(["Yönetim", "Borçlular", "Rapor"])

with t_aylik:
    secilen_ay = st.selectbox("Ay Seçin", aylar, index=datetime.now().month-1, label_visibility="collapsed")
    
    if is_admin:
        with st.expander(f"📥 {secilen_ay} Geliri İşle", expanded=False):
            daireler = st.multiselect("Daireler", DAIRE_LISTESI)
            g_tur = st.radio("Tür", ["Aidat", "Asansör"] if secilen_ay=="Ocak" else ["Aidat"], horizontal=True)
            g_tutar = st.number_input("Tutar ", value=400 if g_tur=="Aidat" else 1800)
            if st.button("Veriyi Kaydet", use_container_width=True):
                yeni = [{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": d, "Tür": g_tur, "Miktar": g_tutar} for d in daireler]
                conn.update(worksheet="Gelirler", data=pd.concat([df_gelir, pd.DataFrame(yeni)], ignore_index=True))
                st.rerun()

    # Gelir Listesi
    f_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]
    for idx, row in f_gelir.iterrows():
        c_del, c_main = st.columns([0.15, 0.85])
        if is_admin and c_del.button("🗑️", key=f"del_g_{idx}"):
            conn.update(worksheet="Gelirler", data=df_gelir.drop(idx)); st.rerun()
        c_main.markdown(f"<div class='item-card'><div class='item-info'>{row['Daire']}<br><small style='color:#8B949E'>{row['Tür']}</small></div><div class='item-price'>{row['Miktar']} TL</div></div>", unsafe_allow_html=True)

    st.write("")
    if is_admin:
        with st.expander(f"📤 {secilen_ay} Gideri İşle"):
            acik = st.text_input("Gider Adı ")
            tut = st.number_input("Tutar  ", min_value=0)
            if st.button("Gideri Kaydet ", use_container_width=True):
                yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": acik, "Miktar": tut}])
                conn.update(worksheet="Giderler", data=pd.concat([df_gider, yeni_g], ignore_index=True)); st.rerun()

    f_gider = df_gider[df_gider["Ay"] == secilen_ay]
    for idx, row in f_gider.iterrows():
        c_del, c_main = st.columns([0.15, 0.85])
        if is_admin and c_del.button("🗑️", key=f"del_gid_{idx}"):
            conn.update(worksheet="Giderler", data=df_gider.drop(idx)); st.rerun()
        c_main.markdown(f"<div class='item-card'><div class='item-info'>{row['Tür']}<br><small style='color:#8B949E'>Gider</small></div><div class='item-price' style='color:#F85149;'>{row['Miktar']} TL</div></div>", unsafe_allow_html=True)

with t_borclular:
    odeme_yapanlar = df_gelir[(df_gelir["Ay"] == secilen_ay) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in odeme_yapanlar]
    for b in borclular: st.error(f"❌ {b}")
    if not borclular: st.success("Tüm aidatlar ödendi!")

with t_rapor:
    rapor_df = pd.concat([df_gelir.assign(T="GELİR"), df_gider.assign(T="GİDER")], ignore_index=True).sort_index(ascending=False)
    st.dataframe(rapor_df[["Tarih", "Ay", "T", "Tür", "Daire", "Miktar"]].fillna("-"), use_container_width=True, hide_index=True)

if st.button("Çıkış", use_container_width=True):
    st.session_state.logged_in_user = None
    st.rerun()
