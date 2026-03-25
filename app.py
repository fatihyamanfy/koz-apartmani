import streamlit as st
import pandas as pd

st.set_page_config(page_title="Koz Apartmanı", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# Google Tablo Linkini CSV formatına çeviriyoruz (Senin tablonun ID'si ile)
SHEET_ID = "1dGtcgA4kE05OGWwn6CV-D87lbR3rmGTDpf5NsIZmYBg"
# GID 0 genellikle ilk sayfadır (Gelirler)
url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Gelirler"

try:
    # Veriyi doğrudan oku
    df = pd.read_csv(url)
    st.success("✅ Bağlantı kuruldu!")
    st.balloons()
    
    st.write("### Güncel Gelir Listesi")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Hata: {e}")
    st.info("Lütfen Google Tablo'da 'Paylaş -> Bağlantıya sahip olan herkes -> Düzenleyen' ayarının açık olduğundan emin olun.")
