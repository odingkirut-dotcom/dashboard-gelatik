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

# Otomatis deteksi kolom nama dan ID personil secara presisi
nama_col = next((col for col in df.columns if 'nama' in str(col).lower() and 'perusahaan' not in str(col).lower()), df.columns[1])
id_col = next((col for col in df.columns if 'id' in str(col).lower() or 'personil' in str(col).lower()), df.columns[0])

# Tombol muat ulang data terbaru
if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.cache_data.clear()
    if 'df_data' in st.session_state:
        del st.session_state['df_data']
    st.rerun()

# --- PENCARIAN PRESISI (HANYA PADA KOLOM NAMA & ID) ---
st.subheader("🔎 Cari Karyawan Berdasarkan Nama / ID")
search_query = st.text_input("Ketik Nama Lengkap, Bagian Nama, atau ID (Contoh: RUKOYAH atau ID-JK0158):")

if search_query:
    query_clean = search_query.strip()
    
    # Pencarian HANYA difokuskan pada kolom Nama dan ID Personil agar tidak nyasar
    mask = (
        df[nama_col].astype(str).str.contains(query_clean, case=False, na=False) |
        df[id_col].astype(str).str.contains(query_clean, case=False, na=False)
    )
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning(f"Data dengan kata kunci '{search_query}' tidak ditemukan pada kolom Nama atau ID.")
    
    elif len(hasil_cari) == 1:
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]

        nama_val = person.get(nama_col, 'Karyawan')
        perusahaan_val = person.get('NAMA PERUSAHAAN', 'Tidak diketahui')

        st.success(f"Ditemukan tepat satu data untuk: **{nama_val}** (Perusahaan: **{perusahaan_val}**)")

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
                    if any(k in col_lower for k in ['nama', 'id', 'nik', 'ktp', 'project', 'posisi', 'area', 'sub', 'tl', 'perusahaan']):
                        with (c1 if i % 2 == 0 else c2):
                            edited_values[col] = st.text_input(str(col), value=str(person.get(col, '')))

            with tab2:
                st.markdown("##### Informasi Alamat & Lokasi")
                c1, c2 = st.columns(2)
                for i, col in enumerate(col_names):
                    col_lower = col.lower()
                    if any(k in col_lower for k in ['alamat', 'rt', 'rw', 'kelurahan', 'kecamatan', 'kotamadya', 'propinsi', 'pos', 'domisili']):
                        with (c1 if i % 2 == 0 else c2):
                            edited_values[col] = st.text_input(str(col), value=str(person.get(col, '')))

            with tab3:
                st.markdown("##### Informasi Pribadi & Kontak Lainnya")
                c1, c2 = st.columns(2)
                assigned_cols = list(edited_values.keys())
                remaining_cols = [c for c in col_names if c not in assigned_cols]
                
                for i, col in enumerate(remaining_cols):
                    with (c1 if i % 2 == 0 else c2):
                        edited_values[col] = st.text_input(str(col), value=str(person.get(col, '')))

            st.markdown("---")
            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub", use_container_width=True)
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke file CSV di GitHub..."):
                    try:
                        for col_name, val in edited_values.items():
                            st.session_state.df_data.loc[idx_row, col_name] = val

                        g = Github(st.secrets["GITHUB_TOKEN"])
                        repo = g.get_repo(REPO_NAME)
                        file_content = repo.get_contents(FILE_PATH)
                        
                        updated_csv_bytes = st.session_state.df_data.to_csv(index=False, encoding="latin1").encode("latin1")
                        repo.update_file(
                            path=FILE_PATH,
                            message=f"Update data nasional baris {idx_row}",
                            content=updated_csv_bytes,
                            sha=file_content.sha
                        )
                        
                        st.cache_data.clear()
                        del st.session_state['df_data']
                        st.success("✅ Perubahan berhasil disimpan permanen ke file CSV GitHub!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke GitHub: {e}")
    
    else:
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang mirip. Silakan ketik nama lebih spesifik agar form edit muncul:")
        st.dataframe(hasil_cari[[id_col, nama_col, 'NAMA PERUSAHAAN', 'Nama Project'] if 'Nama Project' in df.columns else [id_col, nama_col]], use_container_width=True)
else:
    st.info("💡 Ketik nama karyawan atau ID pada kotak pencarian di atas untuk mulai mencari.")
    with st.expander("Lihat Seluruh Tabel Database Nasional"):
        st.dataframe(df, use_container_width=True)
