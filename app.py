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

if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.cache_data.clear()
    if 'df_data' in st.session_state:
        del st.session_state['df_data']
    st.rerun()

st.subheader("🔎 Cari Karyawan di Seluruh Kolom Database")
search_query = st.text_input("Ketik Kata Kunci (Contoh: RUKOYAH atau ID-JK0158):")

if search_query:
    query_clean = search_query.strip()
    
    # Mencari kata kunci di SEMUA kolom DataFrame secara sekaligus
    mask = df.astype(str).apply(lambda row: row.str.contains(query_clean, case=False, na=False)).any(axis=1)
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning(f"Data dengan kata kunci '{search_query}' tidak ditemukan sama sekali di database.")
    elif len(hasil_cari) == 1:
        # Tepat 1 baris ditemukan -> Munculkan form edit lengkap
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]

        st.success(f"Ditemukan tepat satu data pada Baris/Index ke-{idx_row}!")

        with st.form("form_edit_karyawan"):
            st.markdown("### ✏️ Form Edit Informasi Karyawan")
            st.caption("Ubah data di bawah ini sesuai kebutuhan, lalu klik tombol Simpan.")
            
            edited_values = {}
            cols = st.columns(2)
            
            # Membuat input form untuk semua kolom baris tersebut
            for i, col_name in enumerate(df.columns):
                with cols[i % 2]:
                    edited_values[col_name] = st.text_input(str(col_name), value=str(person.get(col_name, '')))

            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub")
            
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
                            message=f"Update data baris {idx_row}",
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
        # Jika ada banyak baris yang cocok, tampilkan tabel ringkasan saja sesuai permintaan
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang mirip. Silakan ketik kata kunci lebih spesifik:")
        st.dataframe(hasil_cari, use_container_width=True)
else:
    st.info("💡 Ketik nama atau ID personil pada kotak pencarian di atas untuk melihat detail dan mengedit informasinya.")
    with st.expander("Lihat Seluruh Tabel Database"):
        st.dataframe(df, use_container_width=True)
