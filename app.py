import streamlit as st
import pandas as pd

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard PT. Gelatik Supra",
    page_icon="🦅",
    layout="wide"
)

# Judul Dashboard
st.title("🦅 Dashboard Proyek - PT. Gelatik Supra")
st.markdown("Menampilkan ringkasan data personil dan proyek per **13 November 2026**.")

# Fungsi untuk memuat dan memfilter data khusus PT. Gelatik Supra
@st.cache_data
def load_data():
    df = pd.read_csv("Summary Database Nasional 13 November 2026.csv", encoding="latin1")
    if 'NAMA PERUSAHAAN' in df.columns:
        df = df[df['NAMA PERUSAHAAN'] == 'PT. GELATIK SUPRA']
    df = df.dropna(subset=['Nama'])
    return df

# Indikator loading
with st.spinner('Sedang memuat data PT. Gelatik Supra...'):
    df = load_data()

st.success(f"Berhasil memuat {len(df)} data personil PT. Gelatik Supra! ✅")

# --- SIDEBAR: FILTER DATA ---
st.sidebar.header("🔍 Filter Data")

if 'Nama Project' in df.columns:
    selected_project = st.sidebar.selectbox(
        "Pilih Nama Project",
        options=["Semua Project"] + list(df['Nama Project'].dropna().unique())
    )
    if selected_project != "Semua Project":
        df = df[df['Nama Project'] == selected_project]

if 'Area CBS' in df.columns:
    selected_area = st.sidebar.selectbox(
        "Pilih Area CBS",
        options=["Semua Area"] + list(df['Area CBS'].dropna().unique())
    )
    if selected_area != "Semua Area":
        df = df[df['Area CBS'] == selected_area]

if 'Jenis Kelamin' in df.columns:
    selected_gender = st.sidebar.selectbox(
        "Pilih Jenis Kelamin",
        options=["Semua"] + list(df['Jenis Kelamin'].dropna().unique())
    )
    if selected_gender != "Semua":
        df = df[df['Jenis Kelamin'] == selected_gender]

# --- METRIK UTAMA (KPI) ---
st.markdown("---")
col1, col2, col3 = st.columns3(3) if hasattr(st, 'columns3') else st.columns(3)
with col1:
    st.metric("Total Personil", len(df))
with col2:
    if 'Nama Project' in df.columns:
        st.metric("Total Jenis Project", df['Nama Project'].nunique())
with col3:
    if 'Area CBS' in df.columns:
        st.metric("Total Area CBS", df['Area CBS'].nunique())

# --- TABEL DATA UTAMA ---
st.markdown("### 📋 Tabel Data Personil PT. Gelatik Supra")
search_name = st.text_input("Cari berdasarkan Nama Karyawan/Personil:")

filtered_df = df.copy()
if search_name:
    # Memecah kata pencarian agar mendukung pencarian multi-kata (misal: "Rika" atau "Siti")
    keywords = search_name.strip().split()
    for kw in keywords:
        filtered_df = filtered_df[filtered_df['Nama'].str.contains(kw, case=False, na=False)]

st.dataframe(filtered_df, use_container_width=True)

# --- VISUALISASI GRAFIK ---
st.markdown("---")
st.markdown("### 📈 Grafik Analisis")

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    if 'Nama Project' in df.columns:
        st.subheader("Distribusi Berdasarkan Project")
        project_counts = df['Nama Project'].value_counts().head(10)
        st.bar_chart(project_counts)

with col_chart2:
    if 'Pendidikan Terakhir' in df.columns:
        st.subheader("Distribusi Pendidikan Terakhir")
        edu_counts = df['Pendidikan Terakhir'].value_counts()
        st.bar_chart(edu_counts)
