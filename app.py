import streamlit as st
import pandas as pd

st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")

TARGET_GUILD = "I The Flying Dutchman I"

st.title(f"🛡️ Multi-Log Audit: {TARGET_GUILD}")
st.write("Upload multiple Loot and Chest logs. Duplicates will be removed automatically.")

# --- SIDEBAR UPLOADS ---
st.sidebar.header("1. Upload Logs")
# Changed to accept multiple loot files
loot_files = st.sidebar.file_uploader("Upload Loot Logs (Multiple allowed)", type=['txt', 'csv'], accept_multiple_files=True)
chest_files = st.sidebar.file_uploader("Upload Chest Logs (Multiple allowed)", type=['txt', 'csv'], accept_multiple_files=True)

if loot_files and chest_files:
    try:
        # 1. Process MULTIPLE Loot Logs
        all_loot_list = []
        for f in loot_files:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            all_loot_list.append(df)
        
        loot_df = pd.concat(all_loot_list, ignore_index=True)

        # --- DE-DUPLICATION STEP ---
        # We remove rows that have identical Time, Looter, and Item.
        # This stops double-counting if two people recorded the same drop.
        initial_count = len(loot_df)
        loot_df = loot_df.drop_duplicates(subset=['timestamp_utc', 'looted_by__name', 'item_id'])
        removed_count = initial_count - len(loot_df)
        
        if removed_count > 0:
            st.toast(f"Removed {removed_count} duplicate loot entries detected across multiple files!")

        # --- GUILD FILTER ---
        if 'looted_by__guild' in loot_df.columns:
            loot_df = loot_df[loot_df['looted_by__guild'] == TARGET_GUILD]
        
        if loot_df.empty:
            st.warning(f"No loot found for {TARGET_GUILD} after filtering.")
            st.stop()

        # 2. Process Chest Logs
        chest_list = []
        for f in chest_files:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            chest_list.append(df)
        
        chest_df = pd.concat(chest_list, ignore_index=True)

        # 3. Aggregate Data
        looted_summary = loot_df.groupby('item_name').agg({
            'quantity': 'sum',
            'looted_by__name': lambda x: ', '.join(sorted(set(x.astype(str)))),
            'looted_by__guild': 'first'
        }).reset_index()

        deposited_summary = chest_df.groupby('Item').agg({
            'Amount': 'sum'
        }).reset_index()

        # 4. Compare
        comparison = pd.merge(
            looted_summary, 
            deposited_summary, 
            left_on='item_name', 
            right_on='Item', 
            how='left'
        )

        comparison['Amount'] = comparison['Amount'].fillna(0)
        comparison['Missing_Qty'] = comparison['quantity'] - comparison['Amount']
        missing_items = comparison[comparison['Missing_Qty'] > 0].copy()

        # --- UI DISPLAY ---
        st.subheader(f"⚠️ Missing Items for {TARGET_GUILD}")
        
        # Search Bar for Player Names
        search_query = st.text_input("🔍 Search by Player Name", "")
        
        display_df = missing_items[[
            'looted_by__guild', 'item_name', 'quantity', 'Amount', 'Missing_Qty', 'looted_by__name'
        ]].rename(columns={
            'looted_by__guild': 'Guild',
            'item_name': 'Item Name',
            'quantity': 'Total Looted',
            'Amount': 'In Chests',
            'Missing_Qty': 'Missing',
            'looted_by__name': 'Looted By'
        })

        if search_query:
            display_df = display_df[display_df['Looted By'].str.contains(search_query, case=False)]

        st.dataframe(display_df, use_container_width=True)
        
        # Metrics to show the user that deduplication worked
        st.caption(f"Note: Deduplicated {removed_count} items. Total unique items tracked: {len(loot_df)}")

    except Exception as e:
        st.error(f"Error: {e}")

else:
    st.info("Upload logs to start. You can select multiple files at once.")
