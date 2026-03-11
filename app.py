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
        "instruction_head": "📖 How to use",
        "instructions": """
        1. **Export Logs:** Get your Loot Logs (.txt) and Chest Logs (.csv/.txt).
        2. **Upload:** Use the sidebar to upload all files. You can select multiple files at once.
        3. **Audit:** The app automatically removes duplicates (if multiple people recorded the same drop) and filters for your guild.
        4. **Check:** Look at the 'Missing' column to see what items weren't deposited.
        """
    },
    "한국어": {
        "title": "🛡️ 길드 전리품 감사 도구",
        "sidebar_head": "1. 로그 업로드",
        "loot_label": "전리품 로그 업로드 (다중 선택 가능)",
        "chest_label": "창고 로그 업로드 (다중 선택 가능)",
        "search_label": "🔍 플레이어 이름으로 검색",
        "btn_text": "리포트 다운로드",
        "guild_col": "길드",
        "item_col": "아이템 이름",
        "looted_col": "총 획득량",
        "chest_col": "창고 확인됨",
        "miss_col": "누락됨",
        "by_col": "획득자",
        "dup_msg": "중복된 항목 {}개를 제거했습니다!",
        "no_loot": "해당 길드의 전리품을 찾을 수 없습니다.",
        "instruction_head": "📖 사용 방법",
        "instructions": """
        1. **로그 내보내기:** 전리품 로그(.txt)와 창고 로그(.csv/.txt)를 준비합니다.
        2. **업로드:** 사이드바를 사용하여 모든 파일을 업로드합니다. 여러 파일을 한 번에 선택할 수 있습니다.
        3. **감사:** 앱이 자동으로 중복 항목을 제거하고(여러 명이 동일한 드랍을 기록한 경우) 길드원을 필터링합니다.
        4. **확인:** '누락됨' 컬럼을 확인하여 창고에 입고되지 않은 아이템을 확인합니다.
        """
    }
}

# --- UI SETUP ---
st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")

# Language Selector
sel_lang = st.sidebar.selectbox("🌐 Language / 언어", ["English", "한국어"])
T = LANGS[sel_lang]

st.title(T["title"])

# Instructions
with st.expander(T["instruction_head"]):
    st.write(T["instructions"])

TARGET_GUILD = "I The Flying Dutchman I"

# --- SIDEBAR UPLOADS ---
st.sidebar.header(T["sidebar_head"])
loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True)
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True)

if loot_files and chest_files:
    try:
        # 1. Process Loot Logs
        all_loot = []
        for f in loot_files:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            all_loot.append(df)
        loot_df = pd.concat(all_loot, ignore_index=True)

        # Deduplicate
        initial_count = len(loot_df)
        loot_df = loot_df.drop_duplicates(subset=['timestamp_utc', 'looted_by__name', 'item_id'])
        removed = initial_count - len(loot_df)
        if removed > 0:
            st.toast(T["dup_msg"].format(removed))

        # Filter Guild
        if 'looted_by__guild' in loot_df.columns:
            loot_df = loot_df[loot_df['looted_by__guild'] == TARGET_GUILD]

        if loot_df.empty:
            st.warning(T["no_loot"])
            st.stop()

        # 2. Process Chest Logs
        all_chest = []
        for f in chest_files:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            all_chest.append(df)
        chest_df = pd.concat(all_chest, ignore_index=True)

        # 3. Aggregate & Compare
        looted_sum = loot_df.groupby('item_name').agg({
            'quantity': 'sum',
            'looted_by__name': lambda x: ', '.join(sorted(set(x.astype(str)))),
            'looted_by__guild': 'first'
        }).reset_index()

        chest_sum = chest_df.groupby('Item').agg({'Amount': 'sum'}).reset_index()

        comparison = pd.merge(looted_sum, chest_sum, left_on='item_name', right_on='Item', how='left').fillna(0)
        comparison['Missing_Qty'] = comparison['quantity'] - comparison['Amount']
        missing = comparison[comparison['Missing_Qty'] > 0].copy()

        # 4. Display Results
        search = st.text_input(T["search_label"], "")
        
        display_df = missing[[
            'looted_by__guild', 'item_name', 'quantity', 'Amount', 'Missing_Qty', 'looted_by__name'
        ]].rename(columns={
            'looted_by__guild': T["guild_col"],
            'item_name': T["item_col"],
            'quantity': T["looted_col"],
            'Amount': T["chest_col"],
            'Missing_Qty': T["miss_col"],
            'looted_by__name': T["by_col"]
        })

        if search:
            display_df = display_df[display_df[T["by_col"]].str.contains(search, case=False)]

        st.dataframe(display_df, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Waiting for logs... / 로그 업로드를 기다리는 중...")
