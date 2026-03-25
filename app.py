import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. PROFESYONEL YAPILANDIRMA ---
st.set_page_config(page_title="Koz Yönetim Pro", layout="centered", initial_sidebar_state="collapsed")

# iPhone Safari & Mobil PWA Ayarları
st.markdown("""
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <style>
        .stApp { background-color: #0D1117; color: #C9D1D9; }
        [data-testid="stHeader"] { background: rgba(0,0,0,0); }
        .main-card {
            background: linear-gradient(145deg, #161B22, #0D1117);
            border: 1px solid #30363D; padding: 20px; border-radius: 16px;
            text-align: center; margin-bottom: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        .stat-val { font-size: 24px; font-weight: 800; color: #58A6FF; }
        .stat-label { font-size: 12px; color: #8B949E; text-transform: uppercase; letter-spacing: 1px; }
        .item-box {
            background: #161B22; border: 1px solid #30363D; padding: 12px;
            border-radius: 12px; margin-bottom: 8px; display: flex;
            justify-content: space-between; align-items: center;
        }
        .stButton>button { 
            border-radius: 10px; transition: 0.3s; border: 1px solid #30363D;
            background: #21262D; color: white;
        }
        .stButton>button:active { transform: scale(0.95); }
    </style>
""", unsafe_allow_html=True)

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "page" not in st.session_state:
    st.session_state.page = "Özet"

DAIRE_LISTESI = [f"DAİRE-{i}" for i in range(1, 9)] # Dinamik Liste
# Senin listen:
DAIRE_LISTESI = ["EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4", "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. VERİ YÖNETİMİ (STABİLİZASYON) ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10) # 10 saniye cache: Uygulamayı hızlandırır, API hatasını engeller
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
    except:
        return pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

def veri_kaydet(worksheet_name, updated_df):
    try:
        conn.update(worksheet=worksheet_name, data=updated_df)
        st.cache_data.clear() # Kayıt sonrası cache'i temizle ki yeni veri gelsin
        return True
    except Exception as e:
        st.error(f"Bağlantı Hatası: {e}")
        return False

# --- 3. GİRİŞ KONTROLÜ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align:center;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    with st.container():
        u = st.text_input("Yönetici Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if u == "fatihyaman" and p == "200915":
                st.session_state.logged_in_user = "admin"
                st.rerun()
            elif u != "" and len(p) == 6:
                st.session_state.logged_in_user = "user"
                st.rerun()
            else: st.error("Hatalı Giriş!")
    st.stop()

# Veriyi bir kez yükle
df_gelir, df_gider = verileri_cek()
is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. DASHBOARD ÜST PANEL ---
total_gelir = df_gelir["Miktar"].sum()
total_gider = df_gider["Miktar"].sum()
net_kasa = total_gelir - total_gider

st.markdown(f"""
    <div class="main-card">
        <div class="stat-label">GÜNCEL KASA DURUMU</div>
        <div class="stat-val">{net_kasa:,.2f} TL</div>
        <div style="display: flex; justify-content: space-around; margin-top: 15px; border-top: 1px solid #30363D; padding-top: 10px;">
            <div><div class="stat-label">GELİR</div><div style="color:#3FB950; font-weight:bold;">{total_gelir:,.0f}</div></div>
            <div><div class="stat-label">GİDER</div><div style="color:#F85149; font-weight:bold;">{total_gider:,.0f}</div></div>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 5. PROFESYONEL NAVİGASYON ---
menu_cols = st.columns(3)
if menu_cols[0].button("🏠 Özet", use_container_width=True): st.session_state.page = "Özet"
if menu_cols[1].button("💸 İşlem", use_container_width=True): st.session_state.page = "İşlem"
if menu_cols[2].button("📊 Rapor", use_container_width=True): st.session_state.page = "Rapor"

st.write("")

# --- SAYFA: ÖZET & BORÇLULAR ---
if st.session_state.page == "Özet":
    curr_month = aylar[datetime.now().month-1]
    st.subheader(f"📍 {curr_month} Ayı Durumu")
    
    # Borçlu Analizi
    yapanlar = df_gelir[(df_gelir["Ay"] == curr_month) & (df_gelir["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in yapanlar]
    
    c1, c2 = st.columns(2)
    c1.metric("Ödeyen", f"{len(yapanlar)} Daire")
    c2.metric("Kalan", f"{len(borclular)} Daire", delta=-len(borclular), delta_color="inverse")
    
    if borclular:
        with st.expander("⚠️ Aidat Beklenen Daireler"):
            for b in borclular: st.write(f"• {b}")
    else:
        st.success("Tüm aidatlar toplandı! 🎉")

# --- SAYFA: İŞLEM GİRİŞİ (GELİR/GİDER) ---
elif st.session_state.page == "İşlem":
    if not is_admin:
        st.warning("Bu sayfa sadece yöneticiye özeldir.")
    else:
        secilen_ay = st.selectbox("İşlem Ayı", aylar, index=datetime.now().month-1)
        islem_tipi = st.segmented_control("İşlem Türü", ["Gelir Tahsilatı", "Gider Ödemesi"], default="GelirTahsilatı")
        
        if islem_tipi == "Gelir Tahsilatı":
            with st.form("gelir_form", clear_on_submit=True):
                sec_daireler = st.multiselect("Daire Seçin", DAIRE_LISTESI)
                t_tur = st.selectbox("Tür", ["Aidat", "Asansör Bakımı", "Ek Ödeme"])
                t_miktar = st.number_input("Tutar (Daire Başı)", value=400)
                t_tarih = st.date_input("İşlem Tarihi")
                if st.form_submit_button("TAHSİLATI KAYDET", use_container_width=True):
                    yeni_data = []
                    for d in sec_daireler:
                        yeni_data.append({"Tarih": t_tarih.strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": d, "Tür": t_tur, "Miktar": t_miktar})
                    if veri_kaydet("Gelirler", pd.concat([df_gelir, pd.DataFrame(yeni_data)], ignore_index=True)):
                        st.success("Kayıt Başarılı!"); time.sleep(1); st.rerun()

        else:
            with st.form("gider_form", clear_on_submit=True):
                g_aciklama = st.text_input("Gider Açıklaması (Örn: Elektrik, Temizlik)")
                g_miktar = st.number_input("Tutar", min_value=0)
                g_tarih = st.date_input("İşlem Tarihi")
                if st.form_submit_button("GİDERİ KAYDET", use_container_width=True):
                    yeni_gider = pd.DataFrame([{"Tarih": g_tarih.strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": g_aciklama, "Miktar": g_miktar}])
                    if veri_kaydet("Giderler", pd.concat([df_gider, yeni_gider], ignore_index=True)):
                        st.success("Gider Kaydedildi!"); time.sleep(1); st.rerun()

# --- SAYFA: RAPOR VE SİLME ---
elif st.session_state.page == "Rapor":
    r_ay = st.selectbox("Ay Filtrele", ["Tümü"] + aylar)
    
    # Veri Filtreleme
    f_gelir = df_gelir if r_ay == "Tümü" else df_gelir[df_gelir["Ay"] == r_ay]
    f_gider = df_gider if r_ay == "Tümü" else df_gider[df_gider["Ay"] == r_ay]
    
    tab1, tab2 = st.tabs(["📥 Gelirler", "📤 Giderler"])
    
    with tab1:
        for idx, row in f_gelir.iterrows():
            with st.container():
                c1, c2 = st.columns([0.8, 0.2])
                c1.markdown(f"**{row['Daire']}** \n<small>{row['Tür']} | {row['Tarih']}</small>", unsafe_allow_html=True)
                c2.markdown(f"**{row['Miktar']}**")
                if is_admin:
                    if st.button("🗑️", key=f"del_gel_{idx}"):
                        if veri_kaydet("Gelirler", df_gelir.drop(idx)): st.rerun()
                st.divider()

    with tab2:
        for idx, row in f_gider.iterrows():
            with st.container():
                c1, c2 = st.columns([0.8, 0.2])
                c1.markdown(f"**{row['Tür']}** \n<small>{row['Tarih']}</small>", unsafe_allow_html=True)
                c2.markdown(f"<span style='color:#F85149;'>-{row['Miktar']}</span>", unsafe_allow_html=True)
                if is_admin:
                    if st.button("🗑️", key=f"del_gid_{idx}"):
                        if veri_kaydet("Giderler", df_gider.drop(idx)): st.rerun()
                st.divider()

# --- ÇIKIŞ ---
st.write("")
if st.button("🚪 Güvenli Çıkış", use_container_width=True):
    st.session_state.logged_in_user = None
    st.rerun()
