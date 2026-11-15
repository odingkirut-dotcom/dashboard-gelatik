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

# Memuat data langsung via Raw URL GitHub dengan anti-cache
def load_data_from_github():
    raw_url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/{encoded_path}?t={time.time()}"
    resp = requests.get(raw_url)
    
    if resp.status_code != 200:
        raw_url_fallback = f"https://raw.githubusercontent.com/{REPO_NAME}/main/Summary%20Database%20Nasional%2013%20November%202026.csv?t={time.time()}"
        resp = requests.get(raw_url_fallback)
        
    if resp.status_code == 200:
        file_decoded = resp.content.decode("latin1")
        df = pd.read_csv(io.StringIO(file_decoded), encoding="latin1", dtype=str)
        df.columns = df.columns.astype(str).str.strip()
        df = df.fillna("")
        return df
    else:
        raise Exception(f"Gagal mengunduh file dari GitHub (Status Code: {resp.status_code})")

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
    if 'selected_index' in st.session_state:
        del st.session_state['selected_index']
    st.session_state.form_version += 1
    st.rerun()

# Deteksi kolom secara aman
cols_list = list(df_master.columns)
id_col = next((col for col in cols_list if 'id' in col.lower() or 'personil' in col.lower()), cols_list[0])
nama_col = next((col for col in cols_list if 'nama' in col.lower() and 'perusahaan' not in col.lower() and 'ibu' not in col.lower()), cols_list[1] if len(cols_list) > 1 else cols_list[0])

# --- PENCARIAN SUPER EKSTRIM (MENCOCOKKAN SEMUA SEL TANPA KECUALI) ---
st.subheader("🔎 Cari Karyawan Berdasarkan Nama / ID")
search_query = st.text_input("Ketik Nama Lengkap, Bagian Nama, atau ID (Contoh: ID-JT000303):", key="input_search_query")

# Reset pilihan jika kotak pencarian dikosongkan
if not search_query:
    if 'selected_index' in st.session_state:
        del st.session_state['selected_index']

hasil_cari = pd.DataFrame()

if search_query:
    query_clean = search_query.strip().lower()
    
    match_indices = []
    for idx, row in df_master.iterrows():
        combined_row_text = " ".join(row.values).lower()
        if query_clean in combined_row_text:
            match_indices.append(idx)
            
    hasil_cari = df_master.loc[match_indices]

# Logika Penanganan Hasil Pencarian
if not hasil_cari.empty:
    if len(hasil_cari) == 1:
        target_row_idx = hasil_cari.index[0]
        st.session_state['selected_index'] = target_row_idx
    else:
        st.warning(f"Ditemukan **{len(hasil_cari)} data** yang cocok dengan kata kunci **'{search_query}'**. Silakan pilih data yang sesuai dari daftar di bawah:")
        
        for idx, row in hasil_cari.iterrows():
            c_id = str(row.get(id_col, '-'))
            c_nama = str(row.get(nama_col, '-'))
            c_perusahaan = str(row.get('NAMA PERusahaan', row.get('NAMA PERUSAHAAN', '')))
            
            cols_btn = st.columns([3, 2, 1])
            cols_btn[0].markdown(f"**{c_nama}** (ID: `{c_id}`)")
            cols_btn[1].markdown(f"🏢 {c_perusahaan}")
            if cols_btn[2].button("Pilih", key=f"btn_pick_{idx}"):
                st.session_state['selected_index'] = idx
                st.rerun()
        
        st.markdown("---")
        if 'selected_index' in st.session_state:
            del st.session_state['selected_index']
else:
    if search_query:
        st.warning(f"Data '{search_query}' tidak ditemukan di dalam file CSV GitHub.")
    if 'selected_index' in st.session_state:
        del st.session_state['selected_index']

# Tampilkan Form Edit berdasarkan Indeks Baris yang Dipilih
if 'selected_index' in st.session_state:
    target_idx = st.session_state['selected_index']
    
    try:
        df_fresh = load_data_from_github()
    except:
        df_fresh = df_master

    # Pastikan indeks ada di data terbaru
    if target_idx < len(df_fresh):
        person = df_fresh.loc[target_idx]

        curr_nama = str(person.get(nama_col, '-'))
        curr_id = str(person.get(id_col, '-'))
        curr_perusahaan = str(person.get('NAMA PERUSAHAAN', '-'))

        form_key = f"form_edit_{target_idx}_{st.session_state.form_version}"
        with st.form(form_key):
            st.markdown(f"### ✏️ Edit Data: **{curr_nama}**")
            st.info(f"🆔 **ID Personil:** {curr_id}  |  🏢 **Perusahaan:** {curr_perusahaan}")
            st.caption("Ubah data apa saja pada kolom di bawah ini, lalu klik tombol Simpan.")

            edited_values = {}
            valid_cols = [c for c in df_fresh.columns if not str(c).startswith('Unnamed:')]
            
            c1, c2 = st.columns(2)
            for i, col in enumerate(valid_cols):
                with (c1 if i % 2 == 0 else c2):
                    unique_key = f"fld_{target_idx}_{col}_{st.session_state.form_version}"
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
                            
                        df_live = pd.read_csv(io.StringIO(file_decoded), encoding="latin1", dtype=str)
                        df_live.columns = df_live.columns.astype(str).str.strip()
                        df_live = df_live.fillna("")
                        
                        # Simpan langsung menggunakan indeks baris yang sama persis
                        if target_idx < len(df_live):
                            for col_name, val in edited_values.items():
                                if col_name in df_live.columns:
                                    df_live.loc[target_idx, col_name] = val

                            updated_csv_str = df_live.to_csv(index=False, encoding="latin1")
                            updated_b64 = base64.b64encode(updated_csv_str.encode("latin1")).decode("utf-8")
                            
                            payload = {
                                "message": f"Update data nasional baris ke-{target_idx}",
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
                            st.error("Indeks baris di file GitHub telah berubah. Silakan cari ulang data.")
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke GitHub: {e}")
    else:
        st.error("Data tidak ditemukan pada indeks terbaru. Silakan cari ulang.")
else:
    if not search_query:
        st.info("💡 Ketik nama karyawan atau ID pada kotak pencarian di atas untuk mulai mencari.")
        with st.expander("Lihat Seluruh Tabel Database Nasional"):
            st.dataframe(df_master, use_container_width=True)
