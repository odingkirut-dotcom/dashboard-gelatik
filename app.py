import streamlit as st
import pandas as pd
from github import Github
import io
import urllib.parse

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Database Nasional",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 Dashboard Data - Database Nasional")
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

# Otomatis deteksi kolom nama dan ID secara presisi
nama_col = next((col for col in df.columns if 'nama' in str(col).lower() and 'perusahaan' not in str(col).lower() and 'ibu' not in str(col).lower()), df.columns[1])
id_col = next((col for col in df.columns if 'id' in str(col).lower() or 'personil' in str(col).lower()), df.columns[0])

# Tombol muat ulang data terbaru
if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.cache_data.clear()
    if 'df_data' in st.session_state:
        del st.session_state['df_data']
    st.rerun()

# --- PENCARIAN TEKS EKSKLUSIF (KOLOM NAMA & ID) ---
st.subheader("🔎 Cari Karyawan Berdasarkan Nama / ID")
search_query = st.text_input("Ketik Nama Lengkap, Bagian Nama, atau ID (Contoh: RIKA SITI RUKOYAH):")

# Menentukan baris yang dipilih berdasarkan input teks
hasil_cari = pd.DataFrame()
idx_row = None

if search_query:
    keywords = search_query.strip().split()
    
    # Pencarian HANYA difokuskan pada kolom Nama dan ID Personil
    mask = pd.Series(True, index=df.index)
    target_cols = [str(nama_col), str(id_col)]
    
    for kw in keywords:
        kw_mask = df[target_cols].astype(str).apply(lambda row: row.str.contains(kw, case=False, na=False)).any(axis=1)
        mask = mask & kw_mask
        
    hasil_cari = df[mask]

# Logika Tampilan Form Edit jika data ditemukan / dipilih
if not hasil_cari.empty:
    if len(hasil_cari) == 1:
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]
        perusahaan_val = person.get('NAMA PERUSAHAAN', 'Tidak diketahui')
        nama_val = person.get(nama_col, 'Karyawan')

        st.success(f"✅ Ditemukan: **{nama_val}** (Perusahaan: **{perusahaan_val}** | Baris Index: {idx_row})")

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
                    col_lower = str(col).lower()
                    if any(k in col_lower for k in ['nama', 'id', 'nik', 'ktp', 'project', 'posisi', 'area', 'sub', 'tl', 'perusahaan']):
                        with (c1 if i % 2 == 0 else c2):
                            unique_key = f"t1_{i}_{col}"
                            edited_values[col] = st.text_input(str(col), value=str(person.get(col, '')), key=unique_key)

            with tab2:
                st.markdown("##### Informasi Alamat & Lokasi")
                c1, c2 = st.columns(2)
                for i, col in enumerate(col_names):
                    col_lower = str(col).lower()
                    if any(k in col_lower for k in ['alamat', 'rt', 'rw', 'kelurahan', 'kecamatan', 'kotamadya', 'propinsi', 'pos', 'domisili']):
                        with (c1 if i % 2 == 0 else c2):
                            unique_key = f"t2_{i}_{col}"
                            edited_values[col] = st.text_input(str(col), value=str(person.get(col, '')), key=unique_key)

            with tab3:
                st.markdown("##### Informasi Pribadi & Kontak Lainnya")
                c1, c2 = st.columns(2)
                assigned_cols = list(edited_values.keys())
                remaining_cols = [c for c in col_names if c not in assigned_cols]
                
                for i, col in enumerate(remaining_cols):
                    with (c1 if i % 2 == 0 else c2):
                        unique_key = f"t3_{i}_{col}"
                        edited_values[col] = st.text_input(str(col), value=str(person.get(col, '')), key=unique_key)

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
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang cocok:")
        st.dataframe(hasil_cari, use_container_width=True)
else:
    if search_query:
        st.warning("Data tidak ditemukan dari pencarian nama/ID. Periksa kembali ejaan kata kunci.")
    else:
        st.info("💡 Ketik nama karyawan atau ID pada kotak pencarian di atas untuk mulai mencari.")
        with st.expander("Lihat Seluruh Tabel Database Nasional"):
            st.dataframe(df, use_container_width=True)
