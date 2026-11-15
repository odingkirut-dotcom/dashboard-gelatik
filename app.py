import streamlit as st
import pandas as pd
from github import Github
import io
import urllib.parse

# Konfigurasi Halaman Web
st.set_page_config(
    page_title="Dashboard & Editor PT. Gelatik Supra",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 Dashboard & Editor Data - PT. Gelatik Supra")
st.markdown("Kelola, cari, dan edit data personil. Perubahan akan **langsung tersimpan secara permanen ke file CSV di GitHub**.")

# --- PENGATURAN GITHUB ---
REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

encoded_path = urllib.parse.quote(FILE_PATH)
RAW_URL = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}"

# Fungsi membaca data langsung via URL mentah
@st.cache_data(ttl=10)
def load_data_from_github():
    df = pd.read_csv(RAW_URL, encoding="latin1")
    
    # Filter fleksibel untuk PT. Gelatik Supra (mengabaikan spasi/huruf besar-kecil)
    if 'NAMA PERUSAHAAN' in df.columns:
        df['NAMA PERUSAHAAN_clean'] = df['NAMA PERUSAHAAN'].astype(str).str.upper().str.replace(".", "").str.strip()
        df_gelatik = df[df['NAMA PERUSAHAAN_clean'].str.contains("GELATIK SUPRA", na=False)].copy()
    else:
        df_gelatik = df.copy()
        
    df_gelatik = df_gelatik.dropna(subset=['Nama'])
    if 'NoKTP' in df_gelatik.columns:
        df_gelatik['NoKTP'] = df_gelatik['NoKTP'].apply(lambda x: f"{int(x)}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x))
    if 'Handphone' in df_gelatik.columns:
        df_gelatik['Handphone'] = df_gelatik['Handphone'].astype(str)
        
    return df_gelatik

# Fungsi khusus untuk menyimpan perubahan permanen ke GitHub
def save_data_to_github(df_updated_gelatik, commit_message):
    g = Github(st.secrets["GITHUB_TOKEN"])
    repo = g.get_repo(REPO_NAME)
    
    file_content = repo.get_contents(FILE_PATH)
    df_full = pd.read_csv(io.BytesIO(file_content.decoded_content), encoding="latin1")
    
    # Hapus kolom helper sementara jika ada
    if 'NAMA PERUSAHAAN_clean' in df_updated_gelatik.columns:
        df_updated_gelatik = df_updated_gelatik.drop(columns=['NAMA PERUSAHAAN_clean'])
        
    df_full.update(df_updated_gelatik)
    updated_csv_bytes = df_full.to_csv(index=False, encoding="latin1").encode("latin1")
    
    repo.update_file(
        path=FILE_PATH,
        message=commit_message,
        content=updated_csv_bytes,
        sha=file_content.sha
    )

# Memuat data ke Session State
try:
    if 'df_data' not in st.session_state:
        with st.spinner("Mengambil database terbaru dari GitHub..."):
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

# --- PENCARIAN & FORM EDIT SPESIFIK ---
st.subheader("🔎 Cari Karyawan untuk Dilihat / Diedit")
search_query = st.text_input("Ketik Nama Lengkap atau ID Personil (Contoh: RIKA atau bagian dari nama):")

if search_query:
    # Pencarian fleksibel: cukup ketik sebagian nama (misal "RIKA" atau "RUKOYAH")
    mask = (
        df['Nama'].str.contains(search_query.strip(), case=False, na=False) |
        df['ID Personil'].astype(str).str.contains(search_query.strip(), case=False, na=False)
    )
    hasil_cari = df[mask]

    if len(hasil_cari) == 0:
        st.warning("Data tidak ditemukan. Coba ketik nama depannya saja (misal: 'Rika' atau 'Siti').")
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
        st.info(f"Ditemukan **{len(hasil_cari)} data**. Silakan pilih atau ketik nama lebih spesifik dari daftar di bawah:")
        st.dataframe(hasil_cari[['ID Personil', 'Nama', 'Nama Project', 'Area CBS', 'Handphone']], use_container_width=True)
else:
    st.info("💡 Ketik nama karyawan (cukup nama depannya saja jika ragu) atau ID personil pada kotak pencarian di atas.")
    with st.expander("Lihat Seluruh Tabel Data PT. Gelatik Supra"):
        st.dataframe(df.drop(columns=['NAMA PERUSAHAAN_clean'], errors='ignore'), use_container_width=True)
