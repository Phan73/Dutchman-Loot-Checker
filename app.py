import streamlit as st
import pandas as pd

st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")

# Setting the Guild Name to track
TARGET_GUILD = "I The Flying Dutchman I"

st.title(f"🛡️ Audit for: {TARGET_GUILD}")

# --- SIDEBAR UPLOADS ---
st.sidebar.header("1. Upload Logs")
loot_file = st.sidebar.file_uploader("Upload Loot Log", type=['txt', 'csv'])
chest_files = st.sidebar.file_uploader("Upload Chest Logs", type=['txt', 'csv'], accept_multiple_files=True)

if loot_file and chest_files:
    try:
        # 1. Process Loot Log
        loot_df = pd.read_csv(loot_file, sep=None, engine='python', encoding='utf-8-sig')
        loot_df.columns = loot_df.columns.str.strip()

        # --- GUILD FILTER ---
        if 'looted_by__guild' in loot_df.columns:
            # Filter to only your guild members
            loot_df = loot_df[loot_df['looted_by__guild'] == TARGET_GUILD]
        
        if loot_df.empty:
            st.warning(f"No loot found for guild: {TARGET_GUILD}.")
            st.stop()

        # 2. Process Chest Logs
        chest_list = []
        for f in chest_files:
            df = pd.read_csv(f, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = df.columns.str.strip()
            chest_list.append(df)
        
        chest_df = pd.concat(chest_list, ignore_index=True)

        # 3. Aggregate Data
        # Group by item_name and keep the Guild name
        looted_summary = loot_df.groupby('item_name').agg({
            'quantity': 'sum',
            'looted_by__name': lambda x: ', '.join(sorted(set(x.astype(str)))),
            'looted_by__guild': 'first'  # This ensures the Guild name is kept
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

        # Fill missing chest amounts with 0
        comparison['Amount'] = comparison['Amount'].fillna(0)
        
        # Calculate Missing
        comparison['Missing_Qty'] = comparison['quantity'] - comparison['Amount']
        
        # Filter for items that are actually missing
        missing_items = comparison[comparison['Missing_Qty'] > 0].copy()

        # --- UI DISPLAY ---
        st.subheader(f"⚠️ Missing Items: {TARGET_GUILD}")
        
        if not missing_items.empty:
            # Re-ordering and renaming columns for the table
            display_df = missing_items[[
                'looted_by__guild', 'item_name', 'quantity', 'Amount', 'Missing_Qty', 'looted_by__name'
            ]].rename(columns={
                'looted_by__guild': 'Looter Guild',
                'item_name': 'Item Name',
                'quantity': 'Total Looted',
                'Amount': 'Total in Chest',
                'Missing_Qty': 'Missing',
                'looted_by__name': 'Looted By'
            })
            
            # Show the table
            st.dataframe(display_df, use_container_width=True)
            
            # Summary Metrics
            st.info(f"Summary: Found {len(display_df)} item types that were looted by {TARGET_GUILD} but are not fully accounted for in the chest logs.")
        else:
            st.success(f"All items looted by {TARGET_GUILD} are accounted for!")

    except Exception as e:
        st.error(f"Error processing files: {e}")

else:
    st.info(f"Awaiting logs to audit {TARGET_GUILD}...")