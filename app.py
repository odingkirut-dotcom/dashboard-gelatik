import streamlit as st
import pandas as pd

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Database Nasional",
    page_icon="🪪",
    layout="wide"
)

# Judul Dashboard
st.title("🪪 Sistem Pencarian & Form Identitas Karyawan")
st.markdown("Data Nasional per **13 November 2026**.")

# Fungsi untuk memuat data
@st.cache_data
def load_data():
    df = pd.read_csv("Summary Database Nasional 13 November 2026.csv", encoding="latin1")
    df = df.dropna(subset=['Nama'])
    # Rapikan format NoKTP dan Handphone agar tidak berantakan
    if 'NoKTP' in df.columns:
        df['NoKTP'] = df['NoKTP'].apply(lambda x: f"{int(x)}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
    return df

df = load_data()

# --- SIDEBAR: FILTER DATA ---
st.sidebar.header("🔍 Filter Data")

if 'NAMA PERUSAHAAN' in df.columns:
    selected_company = st.sidebar.selectbox(
        "Pilih Perusahaan",
        options=["Semua Perusahaan"] + list(df['NAMA PERUSAHAAN'].dropna().unique())
    )
    if selected_company != "Semua Perusahaan":
        df = df[df['NAMA PERUSAHAAN'] == selected_company]

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

# --- METRIK UTAMA ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Personil", len(df))
if 'NAMA PERUSAHAAN' in df.columns:
    col2.metric("Total Perusahaan", df['NAMA PERUSAHAAN'].nunique())
if 'Area CBS' in df.columns:
    col3.metric("Total Area CBS", df['Area CBS'].nunique())

st.markdown("---")

# --- PENCARIAN & FORM IDENTITAS ---
st.subheader("🔎 Cari & Lihat Form Identitas")

search_query = st.text_input("Ketik Nama atau ID Personil (contoh: RIKA SITI RUKOYAH):")

if search_query:
    # Cari kecocokan berdasarkan Nama atau ID Personil
    mask = (
        df['Nama'].str.contains(search_query.strip(), case=False, na=False) |
        df['ID Personil'].astype(str).str.contains(search_query.strip(), case=False, na=False)
    )
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning("Data tidak ditemukan. Coba periksa kembali ejaan nama.")
    else:
        # Jika hasil lebih dari 1, beri dropdown agar user bisa pilih satu orang spesifik
        if len(hasil_cari) > 1:
            st.info(f"Ditemukan {len(hasil_cari)} data yang mirip. Silakan pilih satu orang di bawah ini:")
            pilihan_orang = hasil_cari['ID Personil'].astype(str) + " - " + hasil_cari['Nama'] + " (" + hasil_cari['Nama Project'].fillna('-') + ")"
            selected_label = st.selectbox("Pilih Personil:", pilihan_orang)
            selected_id = selected_label.split(" - ")[0]
            person = hasil_cari[hasil_cari['ID Personil'].astype(str) == selected_id].iloc[0]
        else:
            person = hasil_cari.iloc[0]

        # Fungsi pembantu untuk menampilkan nilai dengan rapi
        def val(col_name):
            v = person.get(col_name, "-")
            return "-" if pd.isna(v) or str(v).strip() == "" else str(v)

        # --- TAMPILAN KARTU FORM IDENTITAS ---
        with st.container(border=True):
            st.markdown(f"### 👤 {val('Nama')}")
            st.caption(f"**ID Personil:** {val('ID Personil')}  |  **Perusahaan:** {val('NAMA PERUSAHAAN')}  |  **Masa Kerja:** {val('MASA KERJA')}")
            st.markdown("---")

            tab1, tab2, tab3 = st.tabs(["📋 Data Pribadi & Alamat", "💼 Data Pekerjaan & Project", "📑 Kontrak, Rekening & BPJS"])

            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    st.text
