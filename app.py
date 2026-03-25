import streamlit as st
from streamlit_gsheets import GSheetsConnection
import json

st.set_page_config(page_title="Koz Apartmanı", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# --- BAĞLANTI ---
try:
    # Secrets içindeki tüm JSON metnini tek seferde okuyoruz
    service_account_info = json.loads(st.secrets["gsheets"]["service_account_json"])
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Verileri çek (Sheet isimleri: Gelirler, Giderler)
    df_gelir = conn.read(worksheet="Gelirler", ttl=0)
    
    st.success("✅ Bağlantı Başarılı!")
    st.balloons()
    st.dataframe(df_gelir, use_container_width=True)
    
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
