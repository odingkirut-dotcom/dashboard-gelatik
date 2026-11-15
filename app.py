import streamlit as st
import pandas as pd

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Database Nasional",
    page_icon="📊",
    layout="wide"
)

# Judul Dashboard
st.title("📊 Sistem Pencarian Database Nasional")
st.markdown("Data Nasional per **13 November 2026**.")

# Fungsi untuk memuat data
@st.cache_data
def load_data():
    df = pd.read_csv("Summary Database Nasional 13 November 2026.csv", encoding="latin1")
    df = df.dropna(subset=['Nama'])
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

# --- PENCARIAN CERDAS ---
st.subheader("🔎 Cari Data Karyawan")
search_query = st.text_input("Ketik Nama atau ID Personil (Contoh: 'Siti' untuk tabel, atau nama lengkap untuk form):")

if search_query:
    mask = (
        df['Nama'].str.contains(search_query.strip(), case=False, na=False) |
        df['ID Personil'].astype(str).str.contains(search_query.strip(), case=False, na=False)
    )
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning("Data tidak ditemukan. Coba periksa kembali ejaan nama.")
    
    # KONDISI 1: Jika hasil pencarian HANYA 1 ORANG -> Tampilkan Form Identitas
    elif len(hasil_cari) == 1:
        person = hasil_cari.iloc[0]

        def val(col_name):
            v = person.get(col_name, "-")
            return "-" if pd.isna(v) or str(v).strip() == "" else str(v)

        st.success(f"Ditemukan 1 data spesifik untuk: **{val('Nama')}**")

        with st.container(border=True):
            st.markdown(f"### 👤 {val('Nama')}")
            st.caption(f"**ID Personil:** {val('ID Personil')}  |  **Perusahaan:** {val('NAMA PERUSAHAAN')}  |  **Masa Kerja:** {val('MASA KERJA')}")
            st.markdown("---")

            tab1, tab2, tab3 = st.tabs(["📋 Data Pribadi & Alamat", "💼 Data Pekerjaan & Project", "📑 Kontrak, Rekening & BPJS"])

            with tab1:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**No. KTP:** `{val('NoKTP')}`")
                    st.markdown(f"**Tempat, Tanggal Lahir:** {val('Tempat lahir')}, {val('Tanggal Lahir')}")
                    st.markdown(f"**Jenis Kelamin:** {val('Jenis Kelamin')}")
                    st.markdown(f"**Agama:** {val('Agama')}")
                    st.markdown(f"**Status Perkawinan:** {val('Status Perkawinan')}")
                with c2:
                    st.markdown(f"**Pendidikan Terakhir:** {val('Pendidikan Terakhir')}")
                    st.markdown(f"**No. Handphone:** {val('Handphone')}")
                    st.markdown(f"**Alamat Email:** {val('Alamat Email')}")
                    st.markdown(f"**Nama Ibu Kandung:** {val('Nama Ibu Kandung')}")
                    st.markdown(f"**Alamat KTP:** {val('Alamat')} RT {val('RT')}/RW {val('RW')}, Kel. {val('kelurahan')}, Kec. {val('kecamatan')}, {val('kotamadya')}, {val('propinsi')} ({val('Kode Pos')})")

            with tab2:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Perusahaan:** {val('NAMA PERUSAHAAN')}")
                    st.markdown(f"**Nama Client:** {val('Nama Client')}")
                    st.markdown(f"**Nama Project:** {val('Nama Project')}")
                    st.markdown(f"**Posisi:** {val('Posisi')}")
                with c2:
                    st.markdown(f"**Area CBS / Sub Area:** {val('Area CBS')} / {val('Sub Area')}")
                    st.markdown(f"**Area Coverage:** {val('Area Coverage')}")
                    st.markdown(f"**Outlet:** {val('Outlet')}")
                    st.markdown(f"**Nama Team Leader (TL):** {val('Nama TL')}")

            with tab3:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Tanggal Bergabung:** {val('Tanggal Bergabung')}")
                    st.markdown(f"**Tanggal Kontrak:** {val('Tanggal Kontrak')}")
                    st.markdown(f"**Berakhir Kontrak:** {val('Tanggal Berakhir Kontrak')}")
                    st.markdown(f"**Tanggal Keluar & Alasan:** {val('Tanggal Keluar')} ({val('Alasan Keluar')})")
                with c2:
                    st.markdown(f"**No. Rekening:** `{val('No Rekening')}`")
                    st.markdown(f"**Nama di Rekening:** {val('Nama Pada Nomer Rekening')}")
                    st.markdown(f"**No. NPWP:** `{val('No NPWP')}`")
                    st.markdown(f"**No. Jamsostek / BPJS:** {val('No Jamsostek')} / {val('No BPJS Kesehatan')}")

    # KONDISI 2: Jika hasil pencarian BANYAK ORANG (seperti mengetik "Siti") -> Tampilkan Tabel
    else:
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang cocok dengan kata kunci **'{search_query}'**. Ditampilkan dalam bentuk tabel:")
        st.dataframe(hasil_cari, use_container_width=True)

else:
    st.info("💡 Silakan ketik nama pada kotak pencarian di atas. Jika mengetik nama umum (misal: **'Siti'**), akan muncul tabel daftar nama. Jika mengetik nama lengkap, akan muncul form identitas spesifik.")
    with st.expander("Lihat Seluruh Tabel Database (Klik untuk membuka)"):
        st.dataframe(df, use_container_width=True)
