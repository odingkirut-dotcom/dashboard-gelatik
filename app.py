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

st.title("🦅 Dashboard & Editor Data - Database Nasional (Semua Perusahaan)")
st.markdown("Kelola, cari, dan edit data personil untuk **semua perusahaan (termasuk BTB, Gelatik Supra, dll)**. Perubahan akan langsung tersimpan secara permanen ke file CSV di GitHub.")

# --- PENGATURAN GITHUB ---
REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

encoded_path = urllib.parse.quote(FILE_PATH)
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}"

# Memuat SELURUH database nasional tanpa filter perusahaan apa pun
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

# Tombol muat ulang data terbaru
if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.cache_data.clear()
    if 'df_data' in st.session_state:
        del st.session_state['df_data']
    st.rerun()

# --- PENCARIAN & KONDISI TAMPILAN EDIT (SELURUH PERUSAHAAN) ---
st.subheader("🔎 Cari Karyawan di Seluruh Perusahaan / Database")
search_query = st.text_input("Ketik Nama Lengkap, Bagian Nama, atau ID Personil (Contoh: RIKA SITI RUKOYAH atau BTB):")

if search_query:
    query_clean = search_query.strip()
    
    # Pencarian fleksibel di seluruh kolom DataFrame
    mask = df.astype(str).apply(lambda row: row.str.contains(query_clean, case=False, na=False)).any(axis=1)
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning("Data tidak ditemukan di database nasional. Periksa kembali ejaan kata kunci.")
    
    elif len(hasil_cari) == 1:
        # KONDISI 1: Tepat satu data ditemukan -> Munculkan form edit lengkap
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]

        # Coba ambil info nama & perusahaan untuk ditampilkan di header sukses
        nama_val = person.get('Nama', person.get(df.columns[1], ''))
        perusahaan_val = person.get('NAMA PERUSAHAAN', 'Tidak diketahui')

        st.success(f"Ditemukan tepat satu data untuk: **{nama_val}** (Perusahaan: **{perusahaan_val}**)")

        with st.form("form_edit_karyawan"):
            st.markdown("### ✏️ Form Edit Informasi Karyawan")
            st.caption("Ubah data di bawah ini sesuai kebutuhan, lalu klik tombol Simpan.")

            edited_values = {}
            cols = st.columns(2)
            
            # Menampilkan seluruh kolom dari baris tersebut agar bisa diedit
            for i, col_name in enumerate(df.columns):
                with cols[i % 2]:
                    edited_values[col_name] = st.text_input(str(col_name), value=str(person.get(col_name, '')))

            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub")
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke file CSV di GitHub..."):
                    try:
                        # Update data di session state lokal
                        for col_name, val in edited_values.items():
                            st.session_state.df_data.loc[idx_row, col_name] = val

                        # Simpan permanen ke GitHub via PyGithub
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
        # KONDISI 2: Banyak data ditemukan -> Hanya tampilkan tabel ringkasan saja
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang mirip. Silakan ketik nama lebih spesifik agar form edit muncul:")
        st.dataframe(hasil_cari, use_container_width=True)
else:
    st.info("💡 Ketik nama karyawan atau kata kunci pada kotak pencarian di atas untuk mulai mencari dari seluruh perusahaan.")
    with st.expander("Lihat Seluruh Tabel Database Nasional"):
        st.dataframe(df, use_container_width=True)
