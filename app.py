import streamlit as st
import pandas as pd
from github import Github
import io

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard & Editor PT. Gelatik Supra",
    page_icon="🦅",
    layout="wide"
)

# --- PENGATURAN GITHUB ---
REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

st.title("🦅 Dashboard & Editor Data - PT. Gelatik Supra")
st.markdown("Kelola, cari, dan edit data personil. Perubahan akan **langsung tersimpan secara permanen ke file CSV di GitHub**.")

# 1. Fungsi membaca data langsung dari GitHub
def load_data_from_github():
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(REPO_NAME)
    file_content = repo.get_contents(FILE_PATH)
    
    # Mengubah raw bytes langsung menggunakan decode latin1 yang aman
    csv_string = file_content.decoded_content.decode("latin1")
    df = pd.read_csv(io.StringIO(csv_string), encoding="latin1")
    
    # Filter khusus PT. Gelatik Supra
    if 'NAMA PERUSAHAAN' in df.columns:
        df_gelatik = df[df['NAMA PERUSAHAAN'] == 'PT. GELATIK SUPRA'].copy()
    else:
        df_gelatik = df.copy()
        
    df_gelatik = df_gelatik.dropna(subset=['Nama'])
    if 'NoKTP' in df_gelatik.columns:
        df_gelatik['NoKTP'] = df_gelatik['NoKTP'].apply(lambda x: f"{int(x)}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
    if 'Handphone' in df_gelatik.columns:
        df_gelatik['Handphone'] = df_gelatik['Handphone'].astype(str)
        
    return df_gelatik, file_content.sha

# 2. Fungsi menyimpan perubahan permanen ke GitHub
def save_data_to_github(df_updated_gelatik, file_sha, commit_message):
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(REPO_NAME)
    
    # Ambil file CSV utuh dari GitHub agar data perusahaan lain aman
    original_file = repo.get_contents(FILE_PATH)
    df_full = pd.read_csv(io.StringIO(original_file.decoded_content.decode("latin1")), encoding="latin1")
    
    # Update data perusahaan Gelatik ke dataframe utama
    df_full.update(df_updated_gelatik)
    
    # Konversi kembali ke string CSV
    updated_csv_string = df_full.to_csv(index=False, encoding="latin1")
    
    repo.update_file(
        path=FILE_PATH,
        message=commit_message,
        content=updated_csv_string,
        sha=file_sha
    )

# Memuat data ke Session State
try:
    if 'df_data' not in st.session_state:
        with st.spinner("Mengambil database terbaru dari GitHub..."):
            df_loaded, sha_loaded = load_data_from_github()
            st.session_state.df_data = df_loaded
            st.session_state.file_sha = sha_loaded
except Exception as e:
    st.error(f"Gagal terhubung ke GitHub. Pastikan GITHUB_TOKEN sudah benar di Secrets. Error: {e}")
    st.stop()

df = st.session_state.df_data

# Tombol untuk memuat ulang data terbaru
if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    del st.session_state['df_data']
    st.rerun()

# --- PENCARIAN & FORM EDIT SPESIFIK ---
st.subheader("🔎 Cari Karyawan untuk Dilihat / Diedit")
search_query = st.text_input("Ketik Nama Lengkap atau ID Personil (Contoh: RIKA KARTIKA):")

if search_query:
    mask = (
        df['Nama'].str.contains(search_query.strip(), case=False, na=False) |
        df['ID Personil'].astype(str).str.contains(search_query.strip(), case=False, na=False)
    )
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning("Data tidak ditemukan. Periksa kembali ejaan nama.")
    elif len(hasil_cari) == 1:
        idx_row = hasil_cari.index[0]
        person = df.loc[idx_row]

        st.success(f"Ditemukan data untuk: **{person['Nama']}** (ID: {person['ID Personil']})")

        # Formulir Edit Data Karyawan
        with st.form("form_edit_karyawan"):
            st.markdown("### ✏️ Form Edit Informasi Karyawan")
            st.caption("Ubah data di bawah ini sesuai kebutuhan, lalu klik tombol Simpan.")

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
                        # Update data di session state lokal
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

                        # Simpan permanen ke GitHub
                        save_data_to_github(
                            st.session_state.df_data,
                            st.session_state.file_sha,
                            f"Update data karyawan: {new_nama}"
                        )
                        
                        # Reset cache state agar memuat data baru
                        del st.session_state['df_data']
                        st.success(f"✅ Perubahan untuk **{new_nama}** berhasil disimpan permanen ke file CSV GitHub!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke GitHub: {e}")
    else:
        st.info(f"Ditemukan **{len(hasil_cari)} data** yang mirip. Ketik nama lebih spesifik agar hanya 1 orang yang muncul untuk diedit:")
        st.dataframe(hasil_cari[['ID Personil', 'Nama', 'Nama Project', 'Area CBS', 'Handphone']], use_container_width=True)
else:
    st.info("💡 Ketik nama karyawan atau ID personil pada kotak pencarian di atas untuk mulai melihat dan mengedit informasinya.")
    with st.expander("Lihat Seluruh Tabel Data PT. Gelatik Supra"):
        st.dataframe(df, use_container_width=True)
