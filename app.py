import streamlit as st
import pandas as pd
import re
import io

# --- LANGUAGE DICTIONARY (PRESERVED EXACTLY) ---
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
        "instruction_head": "📖 상세 사용 방법 (중요: Excel 사용자 필독)",
        "instructions": """
        ### 📋 감사 도구 사용 가이드
        1. **전리품 로그 내보내기:** 전리품 로거(Loot Logger)를 사용하여 데이터를 `.txt` 파일로 저장합니다.
        2. **창고 로그 내보내기:** 길드 창고(은신처 또는 개인섬)에서 '로그' 탭을 클릭하여 내역을 `.csv` 또는 `.txt`로 저장합니다.
        3. **파일 업로드:** 사이드바의 업로드 칸에 모든 전리품 로그와 창고 로그 파일을 드래그하여 넣습니다. (여러 개 동시 선택 가능)
        4. **중복 자동 제거:** 여러 명이 동시에 같은 드랍을 기록했더라도, 앱이 자동으로 중복을 제거하여 정확한 수치를 계산합니다.
        5. **결과 확인:** 표에는 **I The Flying Dutchman I** 길드원이 획득했지만 아직 창고에 입고되지 않은 아이템만 표시됩니다.
        
        **💡 Excel 사용자 참고:** Excel에서 파일을 열어 수정 후 `.csv`로 저장한 경우에도 앱이 자동으로 컬럼명을 인식하여 오류를 방지합니다.
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
        "instruction_head": "📖 Detailed Instructions (For Excel Users)",
        "instructions": """
        ### 📋 How to use the Audit Tool
        1. **Export Loot Logs:** Use your Albion Loot Logger to export the loot data as a `.txt` file.
        2. **Export Chest Logs:** Go to your Guild Chest (HO or Island), click on the 'Logs' tab, and export as `.csv` or `.txt`.
        3. **Upload Files:** Drag and drop **all** your loot logs and chest logs into the sidebar.
        4. **Automatic Cleanup:** The app will automatically remove duplicate lines if multiple people recorded the same loot event.
        5. **Check Results:** The table will only show items looted by **I The Flying Dutchman I** that have not been fully deposited.
        
        **💡 Note for Excel Users:** If you edit files in Excel and save as `.csv`, this app will automatically detect the columns even if the headers change slightly.
        """
    }
}

st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")
sel_lang = st.sidebar.selectbox("🌐 Language / 언어 선택", ["한국어", "English"])
T = LANGS[sel_lang]

st.title(T["title"])
with st.expander(T["instruction_head"], expanded=True):
    st.markdown(T["instructions"])

# --- CORE LOGIC UTILITIES ---
def simplify(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def find_best_column(df, targets):
    for col in df.columns:
        if simplify(col) in [simplify(t) for t in targets]:
            return col
    return None

def robust_read(file):
    """Attempts to read files regardless of Excel's secret formatting."""
    content = file.read()
    # Handle encoding and guess separator
    try:
        decoded = content.decode('utf-8-sig')
    except:
        decoded = content.decode('latin1')
    
    # Check if it's semicolon or comma
    sep = ';' if decoded.count(';') > decoded.count(',') else ','
    return pd.read_csv(io.StringIO(decoded), sep=sep, engine='python')

# --- SIDEBAR & PROCESSING ---
st.sidebar.header(T["sidebar_head"])
loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True)
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True)

if loot_files and chest_files:
    try:
        # 1. LOOT
        all_loot = []
        for f in loot_files:
            df = robust_read(f)
            c_item = find_best_column(df, ['itemname', 'item'])
            c_qty = find_best_column(df, ['quantity', 'qty', 'amount'])
            c_name = find_best_column(df, ['lootedbyname', 'looter', 'player'])
            c_guild = find_best_column(df, ['lootedbyguild', 'guild'])
            c_time = find_best_column(df, ['timestamputc', 'date', 'time'])
            c_id = find_best_column(df, ['itemid', 'id'])
            
            df = df.rename(columns={c_item: 'item_name', c_qty: 'quantity', c_name: 'looted_by__name', 
                                    c_guild: 'looted_by__guild', c_time: 'timestamp_utc', c_id: 'item_id'})
            all_loot.append(df)
        
        loot_df = pd.concat(all_loot, ignore_index=True).drop_duplicates(subset=['timestamp_utc', 'looted_by__name', 'item_id'])
        loot_df = loot_df[loot_df['looted_by__guild'] == "I The Flying Dutchman I"]

        # 2. CHEST (The problematic part)
        all_chest = []
        for f in chest_files:
            df = robust_read(f)
            c_item_ch = find_best_column(df, ['item', 'itemname'])
            c_qty_ch = find_best_column(df, ['amount', 'quantity', 'qty'])
            
            if not c_item_ch or not c_qty_ch:
                st.error(f"❌ Error in {f.name}: Missing 'Item' or 'Amount'. Found: {list(df.columns)}")
                st.stop()
                
            df = df.rename(columns={c_item_ch: 'Item', c_qty_ch: 'Amount'})
            all_chest.append(df)
        
        chest_df = pd.concat(all_chest, ignore_index=True)

        # 3. MERGE
        l_sum = loot_df.groupby('item_name').agg({'quantity':'sum', 'looted_by__name': lambda x: ', '.join(sorted(set(x.astype(str))))}).reset_index()
        c_sum = chest_df.groupby('Item').agg({'Amount':'sum'}).reset_index()
        
        res = pd.merge(l_sum, c_sum, left_on='item_name', right_on='Item', how='left').fillna(0)
        res['Missing_Qty'] = res['quantity'] - res['Amount']
        res = res[res['Missing_Qty'] > 0]

        # 4. DISPLAY
        search = st.text_input(T["search_label"], "")
        display = res.rename(columns={'item_name': T["item_col"], 'quantity': T["looted_col"], 'Amount': T["chest_col"], 'Missing_Qty': T["miss_col"], 'looted_by__name': T["by_col"]})
        
        if search:
            display = display[display[T["by_col"]].str.contains(search, case=False)]
            
        st.dataframe(display.drop(columns=['Item'], errors='ignore'), use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Waiting for logs... / 로그 업로드를 기다리는 중...")
