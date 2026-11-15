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

# Memuat seluruh database mentah tanpa filter perusahaan agar data pasti ada
@st.cache_data(ttl=10)
def load_data_from_github():
    df = pd.read_csv(RAW_URL, encoding="latin1")
    df = df.dropna(subset=['Nama'])
    if 'NoKTP' in df.columns:
        df['NoKTP'] = df['NoKTP'].apply(lambda x: f"{int(x)}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
    if 'Handphone' in df.columns:
        df['Handphone'] = df['Handphone'].astype(str)
    return df

def save_data_to_github(df_updated, commit_message):
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(REPO_NAME)
    
    file_content = repo.get_contents(FILE_PATH)
    df_full = pd.read_csv(io.BytesIO(file_content.decoded_content), encoding="latin1")
    
    df_full.update(df_updated)
    updated_csv_bytes = df_full.to_csv(index=False, encoding="latin1").encode("latin1")
    
    repo.update_file(
        path=FILE_PATH,
        message=commit_message,
        content=updated_csv_bytes,
        sha=file_content.sha
    )

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

st.subheader("🔎 Cari Karyawan untuk Dilihat / Diedit")
search_query = st.text_input("Ketik Kata Kunci Nama (Contoh: Rika atau Rukoyah):")

if search_query:
    query_clean = search_query.strip()
    mask = (
        df['Nama'].astype(str).str.contains(query_clean, case=False, na=False) |
        df['ID Personil'].astype(str).str.contains(query_clean, case=False, na=False)
    )
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning("Data tidak ditemukan di database.")
    elif len(hasil_cari) == 1:
        # Tepat 1 data ditemukan -> Munculkan form edit lengkap
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]

        st.success(f"Ditemukan tepat satu data untuk: **{person['Nama']}** (ID: {person.get('ID Personil', '-')}) - Perusahaan: **{person.get('NAMA PERUSAHAAN', '-')}**")

        with st.form("form_edit_karyawan"):
            st.markdown("### ✏️ Form Edit Informasi Karyawan")
            c1, c2 = st.columns(2)
            with c1:
                new_nama = st.text_input("Nama Lengkap", value=str(person.get('Nama', '')))
                new_hp = st.text_input("No. Handphone", value=str(person.get('Handphone', '')))
                new_email = st.text_input("Alamat Email", value=str(person.get('Alamat Email', '')))
                new_pendidikan = st.text_input("Pendidikan Terakhir", value=str(person.get('Pendidikan Terakhir', '')))
                new_status_kawin = st.text_input("Status Perkawinan", value=str(person.get('Status Perkawinan', '')))
            with c2:
                new_project = st.text_input("Nama Project", value=str(person.get('Nama Project', '')))
                new_posisi = st.text_input("Posisi", value=str(person.get('Posisi', '')))
                new_area = st.text_input("Area CBS", value=str(person.get('Area CBS', '')))
                new_sub_area = st.text_input("Sub Area", value=str(person.get('Sub Area', '')))
                new_tl = st.text_input("Nama Team Leader (TL)", value=str(person.get('Nama TL', '')))

            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub")
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke file CSV di GitHub..."):
                    try:
                        st.session_state.df_data.loc[idx_row, 'Nama'] = new_nama
                        st.session_state.df_data.loc[idx_row, 'Handphone'] = new_hp
                        st.session_state.df_data.loc[idx_row, 'Alamat Email'] = new_email
                        st.session_state.df_data.loc[idx_row, 'Pendidikan Terakhir'] = new_pendidikan
                        st.session_state.df_data.loc[idx_row, 'Status Perkawinan'] = new_status_kawin
                        st.session_state.df_data.loc[idx_row, 'Nama Project'] = new_project
                        st.session_state.df_data.loc[idx_row, 'Posisi'] = new_posisi
                        st.session_state.df_data.loc[idx_row, 'Area CBS'] = new_area
                        st.session_state.df_data.loc[idx_row, 'Sub Area'] = new_sub_area
                        st.session_state.df_data.loc[idx_row, 'Nama TL'] = new_tl

                        save_data_to_github(
                            st.session_state.df_data,
                            f"Update data karyawan: {new_nama}"
                        )
                        
                        st.cache_data.clear()
                        del st.session_state['df_data']
                        st.success(f"✅ Perubahan untuk **{new_nama}** berhasil disimpan permanen ke file CSV GitHub!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke GitHub: {e}")
    else:
        # Banyak data ditemukan -> Hanya tampilkan tabel ringkasan saja sesuai permintaan
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang mirip. Silakan ketik nama lebih spesifik:")
        cols_to_show = [c for c in ['ID Personil', 'Nama', 'NAMA PERUSAHAAN', 'Nama Project', 'Area CBS', 'Handphone'] if c in df.columns]
        st.dataframe(hasil_cari[cols_to_show], use_container_width=True)
else:
    st.info("💡 Ketik nama karyawan pada kotak pencarian di atas untuk mulai melihat dan mengedit informasinya.")
    with st.expander("Lihat Seluruh Tabel Database"):
        st.dataframe(df, use_container_width=True)
