import streamlit as st
import pandas as pd
import re
import io

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")

# --- 2. LANGUAGE DICTIONARY ---
LANGS = {
    "한국어": {
        "title": "🛡️ 길드 전리품 감사 도구 (Flying Dutchman 독점)",
        "sidebar_head": "1. 설정 및 업로드",
        "loot_label": "전리품 로그 업로드 (.txt)",
        "chest_label": "창고 로그 업로드 (CSV 또는 복사본 TXT)",
        "second_guild": "➕ 2번째 길드 추가 (자동완성)",
        "tab_full": "전체 리포트 (Full Report)",
        "tab_player": "개별 감사 (Player Audit)",
        "tab_history": "창고 입고 내역 (Chest History)",
        "tab_ledger": "📦 창고 종합 장부 (Global Ledger)", 
        "search_label": "👤 감사할 플레이어 (Looter)",
        "ledger_search": "🔍 장부 검색 (Player Ledger Search)", 
        "trade_label": "🤝 아이템을 대신 받은 사람 (Officer/Caller 다중선택)",
        "reset_btn": "모든 데이터 초기화 (Reset)",
        "item_col": "아이템 이름",
        "guild_col": "소속 길드", 
        "looted_col": "수량",
        "chest_col": "창고 입고됨",
        "miss_col": "누락됨",
        "by_col": "획득자 명단",
        "status_col": "개인 상태",
        "audit_col": "수동 체크 (사망/거래)",
        "chest_name_col": "창고 / 파일 이름", 
        "action_col": "작업 (Action)", 
        "time_col": "시간 (Time)", 
        "total_dep": "총 입금액", 
        "total_with": "총 출금액", 
        "net_change": "순 변동량", 
        "banked": "✅ 본인 입고",
        "missing": "❌ 미입고",
        "req_both": "⚠️ 이 기능을 사용하려면 **전리품 로그**와 **창고 로그**가 모두 필요합니다.",
        "req_chest": "⚠️ 이 기능을 사용하려면 올바른 형식의 **창고 로그**를 업로드하세요.",
        "instruction_head": "📖 상세 사용 방법 (Usage Guide)",
        "instructions": """
        ### 📋 감사 도구 사용 가이드
        1. **전리품 로그 내보내기:** Albion Loot Logger를 사용하여 데이터를 `.txt` 파일로 저장하세요.
        2. **창고 로그 내보내기:** 게임 내 로그를 드래그하여 복사하거나 엑셀(.csv)로 저장하여 업로드하세요. 다수의 창고 로그를 동시에 업로드할 수 있습니다.
        3. **독립적 사용 가능:** 창고 로그만 업로드하여 '종합 장부' 기능만 단독으로 사용할 수도 있습니다.
        4. **자동 정리:** 로그에 길드 이름이 누락되거나 시간 오차가 있어도 중복 계산을 자동으로 방지합니다.
        5. **다국어 지원:** 한국어 클라이언트 사용자와 영어 사용자 로그가 섞여도 자동으로 아이템 이름을 매칭합니다.
        6. **종합 장부:** '창고 종합 장부' 탭에서 특정 플레이어를 검색하면, 여러 창고에서 아이템을 넣고 뺀 모든 기록과 통계를 확인할 수 있습니다.
        """
    },
    "English": {
        "title": "🛡️ Guild Loot Auditor (Flying Dutchman Exclusive)",
        "sidebar_head": "1. Settings & Upload",
        "loot_label": "Upload Loot Logs (.txt)",
        "chest_label": "Upload Chest Logs (CSV or Copy-Paste TXT)",
        "second_guild": "➕ Add 2nd Guild (Auto-fill)",
        "tab_full": "Full Report",
        "tab_player": "Player Audit",
        "tab_history": "Chest History",
        "tab_ledger": "📦 Global Chest Ledger", 
        "search_label": "👤 Search Looter Name",
        "ledger_search": "🔍 Search Player Ledger", 
        "trade_label": "🤝 Officer Names (Multiple Selection)",
        "reset_btn": "Clear All Data",
        "item_col": "Item Name",
        "guild_col": "Guild", 
        "looted_col": "Quantity",
        "chest_col": "In Chests",
        "miss_col": "Missing",
        "by_col": "Looted By",
        "status_col": "Looter Status",
        "audit_col": "Manual Audit (Died/Traded)",
        "chest_name_col": "Chest / File Name", 
        "action_col": "Action", 
        "time_col": "Time", 
        "total_dep": "Total Deposited", 
        "total_with": "Total Withdrawn", 
        "net_change": "Net Item Change", 
        "banked": "✅ Self Banked",
        "missing": "❌ Missing",
        "req_both": "⚠️ Both **Loot Logs** and **Chest Logs** are required to view this section.",
        "req_chest": "⚠️ Please upload a valid **Chest Log** to view this section.",
        "instruction_head": "📖 Detailed Instructions",
        "instructions": """
        ### 📋 How to use the Audit Tool
        1. **Export Loot Logs:** Use your Albion Loot Logger to export the loot data as a `.txt` file.
        2. **Export Chest Logs:** Highlight the logs inside the game, copy them, and paste them into a `.txt` file, or use `.csv`. You can upload logs from multiple different chests at once.
        3. **Standalone Chest Mode:** You can now upload *only* chest logs if you just want to use the Global Ledger to check who took what.
        4. **Automatic Cleanup:** This version fixes double counting even if one log file is missing guild names or has time offsets.
        5. **Cross-Language Support:** Automatically matches items between Korean and English game clients.
        6. **Global Ledger:** Use the 'Global Chest Ledger' tab to search for a specific player and see exactly what they deposited or withdrawn across ALL uploaded chests, complete with a stat summary.
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

if loot_files or chest_files:
    try:
        loot_df = pd.DataFrame()
        chest_df = pd.DataFrame()

        # --- PROCESS LOOT ---
        if loot_files:
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
                    if c_gd: temp = temp.rename(columns={c_gd: 'guild'})
                    else: temp['guild'] = TARGET_GUILD

                    temp['qty'] = pd.to_numeric(temp['qty'], errors='coerce').fillna(0).astype(int)
                    temp['match_name'] = temp['item_raw'].apply(standardize) + " ." + temp['item_id'].apply(get_enchant_val)
                    temp['tier_equiv'] = temp['item_id'].apply(get_tier_equiv)
                    temp['time'] = pd.to_datetime(temp['time'], errors='coerce').dt.round(buffer_str)
                    all_loot.append(temp)
                else:
                    st.sidebar.error(f"⚠️ Could not detect required columns (Item, Quantity) in Loot File: {f.name}")
            
            if all_loot:
                full_raw_loot = pd.concat(all_loot, ignore_index=True)
                available_guilds = sorted([g for g in full_raw_loot['guild'].dropna().unique() if str(g).strip() != "" and TARGET_GUILD.lower() not in str(g).lower()])
                
                default_index = None
                for i, guild_name in enumerate(available_guilds):
                    if "the flying dutchman" in str(guild_name).lower():
                        default_index = i
                        break
                
                second_guild = st.sidebar.selectbox(T["second_guild"], options=available_guilds, index=default_index)

                if second_guild:
                    pattern = f"({TARGET_GUILD}|{re.escape(second_guild)})"
                    full_raw_loot = full_raw_loot[full_raw_loot['guild'].astype(str).str.contains(pattern, na=False, case=False)].copy()
                else:
                    full_raw_loot = full_raw_loot[full_raw_loot['guild'].astype(str).str.contains(TARGET_GUILD, na=False, case=False)].copy()
                
                loot_df = full_raw_loot.groupby(['time', 'player', 'match_name', 'tier_equiv', 'guild'], as_index=False)['qty'].max()
                loot_df = loot_df[loot_df['tier_equiv'] >= min_tier]

        # --- PROCESS CHEST ---
        if chest_files:
            all_chest = []
            for f in chest_files:
                df = robust_read(f)
                # ADDED BROAD SYNONYMS FOR CHEST COLUMNS SO IT CATCHES EVERYTHING
                c_it = find_best_column(df, ['item', 'itemname', '아이템'])
                c_am = find_best_column(df, ['amount', 'quantity', 'qty', '수량'])
                c_pl = find_best_column(df, ['player', 'user', 'name', 'character', '플레이어', '캐릭터', '이름'])
                c_en = find_best_column(df, ['enchantment', '인챈트'])
                c_ac = find_best_column(df, ['action', 'type', '동작', '작업', '유형']) 
                c_tm = find_best_column(df, ['date', 'time', 'timestamputc', '시간', '날짜']) 
                
                if c_it and c_am:
                    df = df.rename(columns={c_it:'item_raw', c_am:'qty', c_pl:'player'})
                    ench_col = pd.to_numeric(df[c_en], errors='coerce').fillna(0).astype(int) if c_en else 0
                    df['match_name'] = df['item_raw'].apply(standardize) + " ." + ench_col.astype(str)
                    
                    df['chest_name'] = f.name 
                    
                    if c_tm: df = df.rename(columns={c_tm: 'time'})
                    else: df['time'] = 'Unknown Time'

                    if c_ac:
                        is_withdraw = df[c_ac].astype(str).str.contains('with|출', case=False, na=False)
                        df['action'] = ['Withdraw' if w else 'Deposit' for w in is_withdraw]
                    else:
                        df['action'] = 'Deposit'
                        
                    df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(0).astype(int)
                    all_chest.append(df)
                else:
                    st.sidebar.error(f"⚠️ Could not detect required columns (Item, Amount) in Chest File: {f.name}. Make sure it's exported correctly.")
            
            if all_chest:
                chest_df = pd.concat(all_chest, ignore_index=True)

        # --- UI TABS ---
        tab1, tab2, tab3, tab4 = st.tabs([T["tab_full"], T["tab_player"], T["tab_history"], T["tab_ledger"]])
        
        deposits_only = pd.DataFrame()
        chest_totals = {}
        if not chest_df.empty:
            deposits_only = chest_df[chest_df['action'] == 'Deposit']
            chest_totals = deposits_only.groupby('match_name')['qty'].sum().to_dict()

        with tab1:
            if loot_df.empty or chest_df.empty:
                st.info(T["req_both"])
            else:
                l_sum = loot_df.groupby('match_name').agg({'qty':'sum', 'player': lambda x: ', '.join(set(x)), 'guild': lambda x: ', '.join(set(x))}).reset_index()
                l_sum['In Chest'] = l_sum['match_name'].map(chest_totals).fillna(0)
                l_sum['Miss'] = l_sum['qty'] - l_sum['In Chest']
                
                report_df = l_sum[l_sum['Miss'] > 0].sort_values('Miss', ascending=False).rename(columns={
                    'match_name': T["item_col"], 'qty': T["looted_col"], 'guild': T["guild_col"],
                    'player': T["by_col"], 'In Chest': T["chest_col"], 'Miss': T["miss_col"]
                })
                st.dataframe(report_df, use_container_width=True, hide_index=True)

        with tab2:
            if loot_df.empty or chest_df.empty:
                st.info(T["req_both"])
            else:
                ca, cb = st.columns(2)
                search_p = ca.selectbox(T["search_label"], options=sorted(loot_df['player'].dropna().unique()), index=None)
                trade_names = cb.multiselect(T["trade_label"], options=sorted(chest_df['player'].dropna().unique()))
                
                if search_p:
                    p_loot = loot_df[loot_df['player'] == search_p].groupby('match_name').agg({'qty':'sum', 'guild':'first'}).reset_index()
                    audit_rows = []
                    for _, row in p_loot.iterrows():
                        in_bank = int(deposits_only[(deposits_only['player'] == search_p) & (deposits_only['match_name'] == row['match_name'])]['qty'].sum())
                        v_status, is_accounted = "---", (in_bank >= row['qty'])
                        
                        if not is_accounted and trade_names:
                            off_matches = deposits_only[(deposits_only['player'].isin(trade_names)) & (deposits_only['match_name'] == row['match_name']) & (deposits_only['qty'] > 0)].groupby('player')['qty'].sum()
                            if not off_matches.empty:
                                v_status = "✅ Team: " + ", ".join([f"{n} ({int(a)})" for n, a in off_matches.items()])
                                is_accounted = True
                            else: v_status = "❌ Not found in selection"
                        
                        audit_rows.append({
                            T["item_col"]: row['match_name'], T["guild_col"]: row['guild'], T["looted_col"]: row['qty'], 
                            "Own Bank": in_bank, T["status_col"]: T["banked"] if in_bank >= row['qty'] else T["missing"],
                            "Officer Match": v_status, T["audit_col"]: "None", "_sort_priority": 0 if is_accounted else 1
                        })
                    
                    audit_df = pd.DataFrame(audit_rows).sort_values("_sort_priority").drop(columns=["_sort_priority"])
                    st.data_editor(audit_df, use_container_width=True, hide_index=True, column_config={T["audit_col"]: st.column_config.SelectboxColumn(options=["None", "Died", "Traded", "Penalty"])})

        with tab3:
            if chest_df.empty:
                st.info(T["req_chest"])
            else:
                search_hist = st.selectbox(T["search_label"], options=sorted(chest_df['player'].dropna().unique()), index=None, key="hist_tab_search")
                if search_hist:
                    player_history = chest_df[chest_df['player'] == search_hist][['match_name', 'qty']].copy()
                    st.dataframe(player_history.sort_values('match_name'), use_container_width=True, hide_index=True)
                else: 
                    st.info("Select a player from the dropdown above to view their chest deposit history.")
        
        with tab4:
            if chest_df.empty:
                st.info(T["req_chest"])
            else:
                search_ledger = st.selectbox(T["ledger_search"], options=sorted(chest_df['player'].dropna().unique()), index=None)
                
                if search_ledger:
                    p_ledger = chest_df[chest_df['player'] == search_ledger].copy()
                    
                    dep_count = p_ledger[p_ledger['action'] == 'Deposit']['qty'].sum()
                    with_count = p_ledger[p_ledger['action'] == 'Withdraw']['qty'].sum()
                    net_count = dep_count - with_count
                    
                    m1, m2, m3 = st.columns(3)
                    m1.metric(T["total_dep"], f"{dep_count:,}")
                    m2.metric(T["total_with"], f"{with_count:,}")
                    m3.metric(T["net_change"], f"{net_count:,}")
                    
                    st.divider()
                    
                    ledger_display = p_ledger[['time', 'chest_name', 'action', 'match_name', 'qty']].sort_values('time', ascending=False)
                    st.dataframe(
                        ledger_display,
                        use_container_width=True, 
                        hide_index=True,
                        column_config={'time': T["time_col"], 'chest_name': T["chest_name_col"], 'action': T["action_col"], 'match_name': T["item_col"], 'qty': T["looted_col"]}
                    )
                else:
                    st.dataframe(
                        chest_df[['time', 'chest_name', 'player', 'action', 'match_name', 'qty']].sort_values('time', ascending=False),
                        use_container_width=True,
                        hide_index=True,
                        column_config={'time': T["time_col"], 'chest_name': T["chest_name_col"], 'player': T["by_col"], 'action': T["action_col"], 'match_name': T["item_col"], 'qty': T["looted_col"]}
                    )

    except Exception as e:
        st.error(f"Error processing files: {e}")
