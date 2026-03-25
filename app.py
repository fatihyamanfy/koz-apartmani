import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. SAYFA AYARLARI VE YETKİ ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

DAIRE_LISTESI = [
    "EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4",
    "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"
]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# --- 2. VERİTABANI BAĞLANTISI (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    # Sayfaları oku (Sheet isimlerinin 'Gelirler' ve 'Giderler' olduğundan emin olun)
    df_gelir = conn.read(worksheet="Gelirler", ttl=0)
    df_gider = conn.read(worksheet="Giderler", ttl=0)
    return df_gelir.dropna(how="all"), df_gider.dropna(how="all")

try:
    df_gelir, df_gider = verileri_yukle()
except Exception as e:
    st.error(f"Veri çekme hatası: {e}")
    df_gelir = pd.DataFrame(columns=["Tarih", "Ay", "Daire", "Tür", "Miktar"])
    df_gider = pd.DataFrame(columns=["Tarih", "Ay", "Tür", "Miktar"])

# --- 3. GİRİŞ VE KAYIT SİSTEMİ ---
if st.session_state.logged_in_user is None:
    st.title("🔐 Koz Apartmanı Yönetim Sistemi")
    tab_in, tab_up = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with tab_in:
        u_name = st.text_input("Kullanıcı Adı")
        u_pass = st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir"):
            if u_name == "fatihyaman" and u_pass == "200915":
                st.session_state.logged_in_user = "admin"
                st.rerun()
            elif u_name != "" and len(u_pass) == 6 and u_pass.isdigit():
                st.session_state.logged_in_user = "user"
                st.rerun()
            else:
                st.error("Hatalı giriş! Şifre admin için '200915', üyeler için 6 haneli rakamdır.")
    
    with tab_up:
        st.info("Kayıt olanlar sadece izleme yetkisine sahip olur.")
        new_u = st.text_input("Yeni Üye Adı")
        new_p = st.text_input("6 Haneli Şifre", max_chars=6)
        if st.button("Kayıt İşlemini Tamamla"):
            if len(new_p) == 6 and new_p.isdigit():
                st.success("Kayıt başarılı! Şimdi Giriş Yap sekmesinden girebilirsiniz.")
            else:
                st.error("Şifre sadece 6 haneli rakam olmalıdır.")
    st.stop()

is_admin = (st.session_state.logged_in_user == "admin")

# --- 4. GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .bakiye-container { background-color: #1E3A8A; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .month-card { padding: 8px; border-radius: 5px; text-align: center; color: white; font-weight: bold; font-size: 11px; margin-bottom: 5px;}
    .bg-green { background-color: #28a745; }
    .bg-red { background-color: #dc3545; opacity: 0.7; }
    </style>
""", unsafe_allow_html=True)

# --- 5. ÜST PANEL VE YILLIK DURUM ---
st.write(f"Hoş geldin, **{st.session_state.logged_in_user}**" + (" (Yönetici)" if is_admin else " (İzleyici)"))
if st.button("Güvenli Çıkış"):
    st.session_state.logged_in_user = None
    st.rerun()

# Yıllık Durum Şeridi (Renkli Aylar)
cols = st.columns(12)
for idx, ay_isimi in enumerate(aylar):
    gelir_toplam = df_gelir[df_gelir["Ay"] == ay_isimi]["Miktar"].sum()
    renk = "bg-green" if gelir_toplam >= (len(DAIRE_LISTESI) * 400) else "bg-red"
    cols[idx].markdown(f'<div class="month-card {renk}">{ay_isimi}</div>', unsafe_allow_html=True)

# Kasa Özeti
t_gelir = df_gelir["Miktar"].sum()
t_gider = df_gider["Miktar"].sum()
st.markdown(f'<div class="bakiye-container"><h3>GÜNCEL KASA BAKİYESİ: {t_gelir - t_gider:,.2f} TL</h3></div>', unsafe_allow_html=True)

# --- 6. ANA SEKMELER ---
tab_aylik, tab_rapor = st.tabs(["⚙️ Aylık Yönetim", "📜 Genel Hareket Raporu"])

with tab_aylik:
    secilen_ay = st.selectbox("İşlem Yapılacak Ayı Seçin", aylar, index=datetime.now().month-1)
    
    col_gelir, col_gider = st.columns(2)
    
    with col_gelir:
        st.subheader("📥 Gelir Girişi")
        if is_admin:
            with st.expander("➕ Yeni Gelir Ekle"):
                g_daire = st.selectbox("Daire", DAIRE_LISTESI)
                tur_liste = ["Aidat", "Yıllık Asansör Bakımı"] if secilen_ay == "Ocak" else ["Aidat"]
                g_tur = st.radio("Tür", tur_liste, horizontal=True)
                g_miktar = st.number_input("Tutar (TL)", value=400 if g_tur == "Aidat" else 0)
                if st.button("Geliri Kaydet"):
                    yeni_v = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Daire": g_daire, "Tür": g_tur, "Miktar": g_miktar}])
                    updated_gelir = pd.concat([df_gelir, yeni_v], ignore_index=True)
                    conn.update(worksheet="Gelirler", data=updated_gelir)
                    st.success("Kaydedildi!"); st.rerun()
        
        # Aylık Listeleme ve Silme
        ay_g = df_gelir[df_gelir["Ay"] == secilen_ay]
        st.dataframe(ay_g[["Daire", "Tür", "Miktar"]], use_container_width=True, hide_index=False)
        if is_admin and not ay_g.empty:
            sil_id = st.number_input("Silinecek Gelir Satır No (Sol baştaki rakam):", step=1, min_value=0)
            if st.button("Seçili Geliri Sil"):
                try:
                    df_gelir = df_gelir.drop(int(sil_id))
                    conn.update(worksheet="Gelirler", data=df_gelir)
                    st.rerun()
                except: st.error("Hatalı satır numarası!")

    with col_gider:
        st.subheader("📤 Gider Girişi")
        if is_admin:
            with st.expander("➕ Yeni Gider Ekle"):
                gd_acik = st.text_input("Gider Açıklaması")
                gd_tutar = st.number_input("Gider Tutarı", min_value=0)
                if st.button("Gideri Kaydet"):
                    yeni_gid = pd.DataFrame([{"Tarih": datetime.now().strftime("%d.%m.%Y"), "Ay": secilen_ay, "Tür": gd_acik, "Miktar": gd_tutar}])
                    updated_gider = pd.concat([df_gider, yeni_gid], ignore_index=True)
                    conn.update(worksheet="Giderler", data=updated_gider)
                    st.success("Gider İşlendi!"); st.rerun()
        
        ay_gid = df_gider[df_gider["Ay"] == secilen_ay]
        st.dataframe(ay_gid[["Tür", "Miktar"]], use_container_width=True, hide_index=False)
        if is_admin and not ay_gid.empty:
            sil_id_g = st.number_input("Silinecek Gider Satır No:", step=1, min_value=0, key="sgid")
            if st.button("Seçili Gideri Sil"):
                try:
                    df_gider = df_gider.drop(int(sil_id_g))
                    conn.update(worksheet="Giderler", data=df_gider)
                    st.rerun()
                except: st.error("Hatalı satır numarası!")

with tab_rapor:
    st.subheader("🗓️ 2026 Yılı Kronolojik Rapor")
    
    # Rapor birleştirme mantığı
    r_gelir = df_gelir.copy()
    r_gelir["Hareket Tipi"] = "GELİR"
    r_gelir["Açıklama"] = r_gelir["Tür"] + " (" + r_gelir["Daire"] + ")"
    
    r_gider = df_gider.copy()
    r_gider["Hareket Tipi"] = "GİDER"
    r_gider["Açıklama"] = r_gider["Tür"]
    r_gider["Miktar"] = -r_gider["Miktar"] # Giderler eksi görünsün
    
    rapor_df = pd.concat([r_gelir[["Tarih", "Ay", "Hareket Tipi", "Açıklama", "Miktar"]], 
                          r_gider[["Tarih", "Ay", "Hareket Tipi", "Açıklama", "Miktar"]]])
    
    # En yeni işlemi en üstte göster
    st.dataframe(rapor_df.sort_index(ascending=False), use_container_width=True, hide_index=True)
