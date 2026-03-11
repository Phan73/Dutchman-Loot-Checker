import streamlit as st
import pandas as pd

# --- LANGUAGE DICTIONARY ---
LANGS = {
    "한국어": {
        "title": "🛡️ 길드 전리품 감사 도구",
        "sidebar_head": "1. 로그 업로드",
        "loot_label": "전리품 로그 업로드 (여러 파일 가능)",
        "chest_label": "길드 창고 로그 업로드 (여러 파일 가능)",
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
        ### 📋 사용 가이드
        1. **파일 형식:** .txt 또는 Excel에서 저장한 .csv 파일 모두 지원합니다.
        2. **자동 인식:** 대소문자가 다르거나 공백이 있어도 앱이 자동으로 컬럼을 찾아냅니다.
        3. **중복 제거:** 동일한 시간과 아이템 ID를 가진 중복 데이터는 하나로 계산됩니다.
        """
    },
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
        "instruction_head": "📖 Instructions",
        "instructions": "Upload your logs. The app handles different column names automatically."
    }
}

st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")
sel_lang = st.sidebar.selectbox("🌐 Language / 언어 선택", ["한국어", "English"])
T = LANGS[sel_lang]

st.title(T["title"])
with st.expander(T["instruction_head"]):
    st.markdown(T["instructions"])

TARGET_GUILD = "I The Flying Dutchman I"

# --- SMART COLUMN FINDER ---
def find_column(df, possible_names):
    """Finds a column even if case or spacing is different."""
    for col in df.columns:
        clean_col = col.strip().lower().replace("_", "").replace(" ", "")
        for target in possible_names:
            if clean_col == target.lower().replace("_", "").replace(" ", ""):
                return col
    return None

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
            
            # Use Smart Finder for Loot Columns
            c_item = find_column(df, ['item_name', 'itemname', 'Item'])
            c_qty = find_column(df, ['quantity', 'qty', 'amount'])
            c_name = find_column(df, ['looted_by__name', 'looter', 'player'])
            c_guild = find_column(df, ['looted_by__guild', 'guild'])
            c_time = find_column(df, ['timestamp_utc', 'date', 'time'])
            c_id = find_column(df, ['item_id', 'id'])

            # Rename found columns to standard names for logic
            rename_map = {c_item: 'item_name', c_qty: 'quantity', c_name: 'looted_by__name', 
                          c_guild: 'looted_by__guild', c_time: 'timestamp_utc', c_id: 'item_id'}
            df = df.rename(columns={k: v for k, v in rename_map.items() if k is not None})
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

        # 2. Process Chest Logs
        all_chest = []
        for f in chest_files:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
            # Use Smart Finder for Chest Columns
            c_item_ch = find_column(df, ['item', 'item_name', 'itemname'])
            c_qty_ch = find_column(df, ['amount', 'quantity', 'qty'])
            
            df = df.rename(columns={c_item_ch: 'Item', c_qty_ch: 'Amount'})
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

        # 4. Display Result
        search = st.text_input(T["search_label"], "")
        display_df = missing[[
            'looted_by__guild', 'item_name', 'quantity', 'Amount', 'Missing_Qty', 'looted_by__name'
        ]].rename(columns={
            'looted_by__guild': T["guild_col"], 'item_name': T["item_col"], 'quantity': T["looted_col"],
            'Amount': T["chest_col"], 'Missing_Qty': T["miss_col"], 'looted_by__name': T["by_col"]
        })

        if search:
            display_df = display_df[display_df[T["by_col"]].str.contains(search, case=False)]

        st.dataframe(display_df, use_container_width=True)
        
        csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(T["btn_text"], csv_data, "audit_report.csv", "text/csv")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Waiting for logs... / 로그 업로드를 기다리는 중...")
