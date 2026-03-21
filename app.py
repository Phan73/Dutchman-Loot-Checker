import streamlit as st
import pandas as pd
import re
import io

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")

# --- 2. LANGUAGE DICTIONARY (WITH FULL INSTRUCTIONS) ---
LANGS = {
    "한국어": {
        "title": "🛡️ 길드 전리품 감사 도구 (Flying Dutchman 독점)",
        "sidebar_head": "1. 설정 및 업로드",
        "loot_label": "전리품 로그 업로드 (.txt)",
        "chest_label": "창고 로그 업로드 (CSV 또는 복사본 TXT)",
        "tab_full": "전체 리포트 (Full Report)",
        "tab_player": "개별 감사 (Player Audit)",
        "tab_history": "창고 입고 내역 (Chest History)",
        "search_label": "👤 감사할 플레이어 (Looter)",
        "trade_label": "🤝 아이템을 대신 받은 사람 (Officer/Caller)",
        "reset_btn": "모든 데이터 초기화 (Reset)",
        "item_col": "아이템 이름",
        "looted_col": "획득량",
        "chest_col": "창고 입고됨",
        "miss_col": "누락됨",
        "by_col": "획득자 명단",
        "status_col": "개인 상태",
        "audit_col": "수동 체크 (사망/거래)",
        "banked": "✅ 입고됨",
        "missing": "❌ 미입고",
        "instruction_head": "📖 상세 사용 방법 (Usage Guide)",
        "instructions": """
        ### 📋 감사 도구 사용 가이드
        1. **전리품 로그 내보내기:** Albion Loot Logger를 사용하여 데이터를 `.txt` 파일로 저장하세요.
        2. **창고 로그 내보내기 (두 가지 방법):**
            * **방법 A (복사-붙여넣기):** 게임 내 로그를 드래그하여 복사한 후 메모장(`.txt`)에 붙여넣어 저장하세요.
            * **방법 B (Excel):** 엑셀을 사용 중이라면 `.csv` 형식으로 저장하여 업로드하세요.
        3. **파일 업로드:** 사이드바에 **모든** 전리품 로그와 창고 로그를 드래그 앤 드롭 하세요.
        4. **자동 정리:** 이 버전은 로그에 길드 이름이 누락되거나 시간 오차가 있어도 중복 계산을 자동으로 방지합니다.
        5. **결과 확인:** **I The Flying Dutchman I** 길드원이 획득한 아이템만 표시됩니다.
        6. **다국어 지원 (New):** 한국어 클라이언트 사용자와 영어 사용자 로그가 섞여도 자동으로 아이템 이름을 매칭합니다.
        7. **거래 확인:** '개별 감사' 탭에서 오피서 이름을 입력하면 누락된 템이 오피서 창고에 있는지 확인합니다.
        """
    },
    "English": {
        "title": "🛡️ Guild Loot Auditor (Flying Dutchman Exclusive)",
        "sidebar_head": "1. Settings & Upload",
        "loot_label": "Upload Loot Logs (.txt)",
        "chest_label": "Upload Chest Logs (CSV or Copy-Paste TXT)",
        "tab_full": "Full Report",
        "tab_player": "Player Audit",
        "tab_history": "Chest History",
        "search_label": "👤 Search Looter Name",
        "trade_label": "🤝 Officer Name (Single Entry)",
        "reset_btn": "Clear All Data",
        "item_col": "Item Name",
        "looted_col": "Looted Qty",
        "chest_col": "In Chests",
        "miss_col": "Missing",
        "by_col": "Looted By",
        "status_col": "Looter Status",
        "audit_col": "Manual Audit (Died/Traded)",
        "banked": "✅ Banked",
        "missing": "❌ Missing",
        "instruction_head": "📖 Detailed Instructions",
        "instructions": """
        ### 📋 How to use the Audit Tool
        1. **Export Loot Logs:** Use your Albion Loot Logger to export the loot data as a `.txt` file.
        2. **Export Chest Logs (Two supported methods):**
            * **Method A (Copy-Paste):** Highlight the logs inside the game, copy them, and paste them into a standard Notepad (`.txt`) file.
            * **Method B (Excel):** If you use Excel to organize logs, save the file as a `.csv` format before uploading.
        3. **Upload Files:** Drag and drop **all** your loot logs and chest logs into the sidebar.
        4. **Automatic Cleanup:** This version fixes double counting even if one log file is missing guild names or has time offsets.
        5. **Cross-Language Support (New):** Automatically matches items between Korean and English game clients (e.g., Cabbage Soup = 양배추 스프).
        6. **Trade Verification:** In the 'Player Audit' tab, enter the Officer's name to automatically verify if missing items were banked by them.
        7. **Manual Audit:** Use the dropdown in the 'Manual Audit' column to mark if a player died or traded the item manually.
        """
    }
}

sel_lang = st.sidebar.selectbox("🌐 Language", list(LANGS.keys()))
T = LANGS[sel_lang]

st.title(T["title"])
with st.expander(T["instruction_head"], expanded=False):
    st.markdown(T["instructions"])

# --- 3. TRANSLATION MAP ---
TRANSLATION_MAP = {
    "양배추 스프": "Cabbage Soup",
    "대형 채집 포션": "Major Gathering Potion",
    "고스트 헴프": "Ghost Hemp",
    "희귀한 루나이트 광석": "Uncommon Runite Ore",
    "매우 희귀한 루나이트 광석": "Exceptional Runite Ore"
}

def standardize(item_name):
    if not isinstance(item_name, str): return item_name
    return TRANSLATION_MAP.get(item_name.strip(), item_name.strip())

# --- 4. HELPERS ---
def get_tier_equiv(item_id):
    if not isinstance(item_id, str) or not item_id: return 0
    t_match = re.search(r'T(\d)', item_id)
    e_match = re.search(r'@(\d)', item_id)
    tier = int(t_match.group(1)) if t_match else 0
    enchant = int(e_match.group(1)) if e_match else 0
    return tier + enchant

def simplify_col(text):
    return re.sub(r'[^a-z0-9가-힣]', '', str(text).lower())

def find_best_column(df, targets):
    for col in df.columns:
        if simplify_col(col) in [simplify_col(t) for t in targets]:
            return col
    return None

def robust_read(file):
    raw_data = file.read()
    try: content = raw_data.decode('utf-8-sig')
    except: content = raw_data.decode('latin1')
    
    df = None
    if '\t' in content: 
        df = pd.read_csv(io.StringIO(content), sep='\t', engine='python', on_bad_lines='skip', quotechar='"')
    else:
        for sep in [';', ',']:
            temp_df = pd.read_csv(io.StringIO(content), sep=sep, engine='python', on_bad_lines='skip')
            if len(temp_df.columns) > 1:
                df = temp_df
                break
    
    if df is not None:
        df.columns = [str(c).replace('"', '').strip() for c in df.columns]
        return df
    return pd.read_csv(io.StringIO(content), engine='python')

# --- 5. SIDEBAR & LOGIC ---
st.sidebar.header("⚙️ Filters")
min_tier = st.sidebar.slider("Min Tier Equivalent", 1, 12, 4)

if st.sidebar.button(T["reset_btn"]):
    st.cache_data.clear()
    st.rerun()

loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True)
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True)

TARGET_GUILD = "I The Flying Dutchman I"

if loot_files and chest_files:
    try:
        # 1. PROCESS LOOT
        all_loot = []
        for f in loot_files:
            df = robust_read(f)
            c_item = find_best_column(df, ['itemname', 'item', '아이템', '이름'])
            c_qty = find_best_column(df, ['quantity', 'qty', 'amount', '수량'])
            c_name = find_best_column(df, ['lootedbyname', 'looter', 'player', '플레이어'])
            c_id = find_best_column(df, ['item_id', 'itemid', 'id'])
            c_time = find_best_column(df, ['timestamputc', 'date', 'time'])
            
            if c_item and c_qty:
                df = df.rename(columns={c_item: 'item_name', c_qty: 'quantity', c_name: 'player', c_time: 'time', c_id: 'item_id'})
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
                df['match_name'] = df['item_name'].apply(standardize)
                df['time'] = pd.to_datetime(df['time'], errors='coerce')
                all_loot.append(df)
        
        full_loot = pd.concat(all_loot)
        is_duplicate = ((full_loot['player'] == full_loot['player'].shift()) & (full_loot['match_name'] == full_loot['match_name'].shift()) & (full_loot['time'].diff().dt.total_seconds().abs() < 20))
        loot_df = full_loot[~is_duplicate].copy()
        loot_df['tier_equiv'] = loot_df['item_id'].apply(get_tier_equiv)
        loot_df = loot_df[loot_df['tier_equiv'] >= min_tier]

        # 2. PROCESS CHEST
        all_chest = []
        for f in chest_files:
            df = robust_read(f)
            c_item_ch = find_best_column(df, ['item', 'itemname', '아이템'])
            c_qty_ch = find_best_column(df, ['amount', 'quantity', '수량'])
            c_user_ch = find_best_column(df, ['player', 'user', 'name', '사용자'])
            if c_item_ch and c_qty_ch:
                df = df.rename(columns={c_item_ch: 'Item', c_qty_ch: 'Amount', c_user_ch: 'ChestPlayer'})
                df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0).astype(int)
                df['match_name'] = df['Item'].apply(standardize)
                all_chest.append(df)
        
        chest_df = pd.concat(all_chest)
        chest_totals = chest_df.groupby('match_name')['Amount'].sum().to_dict()
        chest_player_totals = chest_df.groupby(['match_name', 'ChestPlayer'])['Amount'].sum().reset_index()

        # DROPDOWN LISTS
        looter_list = sorted(loot_df['player'].dropna().unique().tolist())
        banker_list = sorted(chest_df['ChestPlayer'].dropna().unique().tolist())

        # 3. TABS
        tab1, tab2, tab3 = st.tabs([T["tab_full"], T["tab_player"], T["tab_history"]])

        with tab1:
            l_sum = loot_df.groupby('item_name').agg({'quantity':'sum', 'match_name': 'first', 'player': lambda x: ', '.join(sorted(set(x)))}).reset_index()
            l_sum['In_Chest'] = l_sum['match_name'].map(chest_totals).fillna(0)
            l_sum['Miss'] = l_sum['quantity'] - l_sum['In_Chest']
            st.dataframe(l_sum[l_sum['Miss'] > 0].rename(columns={'item_name': T["item_col"], 'quantity': T["looted_col"], 'In_Chest': T["chest_col"], 'Miss': T["miss_col"], 'player': T["by_col"]}), use_container_width=True, hide_index=True)

        with tab2:
            ca, cb = st.columns(2)
            search_p = ca.selectbox(T["search_label"], options=looter_list, index=None)
            trade_name = cb.selectbox(T["trade_label"], options=banker_list, index=None)
            
            if search_p:
                p_sum = loot_df[loot_df['player'] == search_p].groupby(['match_name', 'item_name'])['quantity'].sum().reset_index()
                audit_rows = []
                for _, row in p_sum.iterrows():
                    in_bank = int(chest_df[(chest_df['ChestPlayer'] == search_p) & (chest_df['match_name'] == row['match_name'])]['Amount'].sum())
                    looted_qty = int(row['quantity'])
                    v_status = "---"
                    if in_bank < looted_qty and trade_name:
                        off_bank = int(chest_df[(chest_df['ChestPlayer'] == trade_name) & (chest_df['match_name'] == row['match_name'])]['Amount'].sum())
                        v_status = f"✅ Banked by {trade_name}" if off_bank >= (looted_qty - in_bank) else f"❌ Missing"
                    
                    audit_rows.append({
                        T["item_col"]: row['item_name'], T["looted_col"]: looted_qty, 
                        T["status_col"]: T["banked"] if in_bank >= looted_qty else T["missing"], 
                        "Trade Verification": v_status, T["audit_col"]: "None"
                    })
                st.data_editor(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True, column_config={T["audit_col"]: st.column_config.SelectboxColumn(options=["None", "Died", "Traded", "Penalty"])})

        with tab3:
            search_hist = st.selectbox(T["search_label"], options=banker_list, index=None, key="hist")
            if search_hist:
                st.dataframe(chest_df[chest_df['ChestPlayer'] == search_hist][['Item', 'Amount']].sort_values(by='Item'), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")
