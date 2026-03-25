import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. MOBİL UYGULAMA KONFİGÜRASYONU ---
st.set_page_config(page_title="Koz Apartmanı", layout="centered", initial_sidebar_state="collapsed")

# iPhone Safari "Ana Ekrana Ekle" Tam Ekran Modu
st.markdown('<meta name="apple-mobile-web-app-capable" content="yes">', unsafe_allow_html=True)
st.markdown('<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">', unsafe_allow_html=True)

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Yönetim"

DAIRE_LISTESI = ["EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4", "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. VERİ BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
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

# --- 3. TASARIM (DARK & COMPACT UI) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: white; }
    /* Alt Menü Barı */
    .nav-bar {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: #161B22; border-top: 1px solid #30363D;
        display: flex; justify-content: space-around; padding: 10px 0;
        z-index: 999;
    }
    .bakiye-container {
        background: linear-gradient(135deg, #1A1C23 0%, #0D1117 100%);
        border: 1px solid #30363D; padding: 15px; border-radius: 12px;
        text-align: center; margin-bottom: 15px;
    }
    .item-card {
        background: #161B22; border: 1px solid #30363D; border-radius: 10px;
        padding: 10px; margin-bottom: 8px; display: flex; align-items: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. GİRİŞ SİSTEMİ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align:center;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    u = st.text_input("Kullanıcı")
    p = st.text_input("Şifre", type="password")
    if st.button("Sisteme Gir", use_container_width=True):
        if u == "fatihyaman" and p == "200915": st.session_state.logged_in_user = "admin"; st.rerun()
        elif u != "" and len(p) == 6: st.session_state.logged_in_user = "user"; st.rerun()
        else: st.error("Hatalı giriş!")
    st.stop()

df_gelir, df_gider = verileri_yukle()
is_admin = (st.session_state.logged_in_user == "admin")

# --- 5. ALT MENÜ NAVİGASYONU ---
c1, c2, c3 = st.columns(3)
if c1.button("⚙️ Yönetim", use_container_width=True): st.session_state.current_page = "Yönetim"
if c2.button("🔍 Borç", use_container_width=True): st.session_state.current_page = "Borçlular"
if c3.button("📜 Rapor", use_container_width=True): st.session_state.current_page = "Rapor"

st.divider()

# --- SAYFA: YÖNETİM ---
if st.session_state.current_page == "Yönetim":
    kasa = df_gelir["Miktar"].sum() - df_gider["Miktar"].sum()
    st.markdown(f'<div class="bakiye-container"><small style="color:#8B949E">KASA</small><h2 style="color:#58A6FF; margin:0;">{kasa:,.2f} TL</h2></div>', unsafe_allow_html=True)
    
    secilen_ay = st.selectbox("Ay", aylar, index=datetime.now().month-1, label_visibility="collapsed")
    
    tab_in, tab_out = st.tabs(["📥 GELİR", "📤 GİDER"])
    
    with tab_in:
        if is_admin:
            with st.form("gelir_f", clear_on_submit=True):
                dlar = st.multiselect("Daireler", DAIRE_LISTESI)
                tur = st.radio("Tür", ["Aidat", "Asansör"], horizontal=True)
                tut = st.number_input("Tutar", value=400)
                tar = st.date_input("Ödeme Tarihi", datetime.now())
                if st.form_submit_button("KAYDET", use_container_width=True):
                    yeni = [{"Tarih": tar.strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": d, "Tür": tur, "Miktar": tut} for d in dlar]
                    conn.update(worksheet="Gelirler", data=pd.concat([df_gelir, pd.DataFrame(yeni)], ignore_index=True))
                    st.rerun()
        
        for idx, row in df_gelir[df_gelir["Ay"]==secilen_ay].iterrows():
            col_d, col_t = st.columns([0.2, 0.8])
            if is_admin and col_d.button("🗑️", key=f"g_{idx}"):
                conn.update(worksheet="Gelirler", data=df_gelir.drop(idx)); st.rerun()
            col_t.markdown(f"<div class='item-card'><b>{row['Daire']}</b><br>{row['Miktar']} TL - {row['Tarih']}</div>", unsafe_allow_html=True)

    with tab_out:
        if is_admin:
            with st.form("gider_f", clear_on_submit=True):
                acik = st.text_input("Gider Adı")
                tut_g = st.number_input("Tutar ", min_value=0)
                tar_g = st.date_input("Gider Tarihi", datetime.now())
                if st.form_submit_button("GİDERİ KAYDET", use_container_width=True):
                    yeni_g = pd.DataFrame([{"Tarih": tar_g.strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": acik, "Miktar": tut_g}])
                    conn.update(worksheet="Giderler", data=pd.concat([df_gider, yeni_g], ignore_index=True)); st.rerun()

        for idx, row in df_gider[df_gider["Ay"]==secilen_ay].iterrows():
            col_d, col_t = st.columns([0.2, 0.8])
            if is_admin and col_d.button("🗑️", key=f"gid_{idx}"):
                conn.update(worksheet="Giderler", data=df_gider.drop(idx)); st.rerun()
            col_t.markdown(f"<div class='item-card' style='border-left:4px solid #F85149;'><b>{row['Tür']}</b><br>{row['Miktar']} TL - {row['Tarih']}</div>", unsafe_allow_html=True)

# --- SAYFA: BORÇLULAR ---
elif st.session_state.current_page == "Borçlular":
    st.subheader("Ödemeyen Daireler")
    ay_filt = st.selectbox("Kontrol Ayı", aylar, index=datetime.now().month-1)
    yapanlar = df_gelir[(df_gelir["Ay"]==ay_filt) & (df_gelir["Tür"]=="Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in yapanlar]
    for b in borclular: st.error(f"❌ {b}")
    if not borclular: st.success("Herkes ödedi!")

# --- SAYFA: RAPOR ---
elif st.session_state.current_page == "Rapor":
    st.subheader("Genel Hareketler")
    full = pd.concat([df_gelir.assign(T="GELİR"), df_gider.assign(T="GİDER")], ignore_index=True)
    full['dt'] = pd.to_datetime(full['Tarih'], format='%d.%m.%Y', errors='coerce')
    st.dataframe(full.sort_values('dt', ascending=False)[["Tarih", "Ay", "T", "Tür", "Daire", "Miktar"]].fillna("-"), use_container_width=True, hide_index=True)
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()
