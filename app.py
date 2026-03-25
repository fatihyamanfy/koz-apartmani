import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Koz Apartmanı", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# --- DOĞRUDAN BAĞLANTI ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Verileri oku (Sheet isimleri: Gelirler, Giderler)
    df_gelir = conn.read(worksheet="Gelirler", ttl=0)
    
    st.success("✅ Tebrikler! Sistem Başarıyla Bağlandı.")
    st.balloons()
    
    st.write("### Mevcut Kayıtlar")
    st.dataframe(df_gelir, use_container_width=True)
    
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.info("Secrets kutusundaki tırnak işaretlerini kontrol edin.")
