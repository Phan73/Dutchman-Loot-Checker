import streamlit as st
import pandas as pd
import re
import io

# --- LANGUAGE DICTIONARY (RESTORED & UPDATED INSTRUCTIONS) ---
LANGS = {
    "한국어": {
        "title": "🛡️ 길드 전리품 감사 도구 (Flying Dutchman 독점)",
        "sidebar_head": "1. 로그 업로드",
        "loot_label": "전리품 로그 업로드 (.txt)",
        "chest_label": "창고 로그 업로드 (CSV 또는 복사본 TXT)",
        "tab_full": "전체 리포트 (Full Report)",
        "tab_player": "개별 감사 (Player Audit)",
        "search_label": "👤 플레이어 이름 검색",
        "reset_btn": "모든 데이터 초기화 (Reset)",
        "item_col": "아이템 이름",
        "looted_col": "획득량",
        "chest_col": "입고 확인됨",
        "miss_col": "누락됨",
        "by_col": "획득자 명단",
        "status_col": "상태",
        "banked": "✅ 입고 완료",
        "missing": "❌ 미입고",
        "instruction_head": "📖 상세 사용 방법 (중요: Excel 및 복사-붙여넣기 사용자 필독)",
        "instructions": """
        ### 📋 감사 도구 사용 가이드
        1. **전리품 로그 내보내기:** 전리품 로거(Loot Logger)를 사용하여 데이터를 `.txt` 파일로 저장합니다.
        2. **창고 로그 내보내기 (두 가지 방법 모두 지원):**
            * **방법 A (복사-붙여넣기):** 게임 내 창고 로그를 전체 드래그하여 복사한 후, 메모장(`.txt`)에 붙여넣어 저장하세요.
            * **방법 B (Excel):** 게임 로그를 Excel에 붙여넣고 수정했다면, 반드시 `.csv` (쉼표로 분리) 형식으로 저장하세요.
        3. **파일 업로드:** 사이드바의 업로드 칸에 모든 전리품 로그와 창고 로그 파일을 넣습니다. (여러 개 동시 선택 가능)
        4. **중복 자동 제거:** 여러 명이 동시에 기록했더라도 앱이 자동으로 중복을 제거하여 정확한 수치를 계산합니다.
        5. **결과 확인:** 표에는 **I The Flying Dutchman I** 길드원이 획득했지만 아직 창고에 입고되지 않은 아이템만 표시됩니다.
        
        **💡 팁:** 게임에서 직접 복사한 텍스트 파일도 앱이 자동으로 '아이템'과 '수량' 컬럼을 찾아냅니다!
        """
    },
    "English": {
        "title": "🛡️ Guild Loot Auditor (Flying Dutchman Exclusive)",
        "sidebar_head": "1. Upload Logs",
        "loot_label": "Upload Loot Logs (.txt)",
        "chest_label": "Upload Chest Logs (CSV or Copy-Paste TXT)",
        "tab_full": "Full Report",
        "tab_player": "Player Audit",
        "search_label": "👤 Search Player Name",
        "reset_btn": "Clear All Data",
        "item_col": "Item Name",
        "looted_col": "Looted Qty",
        "chest_col": "In Chests",
        "miss_col": "Missing",
        "by_col": "Looted By (Full List)",
        "status_col": "Status",
        "banked": "✅ Banked",
        "missing": "❌ Missing",
        "instruction_head": "📖 Detailed Instructions (Supports Excel & Copy-Paste)",
        "instructions": """
        ### 📋 How to use the Audit Tool
        1. **Export Loot Logs:** Use your Albion Loot Logger to export the loot data as a `.txt` file.
        2. **Export Chest Logs (Two supported methods):**
            * **Method A (Copy-Paste):** Highlight the logs inside the game, copy them, and paste them into a standard Notepad (`.txt`) file.
            * **Method B (Excel):** If you use Excel to organize logs, save the file as a `.csv` format before uploading.
        3. **Upload Files:** Drag and drop **all** your loot logs and chest logs into the sidebar.
        4. **Automatic Cleanup:** The app will automatically remove duplicate lines from multiple recorders.
        5. **Check Results:** The table only shows items looted by **I The Flying Dutchman I** that are still missing from the chest.
        
        **💡 Pro-Tip:** You don't need to format the copy-pasted text. The app is smart enough to find the 'Item' and 'Amount' columns automatically!
        """
    }
}

st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")
sel_lang = st.sidebar.selectbox("🌐 Language / 언어 선택", ["한국어", "English"])
T = LANGS[sel_lang]

st.title(T["title"])
with st.expander(T["instruction_head"], expanded=True):
    st.markdown(T["instructions"])

# --- CORE LOGIC ---
def simplify(text):
    return re.sub(r'[^a-z0-9]', '', str(text).lower())

def find_best_column(df, targets):
    for col in df.columns:
        if simplify(col) in [simplify(t) for t in targets]:
            return col
    return None

def robust_read(file):
    raw_data = file.read()
    try: content = raw_data.decode('utf-8-sig')
    except: content = raw_data.decode('latin1')
    
    # Check for raw copy-paste (Tab-separated)
    if '\t' in content and 'Amount' in content:
        return pd.read_csv(io.StringIO(content), sep='\t', engine='python')
    
    # Default to CSV
    sep = ';' if content.count(';') > content.count(',') else ','
    return pd.read_csv(io.StringIO(content), sep=sep, engine='python', on_bad_lines='skip')

# --- SIDEBAR & BUTTONS ---
st.sidebar.header(T["sidebar_head"])
if st.sidebar.button(T["reset_btn"]):
    st.cache_data.clear()
    st.rerun()

loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True, key="loot")
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True, key="chest")

TARGET_GUILD = "I The Flying Dutchman I"

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
            c_time = find_best_column(df, ['timestamputc', 'date'])
            c_id = find_best_column(df, ['itemid', 'id'])
            if c_item and c_qty:
                df = df.rename(columns={c_item: 'item_name', c_qty: 'quantity', c_name: 'player', c_guild: 'guild', c_time: 'time', c_id: 'id'})
                all_loot.append(df)
        
        loot_df = pd.concat(all_loot).drop_duplicates(subset=['time', 'player', 'id'])
        loot_df = loot_df[loot_df['guild'] == TARGET_GUILD]

        # 2. CHEST
        all_chest = []
        for f in chest_files:
            df = robust_read(f)
            c_item_ch = find_best_column(df, ['item', 'itemname'])
            c_qty_ch = find_best_column(df, ['amount', 'quantity', 'totalinchest'])
            if c_item_ch and c_qty_ch:
                df = df.rename(columns={c_item_ch: 'Item', c_qty_ch: 'Amount'})
                all_chest.append(df)
        chest_df = pd.concat(all_chest).groupby('Item')['Amount'].sum().reset_index()

        # 3. UI TABS
        tab1, tab2 = st.tabs([T["tab_full"], T["tab_player"]])

        with tab1:
            l_sum = loot_df.groupby('item_name').agg({'quantity': 'sum', 'player': lambda x: ', '.join(sorted(list(set(x.astype(str))))) }).reset_index()
            full_res = pd.merge(l_sum, chest_df, left_on='item_name', right_on='Item', how='left').fillna(0)
            full_res['Missing_Qty'] = full_res['quantity'] - full_res['Amount']
            full_res = full_res[full_res['Missing_Qty'] > 0]
            st.dataframe(full_res[['item_name', 'quantity', 'Amount', 'Missing_Qty', 'player']].rename(columns={'item_name': T["item_col"], 'quantity': T["looted_col"], 'Amount': T["chest_col"], 'Missing_Qty': T["miss_col"], 'player': T["by_col"]}), use_container_width=True, hide_index=True, column_config={T["by_col"]: st.column_config.TextColumn(width="large")})

        with tab2:
            search_query = st.text_input(T["search_label"], "").strip()
            if search_query:
                p_loot = loot_df[loot_df['player'].str.contains(search_query, case=False)]
                if not p_loot.empty:
                    p_sum = p_loot.groupby('item_name')['quantity'].sum().reset_index()
                    p_final = pd.merge(p_sum, chest_df, left_on='item_name', right_on='Item', how='left').fillna(0)
                    p_final[T["status_col"]] = p_final.apply(lambda r: T["banked"] if r['Amount'] >= r['quantity'] else T["missing"], axis=1)
                    st.dataframe(p_final[['item_name', 'quantity', T["status_col"]]].rename(columns={'item_name': T["item_col"], 'quantity': T["looted_col"]}), use_container_width=True, hide_index=True)
                else:
                    st.warning(f"No guild member found matching '{search_query}'.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info(f"🛡️ Waiting for {TARGET_GUILD} logs...")
