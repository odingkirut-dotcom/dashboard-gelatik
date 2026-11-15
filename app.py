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

# Memuat data dengan cache yang stabil
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

        st.markdown(f"### ✏️ Edit Data: **{curr_nama}**")
        st.info(f"🆔 **ID Personil:** {curr_id}  |  🏢 **Perusahaan:** {curr_perusahaan}")

        # Menggunakan selectbox untuk memilih kolom spesifik yang ingin diubah (Sangat ringan & anti-blank)
        col_names = list(df.columns)
        
        with st.form("form_edit_spesifik"):
            st.markdown("##### Pilih Atribut yang Ingin Diubah:")
            
            # Buat pilihan kolom yang sering diedit di atas, sisanya dalam pilihan lengkap
            selected_col_to_edit = st.selectbox("Pilih Kolom / Atribut:", options=col_names, index=col_names.index('Nama Ibu Kandung') if 'Nama Ibu Kandung' in col_names else 0)
            
            current_val = person.get(selected_col_to_edit, '')
            current_val_str = '' if pd.isna(current_val) else str(current_val)
            
            new_value = st.text_input(f"Nilai Baru untuk [{selected_col_to_edit}]:", value=current_val_str)
            
            st.markdown("---")
            submitted = st.form_submit_button("💾 Simpan Perubahan Ini ke GitHub", use_container_width=True)
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke GitHub..."):
                    try:
                        # Update langsung ke dataframe di session state
                        if st.session_state.df_data[selected_col_to_edit].dtype in ['float64', 'int64']:
                            if new_value.strip() == '':
                                st.session_state.df_data.loc[target_row_idx, selected_col_to_edit] = float('nan')
                            else:
                                try:
                                    st.session_state.df_data.loc[target_row_idx, selected_col_to_edit] = float(new_value) if '.' in new_value else int(new_value)
                                except:
                                    st.session_state.df_data.loc[target_row_idx, selected_col_to_edit] = new_value
                        else:
                            st.session_state.df_data.loc[target_row_idx, selected_col_to_edit] = new_value

                        # Kirim ke GitHub
                        g = Github(st.secrets["GITHUB_TOKEN"])
                        repo = g.get_repo(REPO_NAME)
                        file_content = repo.get_contents(FILE_PATH)
                        
                        updated_csv_bytes = st.session_state.df_data.to_csv(index=False, encoding="latin1").encode("latin1")
                        repo.update_file(
                            path=FILE_PATH,
                            message=f"Update {selected_col_to_edit} untuk ID {curr_id}",
                            content=updated_csv_bytes,
                            sha=file_content.sha
                        )
                        
                        st.success(f"✅ Berhasil mengubah **{selected_col_to_edit}** menjadi **{new_value}** dan tersimpan permanen di GitHub!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke GitHub: {e}")
                        
        with st.expander("👁️ Lihat Seluruh Data Lengkap Karyawan Ini"):
            st.dataframe(pd.DataFrame([person]), use_container_width=True)
            
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
