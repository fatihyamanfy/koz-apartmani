import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Koz Apartmanı Kasa", layout="wide")
st.title("🏢 Koz Apartmanı Yönetim Paneli")

# --- BAĞLANTI ---
try:
    # Standart Streamlit bağlantısı
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Verileri oku
    df_gelir = conn.read(worksheet="Gelirler", ttl=0)
    df_gider = conn.read(worksheet="Giderler", ttl=0)
    
    st.success("✅ Bağlantı Başarılı!")
    
    # Tabloyu göster
    st.write("### Gelir Kayıtları")
    st.dataframe(df_gelir, use_container_width=True)
    
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.info("Lütfen Secrets ayarlarını kontrol edin.")
