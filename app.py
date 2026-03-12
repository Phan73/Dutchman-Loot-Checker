st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")
sel_lang = st.sidebar.selectbox("🌐 Language", list(LANGS.keys()))
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

# --- DATA RESET ---
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
            c_item = find_best_column(df, ['itemname', 'item'])
            c_qty = find_best_column(df, ['quantity', 'qty', 'amount'])
            c_name = find_best_column(df, ['lootedbyname', 'looter', 'player'])
            c_guild = find_best_column(df, ['lootedbyguild', 'guild'])
            c_time = find_best_column(df, ['timestamputc', 'date', 'time'])
            
            if c_item and c_qty:
                df = df.rename(columns={c_item: 'item_name', c_qty: 'quantity', c_name: 'player', c_guild: 'guild', c_time: 'time'})
                df['time'] = pd.to_datetime(df['time'], errors='coerce')
                all_loot.append(df)
        
        raw_loot = pd.concat(all_loot).dropna(subset=['time'])
        raw_loot = raw_loot[raw_loot['guild'] == TARGET_GUILD]

        # --- NEW FUZZY DE-DUPLICATION LOGIC ---
        # Sort so we can compare time differences between rows
        raw_loot = raw_loot.sort_values(by=['player', 'item_name', 'time'])
        
        # Identify duplicates: same player, same item, within 15 seconds of the previous record
        is_duplicate = (
            (raw_loot['player'] == raw_loot['player'].shift()) &
            (raw_loot['item_name'] == raw_loot['item_name'].shift()) &
            (raw_loot['time'].diff().dt.total_seconds() < 15)
        )
        loot_df = raw_loot[~is_duplicate].copy()

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

        # 3. INTERFACE
        tab1, tab2 = st.tabs([T["tab_full"], T["tab_player"]])

        with tab1:
            l_sum = loot_df.groupby('item_name').agg({'quantity':'sum', 'player': lambda x: ', '.join(sorted(set(x)))}).reset_index()
            l_sum['In_Chest'] = l_sum['item_name'].map(chest_totals).fillna(0)
            l_sum['Miss'] = l_sum['quantity'] - l_sum['In_Chest']
            st.dataframe(l_sum[l_sum['Miss'] > 0].rename(columns={'item_name':T["item_col"], 'quantity':T["looted_col"], 'In_Chest':T["chest_col"], 'Miss':T["miss_col"], 'player':T["by_col"]}), use_container_width=True, hide_index=True)

        with tab2:
            search_query = st.text_input(T["search_label"], "").strip()
            if search_query:
                p_loot_summary = loot_df.groupby(['item_name', 'player'])['quantity'].sum().reset_index()
                spec_p = p_loot_summary[p_loot_summary['player'].str.contains(search_query, case=False)]
                
                if not spec_p.empty:
                    def check_personal(row):
                        match = chest_player_totals[(chest_player_totals['Item'] == row['item_name']) & (chest_player_totals['ChestPlayer'].str.contains(row['player'], case=False, na=False))]
                        dep = match['Amount'].sum() if not match.empty else 0
                        return T["banked"] if dep >= row['quantity'] else f"{T['missing']} ({row['quantity'] - dep} left)"

                    spec_p[T["status_col"]] = spec_p.apply(check_personal, axis=1)
                    spec_p[T["audit_col"]] = "Pending"
                    st.data_editor(spec_p[['item_name', 'quantity', T["status_col"], T["audit_col"]]].rename(columns={'item_name':T["item_col"], 'quantity':T["looted_col"]}), use_container_width=True, hide_index=True, disabled=[T["item_col"], T["looted_col"], T["status_col"]], column_config={T["audit_col"]: st.column_config.SelectboxColumn(options=["Pending", "Confirmed Died", "Banked Later", "Excused"])})
                else:
                    st.warning("No data found.")
    except Exception as e:
        st.error(f"Error: {e}")
