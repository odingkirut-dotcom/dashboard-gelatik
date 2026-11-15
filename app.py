import streamlit as st
import pandas as pd

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Database Nasional",
    page_icon="📊",
    layout="wide"
)

# Judul Dashboard
st.title("📊 Dashboard Database Nasional")
st.markdown("Menampilkan seluruh data personil per **13 November 2026**.")

# Fungsi untuk memuat data
@st.cache_data
def load_data():
    df = pd.read_csv("Summary Database Nasional 13 November 2026.csv", encoding="latin1")
    df = df.dropna(subset=['Nama'])
    return df

# Indikator loading
with st.spinner('Sedang memuat database...'):
    df = load_data()

st.success(f"Berhasil memuat {len(df)} total data personil! ✅")

# --- SIDEBAR: FILTER DATA ---
st.sidebar.header("🔍 Filter Data")

# Filter Perusahaan
if 'NAMA PERUSAHAAN' in df.columns:
    selected_company = st.sidebar.selectbox(
        "Pilih Perusahaan",
        options=["Semua Perusahaan"] + list(df['NAMA PERUSAHAAN'].dropna().unique())
    )
    if selected_company != "Semua Perusahaan":
        df = df[df['NAMA PERUSAHAAN'] == selected_company]

# Filter Nama Project
if 'Nama Project' in df.columns:
    selected_project = st.sidebar.selectbox(
        "Pilih Nama Project",
        options=["Semua Project"] + list(df['Nama Project'].dropna().unique())
    )
    if selected_project != "Semua Project":
        df = df[df['Nama Project'] == selected_project]

# Filter Area CBS
if 'Area CBS' in df.columns:
    selected_area = st.sidebar.selectbox(
        "Pilih Area CBS",
        options=["Semua Area"] + list(df['Area CBS'].dropna().unique())
    )
    if selected_area != "Semua Area":
        df = df[df['Area CBS'] == selected_area]

# --- METRIK UTAMA (KPI) ---
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Personil", len(df))
with col2:
    if 'NAMA PERUSAHAAN' in df.columns:
        st.metric("Total Perusahaan", df['NAMA PERUSAHAAN'].nunique())
with col3:
    if 'Area CBS' in df.columns:
        st.metric("Total Area CBS", df['Area CBS'].nunique())

# --- TABEL DATA UTAMA ---
st.markdown("### 📋 Tabel Data Personil")
search_name = st.text_input("Cari berdasarkan Nama Karyawan/Personil:")

filtered_df = df.copy()
if search_name:
    # Mencari string persis sesuai yang diketik (tidak di-split/dipecah kata-katanya)
    filtered_df = filtered_df[filtered_df['Nama'].str.contains(search_name.strip(), case=False, na=False)]

st.dataframe(filtered_df, use_container_width=True)

# --- VISUALISASI GRAFIK ---
st.markdown("---")
st.markdown("### 📈 Grafik Analisis")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    if 'NAMA PERUSAHAAN' in df.columns:
        st.subheader("Distribusi Perusahaan")
        comp_counts = df['NAMA PERUSAHAAN'].value_counts()
        st.bar_chart(comp_counts)

with col_chart2:
    if 'Pendidikan Terakhir' in df.columns:
        st.subheader("Distribusi Pendidikan Terakhir")
        edu_counts = df['Pendidikan Terakhir'].value_counts()
        st.bar_chart(edu_counts)
