import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. PROFESYONEL YAPILANDIRMA ---
st.set_page_config(page_title="Koz Yönetim Pro", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp { background-color: #0D1117; color: #C9D1D9; }
        .main-card {
            background: linear-gradient(145deg, #161B22, #0D1117);
            border: 1px solid #30363D; padding: 20px; border-radius: 16px;
            text-align: center; margin-bottom: 20px;
        }
        .stat-val { font-size: 26px; font-weight: 800; color: #58A6FF; }
        .stat-label { font-size: 11px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }
        .stButton>button { border-radius: 10px; border: 1px solid #30363D; background: #21262D; color: white; }
    </style>
""", unsafe_allow_html=True)

# Oturum Durumları
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "page" not in st.session_state:
    st.session_state.page = "Özet"

DAIRE_LISTESI = ["EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4", "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. KOTA DOSTU VERİ YÖNETİMİ ---
conn = st.connection("gsheets", type=GSheetsConnection)

# TTL değerini 60 saniyeye çıkardım. Bu, dakikada en fazla 1 kez okuma yapmasını sağlar.
@st.cache_data(ttl=60) 
def verileri_cek():
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
    except Exception as e:
        # Eğer kota dolduysa boş dönme, hata mesajı ver ama uygulamayı çökertme
        return None, None

def veri_kaydet(worksheet_name, updated_df):
    try:
        # Önce yazma işlemini yap
        conn.update(worksheet=worksheet_name, data=updated_df)
        # Yazma başarılıysa hafızayı (cache) temizle ki bir sonraki okuma güncel olsun
        st.cache_data.clear()
        time.sleep(1) # Google'a nefes aldır
        return True
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ Google Kotası Doldu! Lütfen 1 dakika bekleyip tekrar deneyin.")
        else:
            st.error(f"Hata: {e}")
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

# Veri Yükleme Denemesi
df_gelir, df_gider = verileri_cek()

if df_gelir is None:
    st.warning("🔄 Google bağlantısı şu an çok yoğun. Lütfen sayfayı 30 saniye sonra yenileyin.")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. DASHBOARD ÜST PANEL ---
total_gelir = df_gelir["Miktar"].sum()
total_gider = df_gider["Miktar"].sum()
net_kasa = total_gelir - total_gider

st.markdown(f"""
    <div class="main-card">
        <div class="stat-label">GÜNCEL KASA</div>
        <div class="stat-val">{net_kasa:,.2f} TL</div>
    </div>
""", unsafe_allow_html=True)

# --- 5. NAVİGASYON ---
menu_cols = st.columns(3)
if menu_cols[0].button("🏠 Özet", use_container_width=True): st.session_state.page = "Özet"
if menu_cols[1].button("💸 İşlem", use_container_width=True): st.session_state.page = "İşlem"
if menu_cols[2].button("📊 Rapor", use_container_width=True): st.session_state.page = "Rapor"

# --- SAYFALAR (Mevcut mantık korundu, veri_kaydet fonksiyonu ile güncellendi) ---
if st.session_state.page == "Özet":
    curr_month = aylar[datetime.now().month-1]
    yapanlar = df_gelir[(df_gelir["Ay"] == curr_month) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in yapanlar]
    st.subheader(f"📍 {curr_month} Aidat Takibi")
    c1, c2 = st.columns(2)
    c1.metric("Ödeyen", len(yapanlar))
    c2.metric("Kalan", len(borclular))
    if borclular: st.error(f"Beklenen: {', '.join(borclular)}")

elif st.session_state.page == "İşlem":
    if is_admin:
        sec_ay = st.selectbox("İşlem Ayı", aylar, index=datetime.now().month-1)
        islem = st.selectbox("Tür", ["Gelir Tahsilatı", "Gider Ödemesi"])
        
        with st.form("islem_form"):
            if islem == "Gelir Tahsilatı":
                daireler = st.multiselect("Daireler", DAIRE_LISTESI)
                t_tur = st.selectbox("Kalem", ["Aidat", "Asansör", "Ek Ödeme"])
                miktar = st.number_input("Tutar", 400)
                if st.form_submit_button("KAYDET"):
                    yeni = [{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Daire": d, "Tür": t_tur, "Miktar": miktar} for d in daireler]
                    if veri_kaydet("Gelirler", pd.concat([df_gelir, pd.DataFrame(yeni)], ignore_index=True)):
                        st.success("Başarılı!"); time.sleep(1); st.rerun()
            else:
                acik = st.text_input("Gider Adı")
                miktar = st.number_input("Tutar", 0)
                if st.form_submit_button("GİDER KAYDET"):
                    yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Tür": acik, "Miktar": miktar}])
                    if veri_kaydet("Giderler", pd.concat([df_gider, yeni_g], ignore_index=True)):
                        st.success("Başarılı!"); time.sleep(1); st.rerun()
    else: st.warning("Yetkiniz yok.")

elif st.session_state.page == "Rapor":
    r_ay = st.selectbox("Ay", ["Tümü"] + aylar)
    t1, t2 = st.tabs(["Gelir", "Gider"])
    with t1:
        data = df_gelir if r_ay=="Tümü" else df_gelir[df_gelir["Ay"]==r_ay]
        for i, r in data.iterrows():
            st.write(f"**{r['Daire']}** - {r['Miktar']} TL ({r['Tarih']})")
            if is_admin and st.button("🗑️", key=f"d_{i}"):
                if veri_kaydet("Gelirler", df_gelir.drop(i)): st.rerun()
    with t2:
        data_g = df_gider if r_ay=="Tümü" else df_gider[df_gider["Ay"]==r_ay]
        for i, r in data_g.iterrows():
            st.write(f"**{r['Tür']}** - {r['Miktar']} TL")
            if is_admin and st.button("🗑️", key=f"dg_{i}"):
                if veri_kaydet("Giderler", df_gider.drop(i)): st.rerun()

if st.button("Çıkış"):
    st.session_state.logged_in_user = None; st.rerun()
