import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json

st.set_page_config(page_title="Koz Apartmanı", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# --- BAĞLANTI AYARI ---
try:
    # Secrets içindeki JSON metnini sözlüğe çeviriyoruz
    creds_dict = json.loads(st.secrets["gsheets"]["service_account_json"])
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Verileri oku
    df_gelir = conn.read(worksheet="Gelirler", ttl=0, spreadsheet=st.secrets["gsheets"]["spreadsheet"])
    df_gider = conn.read(worksheet="Giderler", ttl=0, spreadsheet=st.secrets["gsheets"]["spreadsheet"])
    
    st.success("✅ Bağlantı kuruldu!")
    st.balloons()
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.stop()

# Tablo gösterimi (Örnek)
st.write("### Mevcut Gelir Kayıtları")
st.dataframe(df_gelir, use_container_width=True)
