import streamlit as st
import pandas as pd
from github import Github
import io
import urllib.parse

st.set_page_config(
    page_title="Dashboard & Editor PT. Gelatik Supra",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 Dashboard & Editor Data - PT. Gelatik Supra")
st.markdown("Kelola, cari, dan edit data personil. Perubahan akan **langsung tersimpan secara permanen ke file CSV di GitHub**.")

REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

encoded_path = urllib.parse.quote(FILE_PATH)
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}"

@st.cache_data(ttl=10)
def load_data_from_github():
    df = pd.read_csv(RAW_URL, encoding="latin1")
    return df

try:
    if 'df_data' not in st.session_state:
        with st.spinner("Mengambil database terbaru dari GitHub..."):
            st.session_state.df_data = load_data_from_github()
except Exception as e:
    st.error(f"Gagal memuat data. Detail Error: {e}")
    st.stop()

df = st.session_state.df_data

# Otomatis deteksi kolom nama (mencari kolom yang mengandung kata 'nama' tapi bukan 'perusahaan')
nama_col = next((col for col in df.columns if 'nama' in str(col).lower() and 'perusahaan' not in str(col).lower()), None)
if not nama_col:
    nama_col = df.columns[1] # fallback ke kolom kedua jika tidak ketemu

if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.cache_data.clear()
    if 'df_data' in st.session_state:
        del st.session_state['df_data']
    st.rerun()

st.subheader("🔎 Cari Karyawan untuk Dilihat / Diedit")
search_query = st.text_input("Ketik Kata Kunci Nama (Contoh: Rika atau Rukoyah):")

if search_query:
    query_clean = search_query.strip()
    mask = df[nama_col].astype(str).str.contains(query_clean, case=False, na=False)
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning(f"Data dengan kata kunci '{search_query}' tidak ditemukan di kolom `{nama_col}`.")
        with st.expander("Lihat daftar kolom dan beberapa baris data pertama"):
            st.write("Kolom yang tersedia:", list(df.columns))
            st.dataframe(df[[nama_col]].head(10), use_container_width=True)
            
    elif len(hasil_cari) == 1:
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]

        st.success(f"Ditemukan tepat satu data untuk: **{person[nama_col]}**")

        with st.form("form_edit_karyawan"):
            st.markdown("### ✏️ Form Edit Informasi Karyawan")
            
            # Membuat input form secara dinamis untuk semua kolom baris tersebut
            edited_values = {}
            cols = st.columns(2)
            
            # Ambil semua kolom yang ada di CSV untuk diedit
            for i, col_name in enumerate(df.columns):
                with cols[i % 2]:
                    edited_values[col_name] = st.text_input(str(col_name), value=str(person.get(col_name, '')))

            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub")
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke file CSV di GitHub..."):
                    try:
                        # Update data di session state
                        for col_name, val in edited_values.items():
                            st.session_state.df_data.loc[idx_row, col_name] = val

                        # Simpan ke GitHub via PyGithub
                        g = Github(st.secrets["GITHUB_TOKEN"])
                        repo = g.get_repo(REPO_NAME)
                        file_content = repo.get_contents(FILE_PATH)
                        
                        updated_csv_bytes = st.session_state.df_data.to_csv(index=False, encoding="latin1").encode("latin1")
                        repo.update_file(
                            path=FILE_PATH,
                            message=f"Update data karyawan: {person[nama_col]}",
                            content=updated_csv_bytes,
                            sha=file_content.sha
                        )
                        
                        st.cache_data.clear()
                        del st.session_state['df_data']
                        st.success(f"✅ Perubahan berhasil disimpan permanen ke file CSV GitHub!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke GitHub: {e}")
    else:
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang mirip. Silakan ketik nama lebih spesifik:")
        st.dataframe(hasil_cari, use_container_width=True)
else:
    st.info("💡 Ketik nama karyawan pada kotak pencarian di atas untuk mulai melihat dan mengedit informasinya.")
    with st.expander("Lihat Seluruh Tabel Database"):
        st.dataframe(df, use_container_width=True)
