import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. TASARIM VE AYARLAR ---
st.set_page_config(page_title="Koz Yönetim Pro", layout="centered")

st.markdown("""
    <style>
        .stApp { background-color: #0D1117; color: #C9D1D9; }
        .main-card {
            background: #161B22; border: 1px solid #30363D;
            padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px;
        }
        .stat-val { font-size: 32px; font-weight: 800; color: #58A6FF; }
        .data-row { 
            background: #0D1117; border: 1px solid #30363D; padding: 10px; 
            border-radius: 8px; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center;
        }
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

@st.cache_data(ttl=30) # 30 saniye cache (Daha hızlı tepki için düşürüldü)
def verileri_yukle():
    try:
        df_gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how="all")
        df_gider = conn.read(worksheet="Giderler", ttl=0).dropna(how="all")
        
        def temizle(df, cols):
            df.columns = [str(c).strip().lower() for c in df.columns]
            mapping = {"tarih": "Tarih", "ay": "Ay", "daire": "Daire", "tür": "Tür", "tur": "Tür", "miktar": "Miktar", "tutar": "Miktar"}
            df = df.rename(columns=mapping)
            df["Miktar"] = pd.to_numeric(df["Miktar"], errors='coerce').fillna(0)
            for c in cols:
                if c not in df.columns: df[c] = ""
            return df[cols]

        return temizle(df_gelir, ["Tarih", "Ay", "Daire", "Tür", "Miktar"]), \
               temizle(df_gider, ["Tarih", "Ay", "Tür", "Miktar"])
    except:
        return None, None

def guvenli_kaydet(ws_name, updated_df):
    try:
        conn.update(worksheet=ws_name, data=updated_df)
        st.cache_data.clear()
        st.toast("İşlem Excel'e Yazıldı!", icon="📝")
        time.sleep(1)
        return True
    except:
        st.error("Bağlantı Hatası! Lütfen bekleyip tekrar deneyin.")
        return False

# --- 3. GİRİŞ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align:center;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    u = st.text_input("Yönetici")
    p = st.text_input("Şifre", type="password")
    if st.button("Giriş"):
        if u == "fatihyaman" and p == "200915":
            st.session_state.logged_in_user = "admin"; st.rerun()
        elif u != "" and len(p) == 6:
            st.session_state.logged_in_user = "user"; st.rerun()
        else: st.error("Hatalı Giriş!")
    st.stop()

gelir_df, gider_df = verileri_yukle()
if gelir_df is None:
    st.info("🔄 Veriler yükleniyor...")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. DASHBOARD ---
kasa = gelir_df["Miktar"].sum() - gider_df["Miktar"].sum()
st.markdown(f'<div class="main-card"><small style="color:#8B949E">NET KASA BAKİYESİ</small><div class="stat-val">{kasa:,.2f} TL</div></div>', unsafe_allow_html=True)

menu = st.columns(3)
if menu[0].button("🏠 Özet"): st.session_state.page = "Özet"
if menu[1].button("💸 İşlem"): st.session_state.page = "İşlem"
if menu[2].button("📊 Rapor"): st.session_state.page = "Rapor"

# --- 5. SAYFA MANTIKLARI ---
if st.session_state.page == "Özet":
    ay_simdi = aylar[datetime.now().month-1]
    st.subheader(f"📍 {ay_simdi} Ayı Tahsilat Durumu")
    yapanlar = gelir_df[(gelir_df["Ay"] == ay_simdi) & (gelir_df["Tür"] == "Aidat")]["Daire"].tolist()
    for d in DAIRE_LISTESI:
        icon = "✅" if d in yapanlar else "❌"
        st.write(f"{icon} {d}")

elif st.session_state.page == "İşlem":
    if is_admin:
        sec_ay = st.selectbox("Seçili Ay", aylar, index=datetime.now().month-1)
        tip = st.radio("İşlem Tipi", ["Gelir Tahsilatı", "Gider Ödemesi"], horizontal=True)
        
        # --- FORM ALANI ---
        with st.form("islem_ekran_form", clear_on_submit=True):
            if tip == "Gelir Tahsilatı":
                d_sec = st.multiselect("Daireler", DAIRE_LISTESI)
                turler = ["Aidat", "Ek Ödeme"]
                if sec_ay == "Ocak": turler.append("Asansör Revizyon")
                t_tur = st.selectbox("Tür", turler)
                t_mik = st.number_input("Tutar", value=400)
                if st.form_submit_button("SİSTEME İŞLE"):
                    zaten = gelir_df[(gelir_df["Ay"] == sec_ay) & (gelir_df["Tür"] == t_tur)]["Daire"].tolist()
                    temiz = [d for d in d_sec if d not in zaten]
                    if temiz:
                        yeni = [{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Daire": d, "Tür": t_tur, "Miktar": t_mik} for d in temiz]
                        if guvenli_kaydet("Gelirler", pd.concat([gelir_df, pd.DataFrame(yeni)], ignore_index=True)): st.rerun()
                    else: st.warning("Seçilen daireler zaten ödeme yapmış!")
            else:
                acik = st.text_input("Gider Açıklaması")
                mik = st.number_input("Tutar", 0)
                if st.form_submit_button("GİDERİ İŞLE"):
                    if acik:
                        yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Tür": acik, "Miktar": mik}])
                        if guvenli_kaydet("Giderler", pd.concat([gider_df, yeni_g], ignore_index=True)): st.rerun()

        # --- ANINDA GÖRÜNTÜLEME VE SİLME (İşlem Sayfasında) ---
        st.divider()
        st.subheader(f"🔍 {sec_ay} Ayı Kayıtları (Düzenle/Sil)")
        
        tab_gelir, tab_gider = st.tabs(["Gelirler", "Giderler"])
        with tab_gelir:
            ay_gelir = gelir_df[gelir_df["Ay"] == sec_ay]
            for i, r in ay_gelir.iterrows():
                col1, col2 = st.columns([0.85, 0.15])
                col1.markdown(f"<div class='data-row'><div><b>{r['Daire']}</b><br><small>{r['Tür']}</small></div><div style='color:#3FB950'>{r['Miktar']} TL</div></div>", unsafe_allow_html=True)
                if col2.button("🗑️", key=f"g_del_{i}"):
                    if guvenli_kaydet("Gelirler", gelir_df.drop(i)): st.rerun()
        
        with tab_gider:
            ay_gider = gider_df[gider_df["Ay"] == sec_ay]
            for i, r in ay_gider.iterrows():
                col1, col2 = st.columns([0.85, 0.15])
                col1.markdown(f"<div class='data-row'><div><b>{r['Tür']}</b><br><small>{r['Tarih']}</small></div><div style='color:#F85149'>-{r['Miktar']} TL</div></div>", unsafe_allow_html=True)
                if col2.button("🗑️", key=f"gid_del_{i}"):
                    if guvenli_kaydet("Giderler", gider_df.drop(i)): st.rerun()
    else: st.error("İşlem yetkiniz bulunmuyor.")

elif st.session_state.page == "Rapor":
    # RAPOR SAYFASINDA SİLME BUTONU YOK - SADECE İZLEME
    r_ay = st.selectbox("Rapor Ayı", ["Tümü"] + aylar)
    st.info("💡 Kayıt silme işlemleri sadece 'İşlem' sayfasından yapılabilir.")
    
    t1, t2 = st.tabs(["Gelir Listesi", "Gider Listesi"])
    with t1:
        data = gelir_df if r_ay == "Tümü" else gelir_df[gelir_df["Ay"] == r_ay]
        st.dataframe(data, use_container_width=True, hide_index=True)
    with t2:
        data_g = gider_df if r_ay == "Tümü" else gider_df[gider_df["Ay"] == r_ay]
        st.dataframe(data_g, use_container_width=True, hide_index=True)

if st.button("🚪 Çıkış"):
    st.session_state.logged_in_user = None; st.rerun()
