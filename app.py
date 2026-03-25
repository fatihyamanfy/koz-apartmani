import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. AYARLAR VE YETKİLENDİRME ---
st.set_page_config(page_title="Koz Apartmanı 2026", layout="wide")

# Kullanıcı veritabanı simülasyonu (Gerçek sistemde DB'ye bağlanır)
if "users" not in st.session_state:
    st.session_state.users = {"fatihyaman": "200915"} # Yönetici hesabı

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# --- 2. DAİRE VE AY VERİLERİ ---
DAIRE_LISTESI = [
    "EMEL ERKABAKTEPE-1", "AYŞE EVRENDİLEK-2", "FATİH YAMAN-3", "İSMAİL BOZTEPE-4",
    "FEHMİ KOÇ-5", "MURAT ALTINIŞIK-6", "ARİF BİÇER-7", "ŞERİFE-8"
]
aylar = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", 
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]

# Veri saklama
if "kasa_gelir" not in st.session_state:
    st.session_state.kasa_gelir = pd.DataFrame(columns=["Ay", "Daire", "Tür", "Miktar"])
if "kasa_gider" not in st.session_state:
    st.session_state.kasa_gider = pd.DataFrame(columns=["Ay", "Tür", "Miktar"])

# --- 3. GİRİŞ VE KAYIT SİSTEMİ ---
if st.session_state.logged_in_user is None:
    st.title("🔐 Koz Apartmanı Yönetim Sistemi")
    giris_tab, kayit_tab = st.tabs(["Giriş Yap", "Kayıt Ol"])
    
    with giris_tab:
        u_name = st.text_input("Kullanıcı Adı")
        u_pass = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            if u_name in st.session_state.users and st.session_state.users[u_name] == u_pass:
                st.session_state.logged_in_user = u_name
                st.rerun()
            else:
                st.error("Hatalı kullanıcı adı veya şifre!")

    with kayit_tab:
        new_u = st.text_input("Yeni Kullanıcı Adı")
        new_p = st.text_input("Yeni Şifre (Sadece 6 Haneli Rakam)", max_chars=6)
        if st.button("Kayıt Ol"):
            if len(new_p) == 6 and new_p.isdigit():
                st.session_state.users[new_u] = new_p
                st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
            else:
                st.warning("Şifre tam olarak 6 haneli rakam olmalıdır!")
    st.stop()

# --- 4. YETKİ KONTROLÜ ---
is_admin = (st.session_state.logged_in_user == "fatihyaman")

# --- 5. GÖRSEL TASARIM ---
st.markdown("""
    <style>
    .month-card { padding: 10px; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin: 2px; font-size: 12px;}
    .bg-green { background-color: #28a745; }
    .bg-red { background-color: #dc3545; opacity: 0.6; }
    .bakiye-container { background-color: #1E3A8A; color: white; padding: 20px; border-radius: 15px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- 6. YILLIK DURUM PANOSU (YEŞİL / KIRMIZI AYLAR) ---
st.write(f"Hoş geldiniz, **{st.session_state.logged_in_user}** " + ("(Yönetici)" if is_admin else "(İzleyici)"))
if st.button("Güvenli Çıkış"):
    st.session_state.logged_in_user = None
    st.rerun()

st.subheader("🗓️ 2026 Yılı Tahsilat Durumu")
cols = st.columns(12)
for idx, ay in enumerate(aylar):
    # Ayın ödemesi tamamlandı mı kontrolü (Örn: 8 dairenin hepsi 400+ ödedi mi?)
    aylik_toplam = st.session_state.kasa_gelir[st.session_state.kasa_gelir["Ay"] == ay]["Miktar"].sum()
    odeme_tamam = aylik_toplam >= (len(DAIRE_LISTESI) * 400)
    status_class = "bg-green" if odeme_tamam else "bg-red"
    cols[idx].markdown(f'<div class="month-card {status_class}">{ay}</div>', unsafe_allow_html=True)

# Kasa Özeti
t_gelir = st.session_state.kasa_gelir["Miktar"].sum()
t_gider = st.session_state.kasa_gider["Miktar"].sum()
st.markdown(f'<div class="bakiye-container"><h3>GÜNCEL KASA BAKİYESİ: {t_gelir - t_gider:,.2f} TL</h3></div>', unsafe_allow_html=True)

# --- 7. ANA PANEL ---
secilen_ay = st.selectbox("İncelemek istediğiniz ayı seçin:", aylar, index=datetime.now().month-1)

t1, t2 = st.tabs(["💰 GELİRLER", "💸 GİDERLER"])

with t1:
    if is_admin:
        with st.expander("➕ Yeni Gelir Ekle"):
            g_daire = st.selectbox("Daire", DAIRE_LISTESI)
            turler = ["Aidat", "Yıllık Asansör Bakımı"] if secilen_ay == "Ocak" else ["Aidat"]
            g_tur = st.radio("Tür", turler, horizontal=True)
            g_miktar = st.number_input("Tutar", value=400 if g_tur == "Aidat" else 0)
            if st.button("Kaydet"):
                yeni = pd.DataFrame([{"Ay": secilen_ay, "Daire": g_daire, "Tür": g_tur, "Miktar": g_miktar}])
                st.session_state.kasa_gelir = pd.concat([st.session_state.kasa_gelir, yeni], ignore_index=True)
                st.rerun()
    
    st.dataframe(st.session_state.kasa_gelir[st.session_state.kasa_gelir["Ay"] == secilen_ay], use_container_width=True, hide_index=True)

with t2:
    if is_admin:
        with st.expander("➕ Yeni Gider Ekle"):
            gd_tur = st.text_input("Gider Açıklaması")
            gd_miktar = st.number_input("Tutar (TL)", min_value=0)
            if st.button("Gideri Kaydet"):
                yeni_g = pd.DataFrame([{"Ay": secilen_ay, "Tür": gd_tur, "Miktar": gd_miktar}])
                st.session_state.kasa_gider = pd.concat([st.session_state.kasa_gider, yeni_g], ignore_index=True)
                st.rerun()
                
    st.dataframe(st.session_state.kasa_gider[st.session_state.kasa_gider["Ay"] == secilen_ay], use_container_width=True, hide_index=True)
