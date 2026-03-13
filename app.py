
sel_lang = st.sidebar.selectbox("🌐 Language", list(LANGS.keys()))
T = LANGS[sel_lang]

st.title(T["title"])

# --- HELPERS ---
def get_tier_equiv(item_id):
    if not isinstance(item_id, str) or not item_id: return 0
    t_match = re.search(r'T(\d)', item_id)
    e_match = re.search(r'@(\d)', item_id)
    tier = int(t_match.group(1)) if t_match else 0
    enchant = int(e_match.group(1)) if e_match else 0
    return tier + enchant

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

# --- SIDEBAR ---
st.sidebar.header("⚙️ Filters")
min_tier = st.sidebar.slider("Min Tier Equivalent", 1, 12, 4)
show_mounts = st.sidebar.checkbox("Include Mounts", True)
show_consumables = st.sidebar.checkbox("Include Food/Potions", True)

if st.sidebar.button(T["reset_btn"]):
    st.cache_data.clear()
    st.rerun()

loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True)
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True)

TARGET_GUILD = "I The Flying Dutchman I"

if loot_files and chest_files:
    try:
        # 1. PROCESS LOOT
        processed_dfs = []
        for f in loot_files:
            df = robust_read(f)
            c_item = find_best_column(df, ['itemname', 'item'])
            c_id = find_best_column(df, ['itemid', 'id', 'item_id'])
            c_qty = find_best_column(df, ['quantity', 'qty', 'amount'])
            c_name = find_best_column(df, ['lootedbyname', 'looter', 'player'])
            c_guild = find_best_column(df, ['lootedbyguild', 'guild'])
            c_time = find_best_column(df, ['timestamputc', 'date', 'time'])
            
            if c_item and c_qty:
                rename_map = {c_item: 'item_name', c_qty: 'quantity', c_name: 'player', c_time: 'time'}
                if c_id: rename_map[c_id] = 'item_id'
                if c_guild: rename_map[c_guild] = 'guild'
                df = df.rename(columns=rename_map)
                if 'item_id' not in df.columns: df['item_id'] = "" # Anti-KeyError Fix
                df['time'] = pd.to_datetime(df['time'], errors='coerce')
                processed_dfs.append(df)
        
        if not processed_dfs: st.stop()
        full_loot = pd.concat(processed_dfs, ignore_index=True).sort_values(by=['player', 'item_name', 'time'])
        is_duplicate = ((full_loot['player'] == full_loot['player'].shift()) & (full_loot['item_name'] == full_loot['item_name'].shift()) & (full_loot['time'].diff().dt.total_seconds().abs() < 20))
        loot_df = full_loot[~is_duplicate].copy()
        
        if 'guild' in loot_df.columns:
            loot_df = loot_df[loot_df['guild'].fillna(TARGET_GUILD) == TARGET_GUILD]

        loot_df['tier_equiv'] = loot_df['item_id'].apply(get_tier_equiv)
        loot_df = loot_df[loot_df['tier_equiv'] >= min_tier]
        if not show_mounts: loot_df = loot_df[~loot_df['item_id'].str.contains('MOUNT', na=False)]
        if not show_consumables: loot_df = loot_df[~loot_df['item_id'].str.contains('POTION|MEAL|FOOD', na=False, case=False)]

        # 2. PROCESS CHEST
        all_chest = []
        for f in chest_files:
            df = robust_read(f)
            c_item_ch = find_best_column(df, ['item', 'itemname'])
            c_qty_ch = find_best_column(df, ['amount', 'quantity', 'totalinchest'])
            c_user_ch = find_best_column(df, ['player', 'user', 'name', 'looter'])
            c_time_ch = find_best_column(df, ['time', 'date', 'timestamp'])
            if c_item_ch and c_qty_ch:
                df = df.rename(columns={c_item_ch: 'Item', c_qty_ch: 'Amount', c_user_ch: 'ChestPlayer', c_time_ch: 'ChestTime'})
                all_chest.append(df)
        
        chest_full_df = pd.concat(all_chest)
        chest_totals = chest_full_df.groupby('Item')['Amount'].sum().to_dict()
        chest_player_totals = chest_full_df.groupby(['Item', 'ChestPlayer'])['Amount'].sum().reset_index()

        # 3. INTERFACE
        tab1, tab2, tab3 = st.tabs([T["tab_full"], T["tab_player"], T["tab_history"]])

        with tab1:
            l_sum = loot_df.groupby('item_name').agg({'quantity':'sum', 'player': lambda x: ', '.join(sorted(set(x)))}).reset_index()
            l_sum['In_Chest'] = l_sum['item_name'].map(chest_totals).fillna(0)
            l_sum['Miss'] = l_sum['quantity'] - l_sum['In_Chest']
            report_df = l_sum[l_sum['Miss'] > 0].copy()
            if not report_df.empty:
                # Use the restored dictionary keys here
                report_df = report_df.rename(columns={
                    'item_name': T["item_col"], 
                    'quantity': T["looted_col"], 
                    'In_Chest': T["chest_col"], 
                    'Miss': T["miss_col"], 
                    'player': T["by_col"]
                })
                st.dataframe(report_df, use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("🔍 Individual Audit & Manual Check")
            ca, cb = st.columns(2)
            search_p = ca.text_input(T["search_label"], key="p_audit_s").strip()
            trade_name = cb.text_input(T["trade_label"], key="global_t_n").strip()
            
            if search_p:
                p_sum = loot_df.groupby(['item_name', 'player'])['quantity'].sum().reset_index()
                spec_p = p_sum[p_sum['player'].str.contains(search_p, case=False, na=False)].copy()
                if not spec_p.empty:
                    audit_rows = []
                    for _, row in spec_p.iterrows():
                        m = chest_player_totals[(chest_player_totals['Item'] == row['item_name']) & (chest_player_totals['ChestPlayer'].str.contains(row['player'], case=False, na=False))]
                        lb = m['Amount'].sum() if not m.empty else 0
                        is_missing = lb < row['quantity']
                        
                        v_status = "---"
                        if is_missing and trade_name:
                            t_m = chest_player_totals[(chest_player_totals['Item'] == row['item_name']) & (chest_player_totals['ChestPlayer'].str.contains(trade_name, case=False, na=False))]
                            if t_m['Amount'].sum() >= (row['quantity'] - lb):
                                v_status = f"✅ Banked by {trade_name}"
                            else:
                                v_status = f"❌ Missing from {trade_name}"
                        
                        audit_rows.append({
                            T["item_col"]: row['item_name'],
                            T["looted_col"]: row['quantity'],
                            T["status_col"]: T["banked"] if not is_missing else T["missing"],
                            "Trade Verification": v_status,
                            T["audit_col"]: "None" 
                        })
                    
                    # INTERACTIVE DATA EDITOR
                    st.data_editor(
                        pd.DataFrame(audit_rows),
                        column_config={
                            T["audit_col"]: st.column_config.SelectboxColumn(
                                T["audit_col"],
                                options=["None", "Died (Executed)", "Traded (Manual)", "Penalty"],
                                required=True,
                            )
                        },
                        disabled=[T["item_col"], T["looted_col"], T["status_col"], "Trade Verification"],
                        hide_index=True,
                        use_container_width=True,
                        key="player_manual_editor"
                    )

        with tab3:
            search_hist = st.text_input(T["search_label"], key="h_audit_s").strip()
            if search_hist:
                history = chest_full_df[chest_full_df['ChestPlayer'].str.contains(search_hist, case=False, na=False)]
                if not history.empty:
                    st.dataframe(history[['ChestTime', 'Item', 'Amount']].sort_values(by='ChestTime', ascending=False), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")
