import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Koz Apartmanı Kasa", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# --- ŞİFRESİZ DOĞRUDAN BAĞLANTI ---
try:
    # URL üzerinden doğrudan bağlantı
    url = "https://docs.google.com/spreadsheets/d/1dGtcgA4kE05OGWwn6CV-D87lbR3rmGTDpf5NsIZmYBg/edit?usp=sharing"
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Verileri oku
    df_gelir = conn.read(spreadsheet=url, worksheet="Gelirler", ttl=0)
    
    st.success("✅ Bağlantı Tamam! Koz Apartmanı Verileri Yüklendi.")
    st.balloons()
    st.dataframe(df_gelir, use_container_width=True)
    
except Exception as e:
    st.error(f"Hata: {e}")
