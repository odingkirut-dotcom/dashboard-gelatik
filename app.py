import streamlit as st
import pandas as pd
import requests
import base64
import io
import urllib.parse
import time

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

# Memuat data terbaru langsung dari REST API GitHub (bypass raw cache)
def load_data_from_github():
    api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}?t={time.time()}"
    headers = {
        "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
        "Accept": "application/vnd.github+json",
        "Cache-Control": "no-cache"
    }
    resp = requests.get(api_url, headers=headers)
    if resp.status_code == 200:
        file_data = resp.json()
        download_url = file_data.get("download_url")
        resp_dl = requests.get(f"{download_url}&t={time.time()}")
        file_decoded = resp_dl.content.decode("latin1")
        return pd.read_csv(io.StringIO(file_decoded), encoding="latin1")
    else:
        raw_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}?t={time.time()}"
        return pd.read_csv(raw_url, encoding="latin1")

try:
    with st.spinner("Mengambil database nasional terbaru dari GitHub..."):
        df_master = load_data_from_github()
except Exception as e:
    st.error(f"Gagal memuat data. Detail Error: {e}")
    st.stop()

# Inisialisasi version counter untuk mereset widget form secara total
if 'form_version' not in st.session_state:
    st.session_state.form_version = 0

# Tombol muat ulang data terbaru
if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    st.cache_data.clear()
    if 'selected_id' in st.session_state:
        del st.session_state['selected_id']
    st.session_state.form_version += 1
    st.rerun()

# --- PENCARIAN TEKS EKSKLUSIF (KOLOM NAMA & ID DENGAN AMAN) ---
st.subheader("🔎 Cari Karyawan Berdasarkan Nama / ID")
search_query = st.text_input("Ketik Nama Lengkap, Bagian Nama, atau ID (Contoh: RIKA SITI RUKOYAH):", key="input_search_query")

# Deteksi kolom nama dan ID secara aman
cols_list = list(df_master.columns)
nama_col = next((col for col in cols_list if 'nama' in str(col).lower() and 'perusahaan' not in str(col).lower() and 'ibu' not in str(col).lower()), cols_list[1] if len(cols_list) > 1 else cols_list[0])
id_col = next((col for col in cols_list if 'id' in str(col).lower() or 'personil' in str(col).lower()), cols_list[0])

# Reset pilihan jika kotak pencarian dikosongkan
if not search_query:
    if 'selected_id' in st.session_state:
        del st.session_state['selected_id']

hasil_cari = pd.DataFrame()

if search_query:
    keywords = search_query.strip().split()
    mask = pd.Series(True, index=df_master.index)
    target_cols = [str(nama_col), str(id_col)]
    
    for kw in keywords:
        kw_mask = df_master[target_cols].astype(str).apply(lambda row: row.str.contains(kw, case=False, na=False)).any(axis=1)
        mask = mask & kw_mask
        
    hasil_cari = df_master[mask]

# Logika Penanganan Hasil Pencarian
if not hasil_cari.empty:
    if len(hasil_cari) == 1:
        target_row_idx = hasil_cari.index[0]
        person = df_master.loc[target_row_idx]
        curr_id = str(person.get(id_col, '-'))
        st.session_state['selected_id'] = curr_id
    else:
        st.warning(f"Ditemukan **{len(hasil_cari)} data** yang cocok dengan kata kunci **'{search_query}'**. Ketik nama lebih lengkap atau spesifik agar langsung menuju form edit:")
        st.dataframe(hasil_cari[[id_col, nama_col, 'NAMA PERUSAHAAN'] if 'NAMA PERUSAHAAN' in df_master.columns else [id_col, nama_col]], use_container_width=True)
        if 'selected_id' in st.session_state:
            del st.session_state['selected_id']
else:
    if search_query:
        st.warning("Data tidak ditemukan. Periksa kembali ejaan nama atau ID.")
    if 'selected_id' in st.session_state:
        del st.session_state['selected_id']

# Tampilkan Form Edit jika ada ID tunggal yang aktif dipilih
if 'selected_id' in st.session_state:
    active_id = st.session_state['selected_id']
    
    try:
        df_fresh = load_data_from_github()
    except:
        df_fresh = df_master

    matched_active = df_fresh[df_fresh[id_col].astype(str) == active_id]
    
    if not matched_active.empty:
        active_row_idx = matched_active.index[0]
        person = df_fresh.loc[active_row_idx]

        curr_nama = str(person.get(nama_col, '-'))
        curr_id = str(person.get(id_col, '-'))
        curr_perusahaan = str(person.get('NAMA PERUSAHAAN', '-'))

        form_key = f"form_edit_{active_id}_{st.session_state.form_version}"
        with st.form(form_key):
            st.markdown(f"### ✏️ Edit Data: **{curr_nama}**")
            st.info(f"🆔 **ID Personil:** {curr_id}  |  🏢 **Perusahaan:** {curr_perusahaan}")
            st.caption("Ubah data apa saja pada kolom di bawah ini, lalu klik tombol Simpan.")

            edited_values = {}
            valid_cols = [c for c in df_fresh.columns if not str(c).startswith('Unnamed:')]
            
            c1, c2 = st.columns(2)
            for i, col in enumerate(valid_cols):
                with (c1 if i % 2 == 0 else c2):
                    unique_key = f"fld_{active_id}_{col}_{st.session_state.form_version}"
                    val_data = person.get(col, '')
                    val_str = '' if pd.isna(val_data) else str(val_data)
                    edited_values[col] = st.text_input(str(col), value=val_str, key=unique_key)

            st.markdown("---")
            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub", use_container_width=True)
            
            if submitted:
                with st.spinner("Menyimpan perubahan langsung ke GitHub..."):
                    try:
                        api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/{FILE_PATH}"
                        headers = {
                            "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
                            "Accept": "application/vnd.github+json"
                        }
                        
                        resp_get = requests.get(api_url, headers=headers)
                        if resp_get.status_code != 200:
                            st.error(f"Gagal mengambil metadata file dari GitHub: {resp_get.text}")
                            st.stop()
                            
                        file_data = resp_get.json()
                        current_sha = file_data["sha"]
                        
                        download_url = file_data.get("download_url")
                        if download_url:
                            resp_dl = requests.get(f"{download_url}&t={time.time()}")
                            file_decoded = resp_dl.content.decode("latin1")
                        else:
                            file_content_b64 = file_data["content"]
                            file_decoded = base64.b64decode(file_content_b64).decode("latin1")
                        
                        if not file_decoded.strip():
                            st.error("File CSV di GitHub terbaca kosong.")
                            st.stop()
                            
                        df_live = pd.read_csv(io.StringIO(file_decoded), encoding="latin1")
                        
                        matched_live = df_live[df_live[id_col].astype(str) == active_id]
                        
                        if not matched_live.empty:
                            live_idx = matched_live.index[0]
                            
                            for col_name, val in edited_values.items():
                                if col_name in df_live.columns:
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

                            updated_csv_str = df_live.to_csv(index=False, encoding="latin1")
                            updated_b64 = base64.b64encode(updated_csv_str.encode("latin1")).decode("utf-8")
                            
                            payload = {
                                "message": f"Update data nasional ID {curr_id}",
                                "content": updated_b64,
                                "sha": current_sha
                            }
                            
                            resp_put = requests.put(api_url, headers=headers, json=payload)
                            if resp_put.status_code in [200, 201]:
                                st.session_state.form_version += 1
                                st.success("✅ Perubahan berhasil disimpan permanen ke file CSV GitHub!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Gagal menyimpan ke GitHub API: {resp_put.text}")
                        else:
                            st.error("Gagal mencocokkan ID personil pada data terbaru GitHub.")
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke GitHub: {e}")
else:
    if not search_query:
        st.info("💡 Ketik nama lengkap karyawan atau ID pada kotak pencarian di atas agar langsung memunculkan form edit.")
        with st.expander("Lihat Seluruh Tabel Database Nasional"):
            st.dataframe(df_master, use_container_width=True)
