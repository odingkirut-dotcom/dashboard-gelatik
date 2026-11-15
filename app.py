import streamlit as st
import pandas as pd
from github import Github
import io
import urllib.parse

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard & Editor Database Nasional",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 Dashboard & Editor Data - Database Nasional")
st.markdown("Kelola, cari, dan edit data personil dengan tampilan terorganisir. Perubahan tersimpan **permanen ke GitHub**.")

# --- PENGATURAN GITHUB ---
REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

encoded_path = urllib.parse.quote(FILE_PATH)
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}"

# Memuat SELURUH database nasional
@st.cache_data(ttl=10)
def load_data_from_github():
    df = pd.read_csv(RAW_URL, encoding="latin1")
    return df

try:
    if 'df_data' not in st.session_state:
        with st.spinner("Mengambil database nasional terbaru dari GitHub..."):
            st.session_state.df_data = load_data_from_github()
except Exception as e:
    st.error(f"Gagal memuat data. Detail Error: {e}")
    st.stop()

df = st.session_state.df_data

# Tombol muat ulang data terbaru
if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.cache_data.clear()
    if 'df_data' in st.session_state:
        del st.session_state['df_data']
    st.rerun()

# --- METODE GANDA: PENCARIAN TEKS ATAU PILIH LANGSUNG DARI DROPDOWN ---
st.subheader("🔎 Cari Karyawan (Pencarian Teks / Pilih Langsung)")

col_s1, col_s2 = st.columns(2)

with col_s1:
    search_query = st.text_input("Ketik Nama / ID (Contoh: RUKOYAH):")

with col_s2:
    # Opsi alternatif: Pilih langsung dari daftar (mengambil gabungan kolom teks utama)
    # Mencari kolom yang berisi teks nama
    text_cols = [c for c in df.columns if df[c].dtype == 'object']
    sample_col = text_cols[1] if len(text_cols) > 1 else text_cols[0]
    
    # Ambil list unik untuk dropdown (diurutkan)
    all_names = sorted([str(x) for x in df[sample_col].dropna().unique() if str(x).strip() != ''])
    selected_dropdown = st.selectbox("Atau Pilih Langsung dari Daftar:", options=["-- Pilih Karyawan --"] + all_names)

# Menentukan baris yang dipilih berdasarkan input teks atau dropdown
hasil_cari = pd.DataFrame()
idx_row = None

if search_query:
    keywords = search_query.strip().split()
    mask = pd.Series(True, index=df.index)
    df_str = df.astype(str)
    for kw in keywords:
        kw_mask = df_str.apply(lambda row: row.str.contains(kw, case=False, na=False)).any(axis=1)
        mask = mask & kw_mask
    hasil_cari = df[mask]
elif selected_dropdown != "-- Pilih Karyawan --":
    hasil_cari = df[df[sample_col].astype(str) == selected_dropdown]

# Logika Tampilan Form Edit jika data ditemukan / dipilih
if not hasil_cari.empty:
    if len(hasil_cari) == 1:
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]
        perusahaan_val = person.get('NAMA PERUSAHAAN', 'Tidak diketahui')

        st.success(f"✅ Data dipilih/ditemukan! (Perusahaan: **{perusahaan_val}** | Baris Index: {idx_row})")

        # Formulir Edit dengan Tampilan Tab Modern & Kompak
        with st.form("form_edit_karyawan_modern"):
            st.markdown("### ✏️ Form Edit Informasi Karyawan")
            st.caption("Ubah data melalui tab di bawah ini, lalu klik tombol Simpan di bagian bawah.")

            tab1, tab2, tab3 = st.tabs(["👤 Informasi Utama & Pekerjaan", "🏠 Alamat & Domisili", "📋 Data Lainnya"])
            
            edited_values = {}
            col_names = list(df.columns)
            
            with tab1:
                st.markdown("##### Atribut Utama & Pekerjaan")
                c1, c2 = st.columns(2)
                for i, col in enumerate(col_names):
                    col_lower = col.lower()
                    if
