import streamlit as st
import pandas as pd
from github import Github
import io
import urllib.parse

st.set_page_config(
    page_title="Debug & Editor PT. Gelatik Supra",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 Debug & Dashboard Editor - PT. Gelatik Supra")

REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

encoded_path = urllib.parse.quote(FILE_PATH)
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}"

# Load data tanpa filter dulu untuk melihat isi aslinya
@st.cache_data(ttl=10)
def load_raw_data():
    return pd.read_csv(RAW_URL, encoding="latin1")

try:
    df_raw = load_raw_data()
except Exception as e:
    st.error(f"Gagal memuat CSV: {e}")
    st.stop()

# Tampilkan informasi kolom dan perusahaan unik yang ada di CSV agar kita tahu ejaannya
with st.expander("🔍 Cek Kolom dan Daftar Perusahaan di CSV (Klik untuk Buka)"):
    st.write("Kolom yang tersedia di file CSV:", list(df_raw.columns))
    if 'NAMA PERUSAHAAN' in df_raw.columns:
        st.write("Daftar Perusahaan dalam CSV:", df_raw['NAMA PERUSAHAAN'].unique())

# Cari kolom nama (bisa jadi namanya 'Nama', 'NAMA', atau 'nama')
nama_col = next((col for col in df_raw.columns if 'nama' in col.lower() and 'perusahaan' not in col.lower()), None)

if not nama_col:
    st.error("Kolom 'Nama' tidak ditemukan di dalam CSV! Periksa nama kolom pada expander di atas.")
    st.stop()

# --- PENCARIAN BEBAS TANPA FILTER KETAT ---
st.subheader("🔎 Cari Karyawan di Seluruh Database")
search_query = st.text_input("Ketik Nama Karyawan (Contoh: RIKA atau SITI):", value="RIKA")

if search_query:
    mask = df_raw[nama_col].astype(str).str.contains(search_query.strip(), case=False, na=False)
    hasil_cari = df_raw[mask]

    if len(hasil_cari) == 0:
        st.warning(f"Nama dengan kata '{search_query}' tidak ditemukan sama sekali di file CSV.")
    else:
        st.success(f"Ditemukan **{len(hasil_cari)} data**:")
        st.dataframe(hasil_cari, use_container_width=True)

        # Jika ingin mengedit baris tertentu berdasarkan hasil pencarian
        selected_idx = st.selectbox(
            "Pilih Baris Index untuk Diedit:",
            options=hasil_cari.index.tolist(),
            format_func=lambda x: f"Index {x} - {df_raw.loc[x, nama_col]}"
        )
        
        if selected_idx is not None:
            person = df_raw.loc[selected_idx]
            st.markdown(f"### ✏️ Edit Data untuk: **{person[nama_col]}**")

            with st.form("form_edit_debug"):
                # Menampilkan beberapa kolom input umum secara dinamis
                edited_data = {}
                cols = st.columns(2)
                
                # Ambil beberapa kolom penting untuk diedit
                keys_to_edit = [c for c in df_raw.columns if c not in ['NAMA PERUSAHAAN', 'NAMA PERUSAHAAN_clean']][:10]
                
                for i, col_name in enumerate(keys_to_edit):
                    with cols[i % 2]:
                        edited_data[col_name] = st.text_input(str(col_name), value=str(person.get(col_name, '')))

                submitted = st.form_submit_button("💾 Simpan Perubahan ke GitHub")
                
                if submitted:
                    with st.spinner("Menyimpan..."):
                        try:
                            # Update data ke dataframe utama
                            for k, v in edited_data.items():
                                df_raw.loc[selected_idx, k] = v

                            # Simpan ke GitHub via PyGithub
                            g = Github(st.secrets["GITHUB_TOKEN"])
                            repo = g.get_repo(REPO_NAME)
                            file_content = repo.get_contents(FILE_PATH)
                            
                            updated_csv_bytes = df_raw.to_csv(index=False, encoding="latin1").encode("latin1")
                            repo.update_file(
                                path=FILE_PATH,
                                message=f"Update data: {person[nama_col]}",
                                content=updated_csv_bytes,
                                sha=file_content.sha
                            )
                            
                            st.cache_data.clear()
                            st.success("✅ Berhasil disimpan permanen ke GitHub!")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Gagal menyimpan: {err}")
