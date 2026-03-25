import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. MOBİL OPTİMİZASYON VE TASARIM ---
st.set_page_config(page_title="Koz Yönetim", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp { background-color: #0D1117; color: #C9D1D9; }
        .main-card {
            background: #161B22; border: 1px solid #30363D;
            padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px;
        }
        .stat-val { font-size: 28px; font-weight: 800; color: #58A6FF; }
        .data-row { 
            background: #0D1117; border: 1px solid #30363D; padding: 10px; 
            border-radius: 8px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;
        }
        /* Yenileme Butonu Özel Tasarımı */
        .refresh-btn > button {
            background-color: #21262D !important;
            border: 1px solid #58A6FF !important;
            color: #58A6FF !important;
            font-weight: bold !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- 2. YENİLEME BUTONU (EN ÜSTTE) ---
# iPhone kullanıcıları için kolay erişim
col_ref, col_space = st.columns([0.5, 0.5])
with col_ref:
    if st.button("🔄 Sayfayı Yenile", key="refresh_top"):
        st.cache_data.clear() # Önbelleği temizle
        st.rerun() # Sayfayı zorla yeniden yükle

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "page" not in st.session_state:
    st.session_state.page = "Özet"

DAIRE_LISTESI = ["EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4", "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 3. KOTA DOSTU VERİ YÖNETİMİ ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=15) # 15 saniye cache: Hem güncel veri hem de kota koruması
def verileri_yukle():
    try:
        # Google'dan ham verileri oku
        df_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all")
        df_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all")
        
        def temizle(df, cols):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "daire": "Daire", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True, errors='coerce')
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            return df[cols]

        g_clean = temizle(df_gelir, ["Tarih", "Ay", "Daire", "Tür", "Miktar"])
        gid_clean = temizle(df_gider, ["Tarih", "Ay", "Tür", "Miktar"])
        
        return g_clean.sort_values(by="Tarih", ascending=True), \
               gid_clean.sort_values(by="Tarih", ascending=True)
    except Exception as e:
        # Eğer kota dolduysa None dön
        return None, None

def guvenli_kaydet(ws_name, updated_df):
    try:
        save_df = updated_df.copy()
        save_df["Tarih"] = save_df["Tarih"].dt.strftime("%d.%m.%Y")
        conn.update(worksheet=ws_name, data=save_df)
        st.cache_data.clear()
        st.toast("İşlem Başarılı!", icon="✅")
        time.sleep(2) # Google'a nefes payı bırak
        return True
    except:
        st.error("Google şu an meşgul. Lütfen 10 saniye bekleyip Yenile butonuna basın.")
        return False

# --- 4. GİRİŞ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h3 style='text-align:center;'>🏢 Koz Apartmanı</h3>", unsafe_allow_html=True)
    u = st.text_input("Yönetici")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if u == "fatihyaman" and p == "200915":
            st.session_state.logged_in_user = "admin"; st.rerun()
        elif u != "" and len(p) == 6:
            st.session_state.logged_in_user = "user"; st.rerun()
        else: st.error("Hatalı Giriş!")
    st.stop()

# Veri Yükleme Motoru
gelir_df, gider_df = verileri_yukle()

if gelir_df is None:
    st.warning("⚠️ Google bağlantısı geçici olarak kesildi (Kota doldu).")
    st.info("Lütfen 30 saniye bekleyip yukarıdaki 'Sayfayı Yenile' butonuna basın.")
    if st.button("Bağlantıyı Tekrar Dene"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 5. PANEL ---
kasa = gelir_df["Miktar"].sum() - gider_df["Miktar"].sum()
st.markdown(f'<div class="main-card"><small>TOPLAM KASA</small><div class="stat-val">{kasa:,.2f} TL</div></div>', unsafe_allow_html=True)

menu = st.columns(3)
if menu[0].button("🏠 Özet"): st.session_state.page = "Özet"
if menu[1].button("💸 İşlem"): st.session_state.page = "İşlem"
if menu[2].button("📊 Rapor"): st.session_state.page = "Rapor"

# --- SAYFALAR ---
if st.session_state.page == "Özet":
    ay_simdi = aylar[datetime.now().month-1]
    st.subheader(f"📍 {ay_simdi} Tahsilat")
    yapanlar = gelir_df[(gelir_df["Ay"] == ay_simdi) & (gelir_df["Tür"] == "Aidat")]["Daire"].tolist()
    for d in DAIRE_LISTESI:
        icon = "✅" if d in yapanlar else "❌"
        st.write(f"{icon} {d}")

elif st.session_state.page == "İşlem":
    if is_admin:
        sec_ay = st.selectbox("Ay Seçin", aylar, index=datetime.now().month-1)
        tip = st.radio("İşlem", ["Gelir", "Gider"], horizontal=True)
        
        with st.form("islem_form", clear_on_submit=True):
            tarih = st.date_input("Tarih", datetime.now())
            if tip == "Gelir":
                d_sec = st.multiselect("Daireler", DAIRE_LISTESI, placeholder="Daire Seçin")
                turler = ["Aidat", "Ek Ödeme"]
                if sec_ay == "Ocak": turler.append("Asansör Revizyon")
                t_tur = st.selectbox("Tür", turler)
                t_mik = st.number_input("Tutar", value=400)
                if st.form_submit_button("KAYDET"):
                    zaten = gelir_df[(gelir_df["Ay"] == sec_ay) & (gelir_df["Tür"] == t_tur)]["Daire"].tolist()
                    temiz = [d for d in d_sec if d not in zaten]
                    if temiz:
                        yeni = [{"Tarih": pd.to_datetime(tarih), "Ay": sec_ay, "Daire": d, "Tür": t_tur, "Miktar": t_mik} for d in temiz]
                        if guvenli_kaydet("Gelirler", pd.concat([gelir_df, pd.DataFrame(yeni)], ignore_index=True)): st.rerun()
            else:
                acik = st.text_input("Gider Adı")
                mik = st.number_input("Tutar", 0)
                if st.form_submit_button("GİDER KAYDET"):
                    if acik:
                        yeni_g = pd.DataFrame([{"Tarih": pd.to_datetime(tarih), "Ay": sec_ay, "Tür": acik, "Miktar": mik}])
                        if guvenli_kaydet("Giderler", pd.concat([gider_df, yeni_g], ignore_index=True)): st.rerun()

        st.divider()
        st.subheader(f"🔍 {sec_ay} Kayıtları")
        t1, t2 = st.tabs(["Gelir", "Gider"])
        with t1:
            for i, r in gelir_df[gelir_df["Ay"]==sec_ay].iterrows():
                c1, c2 = st.columns([0.8, 0.2])
                c1.markdown(f"<div class='data-row'><div>{r['Daire']}<br><small>{r['Tarih'].strftime('%d.%m')}</small></div><b>{r['Miktar']}</b></div>", unsafe_allow_html=True)
                if c2.button("🗑️", key=f"dg_{i}"):
                    if guvenli_kaydet("Gelirler", gelir_df.drop(i)): st.rerun()
        with t2:
            for i, r in gider_df[gider_df["Ay"]==sec_ay].iterrows():
                c1, c2 = st.columns([0.8, 0.2])
                c1.markdown(f"<div class='data-row'><div>{r['Tür']}<br><small>{r['Tarih'].strftime('%d.%m')}</small></div><b>{r['Miktar']}</b></div>", unsafe_allow_html=True)
                if c2.button("🗑️", key=f"dgid_{i}"):
                    if guvenli_kaydet("Giderler", gider_df.drop(i)): st.rerun()
    else: st.error("Yetkiniz yok.")

elif st.session_state.page == "Rapor":
    r_ay = st.selectbox("Filtre", ["Tümü"] + aylar)
    st.info("Kayıtlar tarih sırasına göredir.")
    t1, t2 = st.tabs(["Gelir", "Gider"])
    with t1:
        data = gelir_df if r_ay == "Tümü" else gelir_df[gelir_df["Ay"] == r_ay]
        disp = data.copy()
        disp["Tarih"] = disp["Tarih"].dt.strftime("%d.%m.%Y")
        st.dataframe(disp, use_container_width=True, hide_index=True)
    with t2:
        data_g = gider_df if r_ay == "Tümü" else gider_df[gider_df["Ay"] == r_ay]
        disp_g = data_g.copy()
        disp_g["Tarih"] = disp_g["Tarih"].dt.strftime("%d.%m.%Y")
        st.dataframe(disp_g, use_container_width=True, hide_index=True)

if st.button("Çıkış"):
    st.session_state.logged_in_user = None; st.rerun()
