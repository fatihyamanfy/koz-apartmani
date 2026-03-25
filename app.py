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
        /* Mobil buton düzenlemeleri */
        .stButton>button { width: 100%; border-radius: 8px; height: 45px; }
    </style>
""", unsafe_allow_html=True)

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "page" not in st.session_state:
    st.session_state.page = "Özet"

DAIRE_LISTESI = ["EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4", "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. VERİ YÖNETİMİ ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=20) # Mobil hız için cache süresi dengelendi
def verileri_yukle():
    try:
        df_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all")
        df_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all")
        
        def temizle(df, cols):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "daire": "Daire", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            # Tarih kolonunu gerçek tarih formatına çevir (Sıralama için kritik)
            df["Tarih"] = pd.to_datetime(df["Tarih"], dayfirst=True, errors='coerce')
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            return df[cols]

        g_clean = temizle(df_gelir, ["Tarih", "Ay", "Daire", "Tür", "Miktar"])
        gid_clean = temizle(df_gider, ["Tarih", "Ay", "Tür", "Miktar"])
        
        # KRONOLOJİK SIRALAMA (Eskiden Yeniye)
        return g_clean.sort_values(by="Tarih", ascending=True), \
               gid_clean.sort_values(by="Tarih", ascending=True)
    except:
        return None, None

def guvenli_kaydet(ws_name, updated_df):
    try:
        # Kaydederken tarihi tekrar string formatına çevir (Excel uyumu için)
        save_df = updated_df.copy()
        save_df["Tarih"] = save_df["Tarih"].dt.strftime("%d.%m.%Y")
        conn.update(worksheet=ws_name, data=save_df)
        st.cache_data.clear()
        st.toast("Kayıt Başarılı!", icon="✅")
        time.sleep(1)
        return True
    except:
        st.error("Bağlantı Hatası!")
        return False

# --- 3. GİRİŞ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h3 style='text-align:center;'>🏢 Koz Apartmanı Yönetim</h3>", unsafe_allow_html=True)
    u = st.text_input("Yönetici")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş Yap"):
        if u == "fatihyaman" and p == "200915":
            st.session_state.logged_in_user = "admin"; st.rerun()
        elif u != "" and len(p) == 6:
            st.session_state.logged_in_user = "user"; st.rerun()
        else: st.error("Hatalı Giriş!")
    st.stop()

gelir_df, gider_df = verileri_yukle()
if gelir_df is None:
    st.info("Veriler yükleniyor...")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. DASHBOARD ---
kasa = gelir_df["Miktar"].sum() - gider_df["Miktar"].sum()
st.markdown(f'<div class="main-card"><small>GÜNCEL BAKİYE</small><div class="stat-val">{kasa:,.2f} TL</div></div>', unsafe_allow_html=True)

menu = st.columns(3)
if menu[0].button("🏠 Özet"): st.session_state.page = "Özet"
if menu[1].button("💸 İşlem"): st.session_state.page = "İşlem"
if menu[2].button("📊 Rapor"): st.session_state.page = "Rapor"

# --- 5. SAYFALAR ---
if st.session_state.page == "Özet":
    ay_simdi = aylar[datetime.now().month-1]
    st.subheader(f"📍 {ay_simdi} Tahsilat Durumu")
    yapanlar = gelir_df[(gelir_df["Ay"] == ay_simdi) & (gelir_df["Tür"] == "Aidat")]["Daire"].tolist()
    for d in DAIRE_LISTESI:
        icon = "✅" if d in yapanlar else "❌"
        st.write(f"{icon} {d}")

elif st.session_state.page == "İşlem":
    if is_admin:
        sec_ay = st.selectbox("Seçili Ay", aylar, index=datetime.now().month-1)
        tip = st.radio("Tür", ["Gelir", "Gider"], horizontal=True)
        
        with st.form("mobil_islem_form", clear_on_submit=True):
            # TARİH SEÇME SEKİMESİ (Yeni eklendi)
            islem_tarihi = st.date_input("İşlem Tarihi", datetime.now())
            
            if tip == "Gelir":
                d_sec = st.multiselect("Daireler", DAIRE_LISTESI)
                turler = ["Aidat", "Ek Ödeme"]
                if sec_ay == "Ocak": turler.append("Asansör Revizyon")
                t_tur = st.selectbox("Kalem", turler)
                t_mik = st.number_input("Tutar", value=400)
                if st.form_submit_button("KAYDET"):
                    zaten = gelir_df[(gelir_df["Ay"] == sec_ay) & (gelir_df["Tür"] == t_tur)]["Daire"].tolist()
                    temiz = [d for d in d_sec if d not in zaten]
                    if temiz:
                        yeni = [{"Tarih": pd.to_datetime(islem_tarihi), "Ay": sec_ay, "Daire": d, "Tür": t_tur, "Miktar": t_mik} for d in temiz]
                        if guvenli_kaydet("Gelirler", pd.concat([gelir_df, pd.DataFrame(yeni)], ignore_index=True)): st.rerun()
                    else: st.warning("Zaten kayıtlı!")
            else:
                acik = st.text_input("Gider Açıklaması")
                mik = st.number_input("Tutar", 0)
                if st.form_submit_button("GİDERİ KAYDET"):
                    if acik:
                        yeni_g = pd.DataFrame([{"Tarih": pd.to_datetime(islem_tarihi), "Ay": sec_ay, "Tür": acik, "Miktar": mik}])
                        if guvenli_kaydet("Giderler", pd.concat([gider_df, yeni_g], ignore_index=True)): st.rerun()

        # ANLIK GÖSTERİM VE SİLME (İlgili Ay)
        st.divider()
        st.subheader(f"🔍 {sec_ay} Kayıtları")
        t_gelir, t_gider = st.tabs(["Gelir", "Gider"])
        with t_gelir:
            view_g = gelir_df[gelir_df["Ay"] == sec_ay]
            for i, r in view_g.iterrows():
                c1, c2 = st.columns([0.8, 0.2])
                c1.markdown(f"<div class='data-row'><div>{r['Daire']}<br><small>{r['Tarih'].strftime('%d.%m')}</small></div><b>{r['Miktar']}</b></div>", unsafe_allow_html=True)
                if c2.button("🗑️", key=f"delg_{i}"):
                    if guvenli_kaydet("Gelirler", gelir_df.drop(i)): st.rerun()
        with t_gider:
            view_gid = gider_df[gider_df["Ay"] == sec_ay]
            for i, r in view_gid.iterrows():
                c1, c2 = st.columns([0.8, 0.2])
                c1.markdown(f"<div class='data-row'><div>{r['Tür']}<br><small>{r['Tarih'].strftime('%d.%m')}</small></div><b>{r['Miktar']}</b></div>", unsafe_allow_html=True)
                if c2.button("🗑️", key=f"delgid_{i}"):
                    if guvenli_kaydet("Giderler", gider_df.drop(i)): st.rerun()
    else: st.error("Yetkisiz Giriş")

elif st.session_state.page == "Rapor":
    r_ay = st.selectbox("Rapor Filtresi", ["Tümü"] + aylar)
    st.info("Kayıtlar kronolojik (eskiden yeniye) sıralanmıştır.")
    
    tab1, tab2 = st.tabs(["Gelir Listesi", "Gider Listesi"])
    with tab1:
        data = gelir_df if r_ay == "Tümü" else gelir_df[gelir_df["Ay"] == r_ay]
        # Excel'de güzel görünmesi için tarihi formatlayıp göster
        disp_data = data.copy()
        disp_data["Tarih"] = disp_data["Tarih"].dt.strftime("%d.%m.%Y")
        st.dataframe(disp_data, use_container_width=True, hide_index=True)
    with tab2:
        data_g = gider_df if r_ay == "Tümü" else gider_df[gider_df["Ay"] == r_ay]
        disp_data_g = data_g.copy()
        disp_data_g["Tarih"] = disp_data_g["Tarih"].dt.strftime("%d.%m.%Y")
        st.dataframe(disp_data_g, use_container_width=True, hide_index=True)

if st.button("Çıkış"):
    st.session_state.logged_in_user = None; st.rerun()
