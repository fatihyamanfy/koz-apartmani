import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. AYARLAR ---
st.set_page_config(page_title="Koz Yönetim Pro", layout="centered", initial_sidebar_state="collapsed")

# iPhone Safari & Mobil Görünüm
st.markdown("""
    <style>
        .stApp { background-color: #0D1117; color: #C9D1D9; }
        .main-card {
            background: #161B22; border: 1px solid #30363D;
            padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px;
        }
        .stat-val { font-size: 28px; font-weight: 800; color: #58A6FF; }
        .stButton>button { border-radius: 10px; background: #21262D; color: white; border: 1px solid #30363D; }
    </style>
""", unsafe_allow_html=True)

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "page" not in st.session_state:
    st.session_state.page = "Özet"

DAIRE_LISTESI = ["EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4", "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. KOTA KORUMALI VERİ YÖNETİMİ ---
conn = st.connection("gsheets", type=GSheetsConnection)

# TTL'i 120 saniye yaptım. Google'ı çok daha az rahatsız edecek.
@st.cache_data(ttl=120) 
def verileri_yukle():
    try:
        df_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all")
        df_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all")
        
        def temizle(df, beklenen_cols):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "daire": "Daire", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            for c in beklenen_cols:
                if c not in df.columns: df[c] = ""
            return df[beklenen_cols]

        return temizle(df_gelir, ["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               temizle(df_gider, ["Tarih", "Ay", "Tür", "Miktar"])
    except Exception:
        # Hata anında (Kota dolduğunda) boş dönmek yerine mevcut session_state'i kullanacağız
        return None, None

def güvenli_kaydet(ws_name, updated_df):
    try:
        conn.update(worksheet=ws_name, data=updated_df)
        st.cache_data.clear() # Sadece başarılı yazma sonrası temizle
        st.toast("✅ İşlem Başarılı!", icon="🚀")
        time.sleep(2) # Google'a nefes payı
        return True
    except Exception as e:
        st.error("⚠️ Google şu an çok yoğun. Lütfen 30 saniye bekleyip tekrar deneyin.")
        return False

# --- 3. GİRİŞ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align:center;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    u = st.text_input("Yönetici Adı")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş", use_container_width=True):
        if u == "fatihyaman" and p == "200915":
            st.session_state.logged_in_user = "admin"; st.rerun()
        elif u != "" and len(p) == 6:
            st.session_state.logged_in_user = "user"; st.rerun()
        else: st.error("Hatalı Giriş!")
    st.stop()

# Veri Okuma
gelir_df, gider_df = verileri_yukle()

# Eğer okuma başarısızsa (Kota hatası), uygulamayı durdurmak yerine uyarı ver
if gelir_df is None:
    st.info("ℹ️ Veriler güncelleniyor, lütfen bekleyin... (Kota koruması aktif)")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. PANEL ---
kasa = gelir_df["Miktar"].sum() - gider_df["Miktar"].sum()
st.markdown(f'<div class="main-card"><div style="color:#8B949E; font-size:12px;">NET KASA</div><div class="stat-val">{kasa:,.2f} TL</div></div>', unsafe_allow_html=True)

menu = st.columns(3)
if menu[0].button("🏠 Özet"): st.session_state.page = "Özet"
if menu[1].button("💸 İşlem"): st.session_state.page = "İşlem"
if menu[2].button("📊 Rapor"): st.session_state.page = "Rapor"

# --- SAYFA MANTIKLARI ---
if st.session_state.page == "Özet":
    ay_simdi = aylar[datetime.now().month-1]
    st.subheader(f"📍 {ay_simdi} Aidat Takibi")
    yapanlar = gelir_df[(gelir_df["Ay"] == ay_simdi) & (gelir_df["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in yapanlar]
    c1, c2 = st.columns(2)
    c1.metric("Ödeyen", len(yapanlar))
    c2.metric("Kalan", len(borclular))
    if borclular: st.warning(f"Ödeme Beklenen: {', '.join(borclular)}")

elif st.session_state.page == "İşlem":
    if is_admin:
        sec_ay = st.selectbox("İşlem Ayı", aylar, index=datetime.now().month-1)
        tip = st.radio("İşlem Türü", ["Gelir", "Gider"], horizontal=True)
        
        with st.form("islem_form", clear_on_submit=True):
            if tip == "Gelir":
                d_sec = st.multiselect("Daireler", DAIRE_LISTESI)
                t_tur = st.selectbox("Kalem", ["Aidat", "Asansör", "Ek Ödeme"])
                t_mik = st.number_input("Tutar", 400)
                if st.form_submit_button("KAYDET"):
                    yeni = [{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Daire": d, "Tür": t_tur, "Miktar": t_mik} for d in d_sec]
                    if güvenli_kaydet("Gelirler", pd.concat([gelir_df, pd.DataFrame(yeni)], ignore_index=True)):
                        st.rerun()
            else:
                acik = st.text_input("Gider Adı")
                mik = st.number_input("Tutar", 0)
                if st.form_submit_button("GİDERİ KAYDET"):
                    yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Tür": acik, "Miktar": mik}])
                    if güvenli_kaydet("Giderler", pd.concat([gider_df, yeni_g], ignore_index=True)):
                        st.rerun()
    else: st.error("Yetkiniz yok.")

elif st.session_state.page == "Rapor":
    r_ay = st.selectbox("Filtre", ["Tümü"] + aylar)
    t1, t2 = st.tabs(["Gelirler", "Giderler"])
    with t1:
        data = gelir_df if r_ay == "Tümü" else gelir_df[gelir_df["Ay"]==r_ay]
        for i, r in data.iterrows():
            st.write(f"**{r['Daire']}** - {r['Miktar']} TL")
            if is_admin and st.button("🗑️", key=f"del_{i}"):
                if güvenli_kaydet("Gelirler", gelir_df.drop(i)): st.rerun()
    with t2:
        data_g = gider_df if r_ay == "Tümü" else gider_df[gider_df["Ay"]==r_ay]
        for i, r in data_g.iterrows():
            st.write(f"**{r['Tür']}** - {r['Miktar']} TL")
            if is_admin and st.button("🗑️", key=f"gdel_{i}"):
                if güvenli_kaydet("Giderler", gider_df.drop(i)): st.rerun()

if st.button("Çıkış Yap"):
    st.session_state.logged_in_user = None; st.rerun()
