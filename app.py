import streamlit as st
import pandas as pd

# --- LANGUAGE DICTIONARY ---
LANGS = {
    "English": {
        "title": "🛡️ Guild Loot Auditor",
        "sidebar_head": "1. Upload Logs",
        "loot_label": "Upload Loot Logs (Multiple)",
        "chest_label": "Upload Chest Logs (Multiple)",
        "search_label": "🔍 Search by Player Name",
        "btn_text": "Download Report",
        "guild_col": "Guild",
        "item_col": "Item Name",
        "looted_col": "Total Looted",
        "chest_col": "In Chests",
        "miss_col": "Missing",
        "by_col": "Looted By",
        "dup_msg": "Removed {} duplicate entries!",
        "no_loot": "No loot found for this guild.",
        "instruction_head": "📖 Detailed Instructions",
        "instructions": """
        ### 📋 How to use the Audit Tool
        1. **Export Loot Logs:** Use your Albion Loot Logger to export the loot data as a `.txt` file.
        2. **Export Chest Logs:** Go to your Guild Chest (HO or Island), click on the 'Logs' tab, and export as `.csv` or `.txt`.
        3. **Upload Files:** Drag and drop **all** your loot logs and chest logs into the sidebar.
        4. **Automatic Cleanup:** The app will automatically remove duplicate lines if multiple people recorded the same loot event.
        5. **Check Results:** The table will only show items looted by **I The Flying Dutchman I** that have not been fully deposited.
        """
    },
    "한국어": {
        "title": "🛡️ 길드 전리품 감사 도구",
        "sidebar_head": "1. 로그 업로드",
        "loot_label": "전리품 로그 업로드 (여러 파일 선택 가능)",
        "chest_label": "길드 창고 로그 업로드 (여러 파일 선택 가능)",
        "search_label": "🔍 플레이어 이름으로 검색",
        "btn_text": "결과 다운로드",
        "guild_col": "길드",
        "item_col": "아이템 이름",
        "looted_col": "총 획득량",
        "chest_col": "입고 확인됨",
        "miss_col": "누락됨",
        "by_col": "획득자",
        "dup_msg": "중복된 항목 {}개를 제거했습니다!",
        "no_loot": "해당 길드원의 데이터를 찾을 수 없습니다.",
        "instruction_head": "📖 상세 사용 방법",
        "instructions": """
        ### 📋 감사 도구 사용 가이드
        1. **전리품 로그 내보내기:** 전리품 로거(Loot Logger)를 사용하여 데이터를 `.txt` 파일로 저장합니다.
        2. **창고 로그 내보내기:** 길드 창고(은신처 또는 개인섬)에서 '로그' 탭을 클릭하여 내역을 `.csv` 또는 `.txt`로 저장합니다.
        3. **파일 업로드:** 사이드바의 업로드 칸에 모든 전리품 로그와 창고 로그 파일을 드래그하여 넣습니다. (여러 개 동시 선택 가능)
        4. **중복 자동 제거:** 여러 명이 동시에 같은 드랍을 기록했더라도, 앱이 자동으로 중복을 제거하여 정확한 수치를 계산합니다.
        5. **결과 확인:** 표에는 **I The Flying Dutchman I** 길드원이 획득했지만 아직 창고에 입고되지 않은 아이템만 표시됩니다.
        """
    }
}

# --- UI SETUP ---
st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")

# Language Selector
sel_lang = st.sidebar.selectbox("🌐 Language / 언어 선택", ["한국어", "English"])
T = LANGS[sel_lang]

st.title(T["title"])

# Detailed Instructions in an Expander
with st.expander(T["instruction_head"], expanded=True):
    st.markdown(T["instructions"])

TARGET_GUILD = "I The Flying Dutchman I"

# --- SIDEBAR UPLOADS ---
st.sidebar.header(T["sidebar_head"])
loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True)
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True)

if loot_files and chest_files:
    try:
        # 1. Process Multiple Loot Logs
        all_loot = []
        for f in loot_files:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            all_loot.append(df)
        loot_df = pd.concat(all_loot, ignore_index=True)

        # Deduplication using Timestamp, Looter, and Item ID
        initial_count = len(loot_df)
        loot_df = loot_df.drop_duplicates(subset=['timestamp_utc', 'looted_by__name', 'item_id'])
        removed = initial_count - len(loot_df
