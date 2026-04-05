import streamlit as st
import pandas as pd
import re
import io

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")

# --- 2. LANGUAGE DICTIONARY (FULLY RESTORED INSTRUCTIONS) ---
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
        "trade_label": "🤝 아이템을 대신 받은 사람 (Officer/Caller 다중선택)",
        "reset_btn": "모든 데이터 초기화 (Reset)",
        "item_col": "아이템 이름",
        "looted_col": "획득량",
        "chest_col": "창고 입고됨",
        "miss_col": "누락됨",
        "by_col": "획득자 명단",
        "status_col": "개인 상태",
        "audit_col": "수동 체크 (사망/거래)",
        "banked": "✅ 본인 입고",
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
        5. **결과 확인:** **I The Flying Dutchman I** 길드원이 획득한 아이템만 엄격하게 필터링되어 표시됩니다.
        6. **다국어 지원:** 한국어 클라이언트 사용자와 영어 사용자 로그가 섞여도 자동으로 아이템 이름을 매칭합니다.
        7. **거래 확인:** '개별 감사' 탭에서 오피서 이름을 입력하면 누락된 템이 오피서 창고에 있는지 확인합니다.
        8. **시간 버퍼 (New):** 사이드바의 Sync Window를 조절해 로거 간 핑 차이로 인한 중복을 방지하세요.
        9. **데이터 내보내기 (New):** 표 우측 상단의 아이콘을 눌러 검색(돋보기) 및 CSV 다운로드를 할 수 있습니다.
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
        "trade_label": "🤝 Officer Names (Multiple Selection)",
        "reset_btn": "Clear All Data",
        "item_col": "Item Name",
        "looted_col": "Looted Qty",
        "chest_col": "In Chests",
        "miss_col": "Missing",
        "by_col": "Looted By",
        "status_col": "Looter Status",
        "audit_col": "Manual Audit (Died/Traded)",
        "banked": "✅ Self Banked",
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
        5. **Guild Filter:** Strictly filters the logs so ONLY items looted by **I The Flying Dutchman I** members are shown.
        6. **Cross-Language Support:** Automatically matches items between Korean and English game clients (e.g., Cabbage Soup = 양배추 스프).
        7. **Trade Verification:** In the 'Player Audit' tab, enter the Officer's name to automatically verify if missing items were banked by them.
        8. **Custom Buffer (New):** Adjust the Sync Window in the sidebar to prevent double-counting from laggy logs.
        9. **Search & Export (New):** Hover over any table to search (magnifying glass) or download as CSV.
        """
    }
}
sel_lang = st.sidebar.selectbox("🌐 Language", list(LANGS.keys()))
T = LANGS[sel_lang]
st.title(T["title"])

with st.expander(T["instruction_head"], expanded=False):
    st.markdown(T["instructions"])

# --- 3. CONFIG & TRANSLATION MAP ---
TARGET_GUILD = "I The Flying Dutchman I"

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
def get_enchant_val(item_id):
    if not isinstance(item_id, str): return "0"
    match = re.search(r'@(\d)', item_id)
    return match.group(1) if match else "0"

def get_tier_equiv(item_id):
    if not isinstance(item_id, str) or not item_id: return 0
    t_match = re.search(r'T(\d)', item_id)
    e_match = re.search(r'@(\d)', item_id)
    tier = int(t_match.group(1)) if t_match else 0
    enchant = int(e_match.group(1)) if e_match else 0
    return tier + enchant

def find_best_column(df, targets):
    for col in df.columns:
        clean_col = re.sub(r'[^a-z0-9가-힣]', '', str(col).lower())
        if clean_col in [re.sub(r'[^a-z0-9가-힣]', '', t.lower()) for t in targets]:
            return col
    return None

def robust_read(file):
    raw_data = file.read()
    try: content = raw_data.decode('utf-8-sig')
    except: content = raw_data.decode('latin1')
    df = pd.read_csv(io.StringIO(content), sep=None, engine='python', on_bad_lines='skip')
    df.columns = [str(c).replace('"', '').strip() for c in df.columns]
    return df

# --- 5. SIDEBAR FILTERS ---
st.sidebar.header("⚙️ Settings")
min_tier = st.sidebar.slider("Min Tier Equivalent", 1, 12, 4)
buffer_val = st.sidebar.select_slider("Sync Window (Seconds)", options=[1, 2, 3, 5, 10], value=2)
buffer_str = f"{buffer_val}s"

loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True)
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True)

if loot_files and chest_files:
    try:
        # --- PROCESS LOOT ---
        all_loot = []
        for f in loot_files:
            df = robust_read(f)
            c_it = find_best_column(df, ['itemname', 'item', '아이템'])
            c_qty = find_best_column(df, ['quantity', 'qty', 'amount', '수량'])
            c_pl = find_best_column(df, ['lootedbyname', 'looter', 'player'])
            c_id = find_best_column(df, ['item_id', 'itemid'])
            c_tm = find_best_column(df, ['timestamputc', 'date', 'time'])
            c_gd = find_best_column(df, ['lootedbyguild', 'guild', '길드'])
            
            if c_it and c_qty and c_id:
                temp = df.rename(columns={c_it:'item_raw', c_qty:'qty', c_pl:'player', c_id:'item_id', c_tm:'time'}).copy()
                
                # Restore the exact Guild mapping logic
                if c_gd:
                    temp = temp.rename(columns={c_gd: 'guild'})
                else:
                    temp['guild'] = TARGET_GUILD

                temp['qty'] = pd.to_numeric(temp['qty'], errors='coerce').fillna(0).astype(int)
                
                # Apply standardization and .0 enchant forcing
                temp['match_name'] = temp['item_raw'].apply(standardize) + " ." + temp['item_id'].apply(get_enchant_val)
                temp['tier_equiv'] = temp['item_id'].apply(get_tier_equiv)
                
                # Apply dynamic time buffer for deduplication
                temp['time'] = pd.to_datetime(temp['time'], errors='coerce').dt.round(buffer_str)
                all_loot.append(temp)
        
        full_raw_loot = pd.concat(all_loot, ignore_index=True)
        
        # RESTORED: Strict Flying Dutchman Guild Filter
        full_raw_loot = full_raw_loot[full_raw_loot['guild'].astype(str).str.contains(TARGET_GUILD, na=False, case=False)].copy()
        
        # Deduplicate using the buffer window
        loot_df = full_raw_loot.groupby(['time', 'player', 'match_name', 'tier_equiv'], as_index=False)['qty'].max()
        loot_df = loot_df[loot_df['tier_equiv'] >= min_tier]

        # --- PROCESS CHEST ---
        all_chest = []
        for f in chest_files:
            df = robust_read(f)
            c_it = find_best_column(df, ['item', 'itemname'])
            c_am = find_best_column(df, ['amount', 'quantity'])
            c_pl = find_best_column(df, ['player', 'user', 'name'])
            c_en = find_best_column(df, ['enchantment'])
            
            if c_it and c_am:
                df = df.rename(columns={c_it:'item_raw', c_am:'qty', c_pl:'player'})
                ench_col = pd.to_numeric(df[c_en], errors='coerce').fillna(0).astype(int) if c_en else 0
                
                # Apply standardization and .0 enchant forcing
                df['match_name'] = df['item_raw'].apply(standardize) + " ." + ench_col.astype(str)
                all_chest.append(df)
        
        chest_df = pd.concat(all_chest, ignore_index=True)
        chest_totals = chest_df.groupby('match_name')['qty'].sum().to_dict()

        # --- UI TABS ---
        tab1, tab2, tab3 = st.tabs([T["tab_full"], T["tab_player"], T["tab_history"]])

        with tab1:
            l_sum = loot_df.groupby('match_name').agg({'qty':'sum', 'player': lambda x: ', '.join(set(x))}).reset_index()
            l_sum['In Chest'] = l_sum['match_name'].map(chest_totals).fillna(0)
            l_sum['Miss'] = l_sum['qty'] - l_sum['In Chest']
            
            # Using st.dataframe for Pro Table (Search / Download)
            st.dataframe(l_sum[l_sum['Miss'] > 0].sort_values('Miss', ascending=False), use_container_width=True, hide_index=True)

        with tab2:
            ca, cb = st.columns(2)
            search_p = ca.selectbox(T["search_label"], options=sorted(loot_df['player'].dropna().unique()), index=None)
            trade_names = cb.multiselect(T["trade_label"], options=sorted(chest_df['player'].dropna().unique()))
            
            if search_p:
                p_loot = loot_df[loot_df['player'] == search_p].groupby('match_name')['qty'].sum().reset_index()
                audit_rows = []
                for _, row in p_loot.iterrows():
                    # Check player's own bank
                    in_bank = int(chest_df[(chest_df['player'] == search_p) & (chest_df['match_name'] == row['match_name'])]['qty'].sum())
                    
                    v_status = "---"
                    is_accounted = (in_bank >= row['qty']) 
                    
                    # Check selected officers if missing from own bank
                    if not is_accounted and trade_names:
                        off_matches = chest_df[(chest_df['player'].isin(trade_names)) & (chest_df['match_name'] == row['match_name']) & (chest_df['qty'] > 0)].groupby('player')['qty'].sum()
                        if not off_matches.empty:
                            v_status = "✅ Team: " + ", ".join([f"{n} ({int(a)})" for n, a in off_matches.items()])
                            is_accounted = True 
                        else:
                            v_status = "❌ Not found in selection"
                    
                    audit_rows.append({
                        T["item_col"]: row['match_name'], 
                        T["looted_col"]: row['qty'], 
                        "Own Bank": in_bank,
                        T["status_col"]: T["banked"] if in_bank >= row['qty'] else T["missing"],
                        "Officer Match": v_status,
                        T["audit_col"]: "None",
                        "_sort_priority": 0 if is_accounted else 1 # Logic: 0 = Top, 1 = Bottom
                    })
                
                # Convert to DataFrame, sort by priority, then remove the hidden column
                audit_df = pd.DataFrame(audit_rows).sort_values("_sort_priority").drop(columns=["_sort_priority"])
                
                st.data_editor(
                    audit_df, 
                    use_container_width=True, 
                    hide_index=True, 
                    column_config={T["audit_col"]: st.column_config.SelectboxColumn(options=["None", "Died", "Traded", "Penalty"])}
                )

        with tab3:
            # RESTORED: Chest History Tab from earlier response
            search_hist = st.selectbox(
                T["search_label"], 
                options=sorted(chest_df['player'].dropna().unique()), 
                index=None, 
                key="hist_tab_search"
            )
            
            if search_hist:
                player_history = chest_df[chest_df['player'] == search_hist][['match_name', 'qty']].copy()
                player_history = player_history.sort_values('match_name')
                
                st.dataframe(
                    player_history, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "match_name": "Item Name",
                        "qty": "Quantity Deposited"
                    }
                )
            else:
                st.info("Select a player from the dropdown above to view their chest deposit history.")

    except Exception as e:
        st.error(f"Error processing files: {e}")
