import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import time

# --- 1. AYARLAR & TASARIM ---
st.set_page_config(page_title="Koz Yönetim Pro", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
        .stApp { background-color: #0D1117; color: #C9D1D9; }
        .main-card {
            background: #161B22; border: 1px solid #30363D;
            padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px;
        }
        .stat-val { font-size: 32px; font-weight: 800; color: #58A6FF; }
        .stButton>button { border-radius: 8px; background: #21262D; color: white; border: 1px solid #30363D; width: 100%; }
        .stButton>button:hover { border-color: #58A6FF; color: #58A6FF; }
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

@st.cache_data(ttl=60) 
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
        return None, None

def guvenli_kaydet(ws_name, updated_df):
    try:
        conn.update(worksheet=ws_name, data=updated_df)
        st.cache_data.clear()
        st.success("✅ Kayıt Excel'e İşlendi!")
        time.sleep(1)
        return True
    except Exception:
        st.error("⚠️ Bağlantı hatası. Lütfen 30 saniye sonra tekrar deneyin.")
        return False

# --- 3. GİRİŞ ---
if st.session_state.logged_in_user is None:
    st.markdown("<h2 style='text-align:center;'>🏢 Koz Apartmanı</h2>", unsafe_allow_html=True)
    u = st.text_input("Yönetici")
    p = st.text_input("Şifre", type="password")
    if st.button("Sisteme Giriş"):
        if u == "fatihyaman" and p == "200915":
            st.session_state.logged_in_user = "admin"; st.rerun()
        elif u != "" and len(p) == 6:
            st.session_state.logged_in_user = "user"; st.rerun()
        else: st.error("Giriş Başarısız!")
    st.stop()

gelir_df, gider_df = verileri_yukle()
if gelir_df is None:
    st.info("🔄 Veriler güncelleniyor...")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. DASHBOARD (EXCEL MANTIĞI) ---
toplam_gelir = gelir_df["Miktar"].sum()
toplam_gider = gider_df["Miktar"].sum()
kasa = toplam_gelir - toplam_gider

st.markdown(f"""
    <div class="main-card">
        <div style="color:#8B949E; font-size:12px; margin-bottom:5px;">GÜNCEL KASA (BAKİYE)</div>
        <div class="stat-val">{kasa:,.2f} TL</div>
        <div style="display: flex; justify-content: space-between; margin-top: 15px; border-top: 1px solid #30363D; padding-top: 10px;">
            <div style="color:#3FB950;"><b>+ {toplam_gelir:,.0f}</b><br><small>Gelir</small></div>
            <div style="color:#F85149;"><b>- {toplam_gider:,.0f}</b><br><small>Gider</small></div>
        </div>
    </div>
""", unsafe_allow_html=True)

menu = st.columns(3)
if menu[0].button("🏠 Özet"): st.session_state.page = "Özet"
if menu[1].button("💸 İşlem"): st.session_state.page = "İşlem"
if menu[2].button("📊 Rapor"): st.session_state.page = "Rapor"

# --- 5. SAYFA MANTIKLARI ---
if st.session_state.page == "Özet":
    ay_simdi = aylar[datetime.now().month-1]
    st.subheader(f"📍 {ay_simdi} Ayı Aidat Listesi")
    yapanlar = gelir_df[(gelir_df["Ay"] == ay_simdi) & (gelir_df["Tür"] == "Aidat")]["Daire"].tolist()
    borclular = [d for d in DAIRE_LISTESI if d not in yapanlar]
    
    for d in DAIRE_LISTESI:
        col1, col2 = st.columns([0.8, 0.2])
        col1.write(f"🏢 {d}")
        if d in yapanlar:
            col2.markdown("✅")
        else:
            col2.markdown("❌")
    st.divider()

elif st.session_state.page == "İşlem":
    if is_admin:
        sec_ay = st.selectbox("İşlem Yapılacak Ay", aylar, index=datetime.now().month-1)
        tip = st.radio("İşlem Türü", ["Gelir Tahsilatı", "Gider Ödemesi"], horizontal=True)
        
        with st.form("excel_islem_form"):
            if tip == "Gelir Tahsilatı":
                d_sec = st.multiselect("Daire Seçin", DAIRE_LISTESI)
                
                # --- ASANSÖR REVİZYON ŞARTI ---
                turler = ["Aidat", "Ek Ödeme"]
                if sec_ay == "Ocak":
                    turler.append("Asansör Revizyon")
                
                t_tur = st.selectbox("Tahsilat Kalemi", turler)
                t_mik = st.number_input("Birim Tutar (TL)", value=400)
                
                if st.form_submit_button("EXCEL'E KAYDET"):
                    if not d_sec:
                        st.warning("Hiçbir daire seçilmedi!")
                    else:
                        # --- MÜKERRER KONTROLÜ ---
                        zaten_kayitli = gelir_df[(gelir_df["Ay"] == sec_ay) & (gelir_df["Tür"] == t_tur)]["Daire"].tolist()
                        hatali = [d for d in d_sec if d in zaten_kayitli]
                        temiz = [d for d in d_sec if d not in zaten_kayitli]
                        
                        if hatali:
                            st.error(f"❌ {', '.join(hatali)} bu ay için zaten {t_tur} ödemesi yapmış!")
                        
                        if temiz:
                            yeni = [{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Daire": d, "Tür": t_tur, "Miktar": t_mik} for d in temiz]
                            if guvenli_kaydet("Gelirler", pd.concat([gelir_df, pd.DataFrame(yeni)], ignore_index=True)):
                                st.rerun()
            else:
                acik = st.text_input("Gider Açıklaması")
                mik = st.number_input("Tutar", 0)
                if st.form_submit_button("GİDERİ İŞLE"):
                    if acik:
                        yeni_g = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": sec_ay, "Tür": acik, "Miktar": mik}])
                        if guvenli_kaydet("Giderler", pd.concat([gider_df, yeni_g], ignore_index=True)):
                            st.rerun()
                    else: st.warning("Gider açıklaması boş olamaz!")
    else: st.error("Yetkisiz Kullanıcı!")

elif st.session_state.page == "Rapor":
    r_ay = st.selectbox("Ay Seçin", ["Tümü"] + aylar)
    t1, t2 = st.tabs(["Gelir Defteri", "Gider Defteri"])
    with t1:
        data = gelir_df if r_ay == "Tümü" else gelir_df[gelir_df["Ay"]==r_ay]
        st.dataframe(data, use_container_width=True, hide_index=True)
        if is_admin:
            secilen_sil = st.selectbox("Silinecek Kayıt (Daire)", data["Daire"].unique(), key="gelir_sil")
            if st.button("Seçili Kaydı Sil"):
                idx = data[data["Daire"] == secilen_sil].index[0]
                if guvenli_kaydet("Gelirler", gelir_df.drop(idx)): st.rerun()

    with t2:
        data_g = gider_df if r_ay == "Tümü" else gider_df[gider_df["Ay"]==r_ay]
        st.dataframe(data_g, use_container_width=True, hide_index=True)
        if is_admin:
            secilen_sil_g = st.selectbox("Silinecek Kayıt (Tür)", data_g["Tür"].unique(), key="gider_sil")
            if st.button("Seçili Gideri Sil"):
                idx_g = data_g[data_g["Tür"] == secilen_sil_g].index[0]
                if guvenli_kaydet("Giderler", gider_df.drop(idx_g)): st.rerun()

if st.button("🚪 Güvenli Çıkış"):
    st.session_state.logged_in_user = None; st.rerun()
