import streamlit as st
import pandas as pd
import requests
import io
import time
import base64

st.set_page_config(
    page_title="Dashboard Database Nasional",
    page_icon="🦅",
    layout="wide"
)

st.title("🦅 Dashboard Data - Database Nasional")
st.markdown("Kelola dan edit data personil dengan cepat. Perubahan tersimpan **permanen ke GitHub**.")

REPO_NAME = "odingkirut-dotcom/dashboard-gelatik"
FILE_PATH = "Summary Database Nasional 13 November 2026.csv"

# Fungsi untuk memuat data dengan aman
def load_data():
    url = f"https://raw.githubusercontent.com/{REPO_NAME}/main/Summary%20Database%20Nasional%2013%20November%202026.csv?t={time.time()}"
    resp = requests.get(url)
    if resp.status_code == 200:
        content = resp.content.decode("latin1")
        if "404: Not Found" in content[:50]:
            raise Exception("File CSV di GitHub masih berisi teks 404. Harap pastikan file CSV sudah di-restore di GitHub.")
        df = pd.read_csv(io.StringIO(content), encoding="latin1", dtype=str)
        df.columns = df.columns.astype(str).str.strip()
        return df.fillna("")
    else:
        raise Exception(f"Gagal mengunduh file (Kode: {resp.status_code})")

try:
    with st.spinner("Memuat database dari GitHub..."):
        df_master = load_data()
except Exception as e:
    st.error(f"{e}")
    st.stop()

if 'form_version' not in st.session_state:
    st.session_state.form_version = 0

if st.sidebar.button("🔄 Muat Ulang Data Terbaru"):
    if 'selected_person_id' in st.session_state:
        del st.session_state['selected_person_id']
    st.session_state.form_version += 1
    st.rerun()

cols_list = list(df_master.columns)
id_col = next((c for c in cols_list if 'id' in c.lower() or 'personil' in c.lower()), cols_list[0])
nama_col = next((c for c in cols_list if 'nama' in c.lower() and 'perusahaan' not in c.lower()), cols_list[1] if len(cols_list) > 1 else cols_list[0])

st.subheader("🔎 Cari Karyawan Berdasarkan Nama / ID")
search_query = st.text_input("Ketik Nama Lengkap atau ID:", key="search_box")

if not search_query and 'selected_person_id' in st.session_state:
    del st.session_state['selected_person_id']

if search_query:
    q = search_query.strip().lower()
    match_idx = []
    for idx, row in df_master.iterrows():
        if q in " ".join(row.values).lower():
            match_idx.append(idx)
    hasil_cari = df_master.loc[match_idx]
    
    if not hasil_cari.empty:
        if len(hasil_cari) == 1:
            row_item = hasil_cari.iloc[0]
            st.session_state['selected_person_id'] = str(row_item.get(id_col, '')).strip()
        else:
            st.warning(f"Ditemukan {len(hasil_cari)} data. Pilih salah satu:")
            for idx, row in hasil_cari.iterrows():
                c_id = str(row.get(id_col, '-')).strip()
                c_nama = str(row.get(nama_col, '-'))
                c_pt = str(row.get('NAMA PERUSAHAAN', ''))
                if st.button(f"{c_nama} (ID: {c_id}) - {c_pt}", key=f"btn_{c_id}_{idx}"):
                    st.session_state['selected_person_id'] = c_id
                    st.rerun()
            st.stop()
    else:
        st.warning("Data tidak ditemukan.")
        if 'selected_person_id' in st.session_state:
            del st.session_state['selected_person_id']

if 'selected_person_id' in st.session_state:
    target_id = st.session_state['selected_person_id']
    
    # Cari baris HANYA berdasarkan ID unik (karena ID tidak pernah berubah walau nama diedit)
    matched_master = df_master[df_master[id_col].astype(str).str.strip() == target_id]
        
    if not matched_master.empty:
        person = matched_master.iloc[0]
        
        with st.form(f"form_{target_id}_{st.session_state.form_version}"):
            st.markdown(f"### ✏️ Edit Data: **{person.get(nama_col, '')}**")
            st.info(f"🆔 ID: {target_id} | 🏢 Perusahaan: {person.get('NAMA PERUSAHAAN', '')}")
            
            edited_vals = {}
            valid_cols = [c for c in df_master.columns if not c.startswith('Unnamed:')]
            
            c1, c2 = st.columns(2)
            for i, col in enumerate(valid_cols):
                with (c1 if i % 2 == 0 else c2):
                    val = str(person.get(col, ''))
                    edited_vals[col] = st.text_input(str(col), value=val, key=f"inp_{target_id}_{col}")
            
            submitted = st.form_submit_button("💾 Simpan Perubahan Secara Permanen ke GitHub", use_container_width=True)
            
            if submitted:
                with st.spinner("Menyimpan ke GitHub..."):
                    try:
                        api_url = f"https://api.github.com/repos/{REPO_NAME}/contents/Summary%20Database%20Nasional%2013%20November%202026.csv"
                        headers = {
                            "Authorization": f"Bearer {st.secrets['GITHUB_TOKEN']}",
                            "Accept": "application/vnd.github+json"
                        }
                        
                        # Ambil data live paling fresh dari GitHub
                        r_get = requests.get(api_url, headers=headers)
                        if r_get.status_code != 200:
                            st.error(f"Gagal mengambil file dari API GitHub (Status: {r_get.status_code})")
                            st.stop()
                            
                        j_data = r_get.json()
                        sha = j_data['sha']
                        
                        r_dl = requests.get(f"{j_data['download_url']}?t={time.time()}")
                        df_live = pd.read_csv(io.StringIO(r_dl.content.decode("latin1")), encoding="latin1", dtype=str)
                        df_live.columns = df_live.columns.astype(str).str.strip()
                        df_live = df_live.fillna("")
                        
                        # Cari baris di file LIVE GitHub STRICTLY berdasarkan ID Unik
                        live_match = df_live[df_live[id_col].astype(str).str.strip() == target_id]
                            
                        if not live_match.empty:
                            live_idx = live_match.index[0]
                            
                            # Update kolom pada baris tersebut secara presisi
                            for k, v in edited_vals.items():
                                if k in df_live.columns:
                                    df_live.loc[live_idx, k] = v
                                    
                            csv_str = df_live.to_csv(index=False, encoding="latin1")
                            b64_content = base64.b64encode(csv_str.encode("latin1")).decode("utf-8")
                            
                            payload = {
                                "message": f"Update data ID {target_id} via Dashboard",
                                "content": b64_content,
                                "sha": sha
                            }
                            
                            r_put = requests.put(api_url, headers=headers, json=payload)
                            if r_put.status_code in [200, 201]:
                                st.session_state.form_version += 1
                                st.success("✅ Perubahan berhasil disimpan permanen ke GitHub!")
                                st.balloons()
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Gagal menyimpan ke GitHub: {r_put.text}")
                        else:
                            st.error(f"Data dengan ID '{target_id}' tidak ditemukan pada file live GitHub terbaru.")
                    except Exception as err:
                        st.error(f"Error: {err}")
    else:
        st.error("Data tidak ditemukan.")
else:
    st.info("💡 Ketik nama atau ID pada kolom pencarian di atas.")
    with st.expander("Lihat Seluruh Tabel"):
        st.dataframe(df_master, use_container_width=True)
