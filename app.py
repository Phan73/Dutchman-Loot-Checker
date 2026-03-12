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
                df['time'] = pd.to_datetime(df['time'])
                all_loot.append(df)
        
        combined_loot = pd.concat(all_loot)
        combined_loot = combined_loot[combined_loot['guild'] == TARGET_GUILD]

        # REFINED DE-DUPLICATION (10-second fuzzy window)
        # We sort by time, then group by item/player, and remove entries within 10s of each other.
        combined_loot = combined_loot.sort_values('time')
        loot_df = combined_loot.groupby(['item_name', 'player', 'quantity']).apply(
            lambda x: x.loc[x['time'].diff().dt.total_seconds().fillna(11) > 10]
        ).reset_index(drop=True)

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
