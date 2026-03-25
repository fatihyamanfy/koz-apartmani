import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. SAFARİ TAM EKRAN VE MOBİL AYARLAR ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide", initial_sidebar_state="collapsed")

# iPhone Safari için "Ana Ekrana Ekle" ayarı (Standalone Mode)
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

# --- 3. GİRİŞ VE KAYIT SİSTEMİ ---
if st.session_state.logged_in_user is None:
    st.title("🏢 Koz Apartmanı")
    tab_giris, tab_kayit = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab_giris:
        u_name = st.text_input("Kullanıcı Adı", key="login_u")
        u_pass = st.text_input("Şifre", type="password", key="login_p")
        if st.button("Giriş", use_container_width=True):
            if u_name == "fatihyaman" and u_pass == "200915":
                st.session_state.logged_in_user = "admin"
                st.rerun()
            elif u_name != "" and len(u_pass) == 6:
                st.session_state.logged_in_user = "user"
                st.rerun()
            else: st.error("Hatalı bilgiler!")

    with tab_kayit:
        st.info("Kayıt olanlar sadece izleme yetkisine sahip olur.")
        new_u = st.text_input("Kullanıcı Adı", key="reg_u")
        new_p = st.text_input("Şifre (6 Rakam)", max_chars=6, key="reg_p")
        if st.button("Kayıt Ol", use_container_width=True):
            if len(new_p) == 6 and new_p.isdigit():
                st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
            else: st.error("Şifre 6 haneli rakam olmalı!")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. MODERN TASARIM (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .bakiye-kutu { 
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%); 
        color: white; padding: 20px; border-radius: 20px; text-align: center; 
        margin-bottom: 25px; box-shadow: 0 10px 20px rgba(30,58,138,0.2);
    }
    .month-card { padding: 8px; border-radius: 8px; text-align: center; color: white; font-weight: bold; font-size: 10px; }
    .bg-green { background-color: #10B981; }
    .bg-red { background-color: #EF4444; }
    /* Liste Tasarımı */
    .item-card {
        background-color: white; padding: 15px; border-radius: 12px;
        margin-bottom: 10px; border: 1px solid #e5e7eb;
        display: flex; justify-content: space-between; align-items: center;
    }
    .item-info { color: #1f2937; font-weight: 600; font-size: 14px; }
    .item-price { color: #1E3A8A; font-weight: 800; font-size: 16px; }
    </style>
""", unsafe_allow_html=True)

# --- 5. ÜST PANEL ---
st.markdown(f'<div class="bakiye-kutu"><div style="font-size:14px; opacity:0.9;">TOPLAM KASA</div><div style="font-size:32px; font-weight:900;">{df_gelir["Miktar"].sum() - df_gider["Miktar"].sum():,.2f} TL</div></div>', unsafe_allow_html=True)

cols = st.columns(12)
for idx, ay_adi in enumerate(aylar):
    gelir_toplam = df_gelir[df_gelir["Ay"] == ay_adi]["Miktar"].sum()
    renk = "bg-green" if gelir_toplam >= 3200 else "bg-red"
    cols[idx].markdown(f'<div class="month-card {renk}">{ay_adi[:3]}</div>', unsafe_allow_html=True)

# --- 6. ANA SEKMELER ---
st.divider()
t_aylik, t_borclular, t_rapor = st.tabs(["⚙️ Yönetim", "🔍 Borçlular", "📜 Rapor"])

with t_aylik:
    secilen_ay = st.selectbox("Ay Seçimi", aylar, index=datetime.now().month-1)
    
    if is_admin:
        with st.expander(f"➕ {secilen_ay} Gelir Ekle", expanded=False):
            daireler = st.multiselect("Daireler", DAIRE_LISTESI)
            c1, c2 = st.columns(2)
            g_tur = c1.radio("Tür", ["Aidat", "Asansör"] if secilen_ay=="Ocak" else ["Aidat"])
            g_tutar = c2.number_input("Tutar", value=400 if g_tur=="Aidat" else 1800)
            if st.button("Kaydet", use_container_width=True):
                yeni = [{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": d, "Tür": g_tur, "Miktar": g_tutar} for d in daireler]
                conn.update(worksheet="Gelirler", data=pd.concat([df_gelir, pd.DataFrame(yeni)], ignore_index=True))
                st.rerun()

    st.markdown(f"### {secilen_ay} Hareketleri")
    f_gelir = df_gelir[df_gelir["Ay"] == secilen_ay]
    for idx, row in f_gelir.iterrows():
        col_del, col_main = st.columns([0.15, 0.85])
        if is_admin and col_del.button("🗑️", key=f"del_g_{idx}"):
            conn.update(worksheet="Gelirler", data=df_gelir.drop(idx)); st.rerun()
        col_main.markdown(f"<div class='item-card'><div class='item-info'>{row['Daire']}<br><small>{row['Tür']}</small></div><div class='item-price'>{row['Miktar']} TL</div></div>", unsafe_allow_html=True)

    if is_admin:
        with st.expander(f"➕ {secilen_ay} Gider Ekle"):
            acik = st.text_input("Gider Adı")
            tut = st.number_input("Tutar ", min_value=0)
            if st.button("Gideri Kaydet", use_container_width=True):
                yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": acik, "Miktar": tut}])
                conn.update(worksheet="Giderler", data=pd.concat([df_gider, yeni_g], ignore_index=True)); st.rerun()

    f_gider = df_gider[df_gider["Ay"] == secilen_ay]
    for idx, row in f_gider.iterrows():
        col_del, col_main = st.columns([0.15, 0.85])
        if is_admin and col_del.button("🗑️", key=f"del_gid_{idx}"):
            conn.update(worksheet="Giderler", data=df_gider.drop(idx)); st.rerun()
        col_main.markdown(f"<div class='item-card'><div class='item-info'>{row['Tür']}<br><small>Gider</small></div><div class='item-price' style='color:#EF4444;'>{row['Miktar']} TL</div></div>", unsafe_allow_html=True)

with t_borclular:
    odeme_yapanlar = df_gelir[(df_gelir["Ay"] == secilen_ay) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in odeme_yapanlar]
    for b in borclular: st.error(f"❌ {b}")
    if not borclular: st.success("Tüm aidatlar ödendi!")

with t_rapor:
    st.dataframe(pd.concat([df_gelir.assign(T="GELİR"), df_gider.assign(T="GİDER")], ignore_index=True).sort_index(ascending=False), use_container_width=True, hide_index=True)

st.sidebar.button("Güvenli Çıkış", on_click=lambda: st.session_state.update({"logged_in_user": None}))
