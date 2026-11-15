import streamlit as st
import pandas as pd
from github import Github
import urllib.parse

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard Database Nasional",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 Dashboard Data - Database Nasional")
st.markdown("Kelola dan edit data personil dengan cepat. Perubahan tersimpan **permanen ke GitHub**.")

# --- PENGATURAN GITHUB ---
REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

encoded_path = urllib.parse.quote(FILE_PATH)
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}"

# Memuat data terbaru langsung dari GitHub
@st.cache_data(ttl=5)
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

# --- PENCARIAN TEKS EKSKLUSIF (KOLOM NAMA & ID) ---
st.subheader("🔎 Cari Karyawan Berdasarkan Nama / ID")
search_query = st.text_input("Ketik Nama Lengkap, Bagian Nama, atau ID (Contoh: RIKA SITI RUKOYAH):")

# Otomatis deteksi kolom nama dan ID secara presisi
nama_col = next((col for col in df.columns if 'nama' in str(col).lower() and 'perusahaan' not in str(col).lower() and 'ibu' not in str(col).lower()), df.columns[1])
id_col = next((col for col in df.columns if 'id' in str(col).lower() or 'personil' in str(col).lower()), df.columns[0])

# Menentukan baris yang dipilih berdasarkan input teks
hasil_cari = pd.DataFrame()

if search_query:
    keywords = search_query.strip().split()
    mask = pd.Series(True, index=df.index)
    target_cols = [str(nama_col), str(id_col)]
    
    for kw in keywords:
        kw_mask = df[target_cols].astype(str).apply(lambda row: row.str.contains(kw, case=False, na=False)).any(axis=1)
        mask = mask & kw_mask
        
    hasil_cari = df[mask]

# Logika Tampilan Form Edit jika data ditemukan
if not hasil_cari.empty:
    if len(hasil_cari) == 1:
        target_row_idx = hasil_cari.index[0]
        person = df.loc[target_row_idx]

        curr_nama = str(person.get(nama_col, '-'))
        curr_id = str(person.get(id_col, '-'))
        curr_perusahaan = str(person.get('NAMA PERUSAHAAN', '-'))

        # Formulir Edit dengan Tampilan 2 Kolom yang Nyaman & Lengkap
        with st.form("form_edit_karyawan_lengkap"):
            st.markdown(f"### ✏️ Edit Data: **{curr_nama}**")
            st.info(f"🆔 **ID Personil:** {curr_id}  |  🏢 **Perusahaan:** {curr_perusahaan}")
            st.caption("Ubah data apa saja pada kolom di bawah ini, lalu klik tombol Simpan.")

            edited_values = {}
            col_names = list(df.columns)
            
            # Menampilkan seluruh kolom dalam layout 2 kolom yang rapi
            c1, c2 = st.columns(2)
            for i, col in enumerate(col_names):
                with (c1 if i % 2 == 0 else c2):
                    unique_key = f"field_{i}_{col}"
                    val_data = person.get(col, '')
                    val_str = '' if pd.isna(val_data) else str(val_data)
                    edited_values[col] = st.text_input(str(col), value=val_str, key=unique_key)

            st.markdown("---")
            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub", use_container_width=True)
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke GitHub..."):
                    try:
                        # Ambil DataFrame paling fresh langsung dari GitHub untuk menghindari konflik
                        df_live = load_data_from_github()
                        
                        # Cari baris yang sama persis berdasarkan ID Personil agar akurat
                        matched = df_live[df_live[id_col].astype(str) == curr_id]
                        if not matched.empty:
                            live_idx = matched.index[0]
                            
                            for col_name, val in edited_values.items():
                                if df_live[col_name].dtype in ['float64', 'int64']:
                                    if val.strip() == '':
                                        df_live.loc[live_idx, col_name] = float('nan')
                                    else:
                                        try:
                                            df_live.loc[live_idx, col_name] = float(val) if '.' in val else int(val)
                                        except:
                                            df_live.loc[live_idx, col_name] = val
                                else:
                                    df_live.loc[live_idx, col_name] = val

                            # Kirim update ke GitHub via PyGithub
                            g = Github(st.secrets["GITHUB_TOKEN"])
                            repo = g.get_repo(REPO_NAME)
                            file_content = repo.get_contents(FILE_PATH)
                            
                            updated_csv_bytes = df_live.to_csv(index=False, encoding="latin1").encode("latin1")
                            repo.update_file(
                                path=FILE_PATH,
                                message=f"Update data nasional ID {curr_id}",
                                content=updated_csv_bytes,
                                sha=file_content.sha
                            )
                            
                            # Bersihkan cache agar data langsung segar
                            st.cache_data.clear()
                            if 'df_data' in st.session_state:
                                del st.session_state['df_data']
                                
                            st.success("✅ Perubahan berhasil disimpan permanen ke file CSV GitHub!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("Gagal mencocokkan ID personil pada data terbaru GitHub.")
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
