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
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}?v={pd.Timestamp.now().timestamp()}"

# Memuat SELURUH database nasional tanpa cache yang mengunci data lama
def load_data_from_github():
    df = pd.read_csv(RAW_URL, encoding="latin1")
    return df

try:
    with st.spinner("Mengambil database nasional terbaru dari GitHub..."):
        df = load_data_from_github()
except Exception as e:
    st.error(f"Gagal memuat data. Detail Error: {e}")
    st.stop()

# Tombol muat ulang data terbaru
if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.rerun()

# --- PENCARIAN TEKS EKSKLUSIF (KOLOM NAMA & ID) ---
st.subheader("🔎 Cari Karyawan Berdasarkan Nama / ID")
search_query = st.text_input("Ketik Nama Lengkap, Bagian Nama, atau ID (Contoh: RIKA SITI RUKOYAH):")

# Otomatis deteksi kolom nama dan ID secara presisi
nama_col = next((col for col in df.columns if 'nama' in str(col).lower() and 'perusahaan' not in str(col).lower() and 'ibu' not in str(col).lower()), df.columns[1])
id_col = next((col for col in df.columns if 'id' in str(col).lower() or 'personil' in str(col).lower()), df.columns[0])

# Menentukan baris yang dipilih berdasarkan input teks
hasil_cari = pd.DataFrame()
idx_row = None

if search_query:
    keywords = search_query.strip().split()
    
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

        curr_nama = person.get(nama_col, '-')
        curr_id = person.get(id_col, '-')
        curr_perusahaan = person.get('NAMA PERUSAHAAN', '-')

        # Formulir Edit dengan Tampilan Seksi Rapi Berkelompok (2 Kolom)
        with st.form("form_edit_karyawan_modern"):
            st.markdown(f"### ✏️ Edit Data: **{curr_nama}**")
            st.info(f"🆔 **ID Personil:** {curr_id}  |  🏢 **Perusahaan:** {curr_perusahaan}")
            st.caption("Semua atribut karyawan tersedia di bawah ini. Ubah data apa saja lalu klik tombol Simpan.")

            edited_values = {}
            col_names = list(df.columns)
            
            sec1_cols, sec2_cols, sec3_cols = [], [], []
            for col in col_names:
                col_lower = str(col).lower()
                if any(k in col_lower for k in ['alamat', 'rt', 'rw', 'kelurahan', 'kecamatan', 'kotamadya', 'propinsi', 'pos', 'domisili']):
                    sec2_cols.append(col)
                elif any(k in col_lower for k in ['nama', 'id', 'nik', 'ktp', 'project', 'posisi', 'area', 'sub', 'tl', 'perusahaan']) and 'ibu' not in col_lower:
                    sec1_cols.append(col)
                else:
                    sec3_cols.append(col)

            # Bagian 1: Informasi Utama & Pekerjaan
            st.markdown("#### 👤 Informasi Utama & Pekerjaan")
            c1, c2 = st.columns(2)
            for i, col in enumerate(sec1_cols):
                with (c1 if i % 2 == 0 else c2):
                    unique_key = f"sec1_{i}_{col}"
                    val_data = person.get(col, '')
                    val_str = '' if pd.isna(val_data) else str(val_data)
                    edited_values[col] = st.text_input(str(col), value=val_str, key=unique_key)

            st.markdown("---")
            # Bagian 2: Informasi Alamat & Lokasi
            st.markdown("#### 🏠 Informasi Alamat & Lokasi")
            c1, c2 = st.columns(2)
            for i, col in enumerate(sec2_cols):
                with (c1 if i % 2 == 0 else c2):
                    unique_key = f"sec2_{i}_{col}"
                    val_data = person.get(col, '')
                    val_str = '' if pd.isna(val_data) else str(val_data)
                    edited_values[col] = st.text_input(str(col), value=val_str, key=unique_key)

            st.markdown("---")
            # Bagian 3: Informasi Pribadi & Kontak Lainnya
            st.markdown("#### 📋 Informasi Pribadi & Kontak Lainnya")
            c1, c2 = st.columns(2)
            for i, col in enumerate(sec3_cols):
                with (c1 if i % 2 == 0 else c2):
                    unique_key = f"sec3_{i}_{col}"
                    val_data = person.get(col, '')
                    val_str = '' if pd.isna(val_data) else str(val_str)
                    edited_values[col] = st.text_input(str(col), value=val_str, key=unique_key)

            st.markdown("---")
            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub", use_container_width=True)
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke file CSV di GitHub..."):
                    try:
                        # Ambil data terbaru langsung dari github sebelum melakukan update row
                        df_live = load_data_from_github()
                        
                        for col_name, val in edited_values.items():
                            if df_live[col_name].dtype in ['float64', 'int64']:
                                if val.strip() == '':
                                    df_live.loc[idx_row, col_name] = float('nan')
                                else:
                                    try:
                                        df_live.loc[idx_row, col_name] = float(val) if '.' in val else int(val)
                                    except:
                                        df_live.loc[idx_row, col_name] = val
                            else:
                                df_live.loc[idx_row, col_name] = val

                        g = Github(st.secrets["GITHUB_TOKEN"])
                        repo = g.get_repo(REPO_NAME)
                        file_content = repo.get_contents(FILE_PATH)
                        
                        updated_csv_bytes = df_live.to_csv(index=False, encoding="latin1").encode("latin1")
                        repo.update_file(
                            path=FILE_PATH,
                            message=f"Update data nasional baris {idx_row}",
                            content=updated_csv_bytes,
                            sha=file_content.sha
                        )
                        
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
