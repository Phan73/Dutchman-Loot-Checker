import streamlit as st
import pandas as pd
import re
import io

# --- LANGUAGE DICTIONARY (RESTORED ORIGINAL INSTRUCTIONS) ---
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
        "status_col": "개인별 입고 상태",
        "audit_col": "감사 확인 (사망/특이사항)",
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
        6. **개별 감사 기능:** '개별 감사' 탭에서 플레이어를 검색하면 해당 인원이 아이템을 넣었는지 추적합니다. (예: Joker가 넣고 Carlun이 안 넣었다면, Carlun만 미입고로 표시됨)
        
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
        "by_col": "Looted By",
        "status_col": "Personal Status",
        "audit_col": "Audit Action (Died/Other)",
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
        5. **Check Results:** The table only shows items looted by **I The Flying Dutchman I** that are still missing.
        6. **Strict Name Matching:** This version checks who actually deposited the item. If Joker deposited and Carlun didn't, only Carlun will be flagged as missing.
        """
    }
}

st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")
sel_lang = st.sidebar.selectbox("🌐 Language / 언어 선택", list(LANGS.keys()))
T = LANGS[sel_lang]

st.title(T["title"])
with st.expander(T["instruction_head"], expanded=True):
    st.markdown(T["instructions"])

# --- HELPERS ---
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
    if '\t' in content: return pd.read_csv(io.StringIO(content), sep='\t', engine='python', on_bad_lines='skip')
    for sep in [',', ';']:
        df = pd.read_csv(io.StringIO(content), sep=sep, engine='python', on_bad_lines='skip')
        if len(df.columns) > 1: return df
    return pd.read_csv(io.StringIO(content), engine='python')

# --- SIDEBAR & DATA RESET ---
st.sidebar.header(T["sidebar_head"])
if st.sidebar.button(T["reset_btn"]):
    st.cache_data.clear()
    st.rerun()

loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True, key="loot")
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True, key="chest")

TARGET_GUILD = "I The Flying Dutchman I"

if loot_files and chest_files:
    try:
        # 1. PROCESS LOOT (With Improved De-duplication)
        all_loot = []
        for f in loot_files:
            df = robust_read(f)
            c_item = find_best_column(df, ['itemname', 'item'])
            c_qty = find_best_column(df, ['quantity', 'qty', 'amount'])
            c_name = find_best_column(df, ['lootedbyname', 'looter', 'player'])
            c_guild = find_best_column(df, ['lootedbyguild', 'guild'])
            c_time = find_best_column(df, ['timestamputc', 'date', 'time'])
            
            if c_item and c_qty:
                df = df.rename(columns={c_item: 'item_name', c_qty: 'quantity', c_name: 'player', c_guild: 'guild', c_time: 'time'})
                all_loot.append(df)
        
        # KEY FIX: Deduplicate based on time + player + item_name
        # This prevents double counting across different uploaders
        loot_df = pd.concat(all_loot).drop_duplicates(subset=['time', 'player', 'item_name', 'quantity'])
        loot_df = loot_df[loot_df['guild'] == TARGET_GUILD]

        # 2. PROCESS CHEST
        all_chest = []
        for f in chest_files:
            df = robust_read(f)
            c_item_ch = find_best_column(df, ['item', 'itemname'])
            c_qty_ch = find_best_column(df, ['amount', 'quantity', 'totalinchest'])
            c_user_ch = find_best_column(df, ['player', 'user', 'name', 'looter'])
            if c_item_ch and c_qty_ch:
                df = df.rename(columns={c_item_ch: 'Item', c_qty_ch: 'Amount', c_user_ch: 'ChestPlayer'})
                all_chest.append(df)
        
        chest_full_df = pd.concat(all_chest)
        chest_totals = chest_full_df.groupby('Item')['Amount'].sum().to_dict()
        chest_player_totals = chest_full_df.groupby(['Item', 'ChestPlayer'])['Amount'].sum().reset_index()

        # 3. INTERFACE TABS
        tab1, tab2 = st.tabs([T["tab_full"], T["tab_player"]])

        with tab1:
            l_sum = loot_df.groupby('item_name').agg({'quantity':'sum', 'player': lambda x: ', '.join(sorted(set(x)))}).reset_index()
            l_sum['In_Chest'] = l_sum['item_name'].map(chest_totals).fillna(0)
            l_sum['Miss'] = l_sum['quantity'] - l_sum['In_Chest']
            full_res = l_sum[l_sum['Miss'] > 0]
            st.dataframe(full_res[['item_name', 'quantity', 'In_Chest', 'Miss', 'player']].rename(columns={'item_name':T["item_col"], 'quantity':T["looted_col"], 'In_Chest':T["chest_col"], 'Miss':T["miss_col"], 'player':T["by_col"]}), use_container_width=True, hide_index=True)

        with tab2:
            search_query = st.text_input(T["search_label"], "").strip()
            if search_query:
                p_loot_summary = loot_df.groupby(['item_name', 'player'])['quantity'].sum().reset_index()
                specific_player = p_loot_summary[p_loot_summary['player'].str.contains(search_query, case=False)]
                
                if not specific_player.empty:
                    def check_personal_deposit(row):
                        item, p_name, looted_qty = row['item_name'], row['player'], row['quantity']
                        match = chest_player_totals[(chest_player_totals['Item'] == item) & (chest_player_totals['ChestPlayer'].str.contains(p_name, case=False, na=False))]
                        deposited_qty = match['Amount'].sum() if not match.empty else 0
                        if deposited_qty >= looted_qty: return T["banked"]
                        return f"{T['missing']} ({looted_qty - deposited_qty} left)"

                    specific_player[T["status_col"]] = specific_player.apply(check_personal_deposit, axis=1)
                    specific_player[T["audit_col"]] = "Pending"
                    st.data_editor(
                        specific_player[['item_name', 'quantity', T["status_col"], T["audit_col"]]].rename(columns={'item_name':T["item_col"], 'quantity':T["looted_col"]}),
                        use_container_width=True, hide_index=True,
                        disabled=[T["item_col"], T["looted_col"], T["status_col"]],
                        column_config={T["audit_col"]: st.column_config.SelectboxColumn(options=["Pending", "Confirmed Died", "Banked Later", "Excused"])}
                    )
                else:
                    st.warning(f"No guild member found matching '{search_query}'.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info(f"🛡️ Waiting for {TARGET_GUILD} logs...")
