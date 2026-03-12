import streamlit as st
import pandas as pd
import re
import io

# --- LANGUAGE DICTIONARY (RESTORED OLD INSTRUCTIONS) ---
LANGS = {
    "한국어": {
        "title": "🛡️ 길드 전리품 감사 도구 (Flying Dutchman 독점)",
        "sidebar_head": "1. 로그 업로드",
        "loot_label": "전리품 로그 업로드 (여러 파일 가능)",
        "chest_label": "길드 창고 로그 업로드 (여러 파일 가능)",
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
        "instruction_head": "📖 상세 사용 방법 (중요: Excel 사용자 필독)",
        "instructions": """
        ### 📋 감사 도구 사용 가이드
        1. **전리품 로그 내보내기:** 전리품 로거(Loot Logger)를 사용하여 데이터를 `.txt` 파일로 저장합니다.
        2. **창고 로그 내보내기:** 길드 창고(은신처 또는 개인섬)에서 '로그' 탭을 클릭하여 내역을 `.csv` 또는 `.txt`로 저장합니다.
        3. **파일 업로드:** 사이드바의 업로드 칸에 모든 전리품 로그와 창고 로그 파일을 드래그하여 넣습니다. (여러 개 동시 선택 가능)
        4. **중복 자동 제거:** 여러 명이 동시에 같은 드랍을 기록했더라도, 앱이 자동으로 중복을 제거하여 정확한 수치를 계산합니다.
        5. **결과 확인:** 표에는 **I The Flying Dutchman I** 길드원이 획득했지만 아직 창고에 입고되지 않은 아이템만 표시됩니다.
        
        **💡 Excel 사용자 참고:** Excel에서 파일을 열어 수정 후 `.csv`로 저장한 경우에도 앱이 자동으로 컬럼명을 인식하여 오류를 방지합니다.
        """
    },
    "English": {
        "title": "🛡️ Guild Loot Auditor (Flying Dutchman Exclusive)",
        "sidebar_head": "1. Upload Logs",
        "loot_label": "Upload Loot Logs (Multiple)",
        "chest_label": "Upload Chest Logs (Multiple)",
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
        "instruction_head": "📖 Detailed Instructions (For Excel Users)",
        "instructions": """
        ### 📋 How to use the Audit Tool
        1. **Export Loot Logs:** Use your Albion Loot Logger to export the loot data as a `.txt` file.
        2. **Export Chest Logs:** Go to your Guild Chest (HO or Island), click on the 'Logs' tab, and export as `.csv` or `.txt`.
        3. **Upload Files:** Drag and drop **all** your loot logs and chest logs into the sidebar.
        4. **Automatic Cleanup:** The app will automatically remove duplicate lines if multiple people recorded the same loot event.
        5. **Check Results:** The table will only show items looted by **I The Flying Dutchman I** that have not been fully deposited.
        
        **💡 Note for Excel Users:** If you edit files in Excel and save as `.csv`, this app will automatically detect the columns even if the headers change slightly.
        """
    }
}

st.set_page_config(page_title="Flying Dutchman Auditor", layout="wide")
sel_lang = st.sidebar.selectbox("🌐 Language / 언어 선택", ["한국어", "English"])
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
    content = file.read()
    try: decoded = content.decode('utf-8-sig')
    except: decoded = content.decode('latin1')
    sep = ';' if decoded.count(';') > decoded.count(',') else ','
    return pd.read_csv(io.StringIO(decoded), sep=sep, engine='python')

# --- SIDEBAR & RESET ---
st.sidebar.header(T["sidebar_head"])

if st.sidebar.button(T["reset_btn"]):
    st.cache_data.clear()
    st.rerun()

loot_files = st.sidebar.file_uploader(T["loot_label"], type=['txt', 'csv'], accept_multiple_files=True, key="loot")
chest_files = st.sidebar.file_uploader(T["chest_label"], type=['txt', 'csv'], accept_multiple_files=True, key="chest")

# --- STRICT MONOPOLY FILTER ---
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
            c_time = find_best_column(df, ['timestamputc', 'date'])
            c_id = find_best_column(df, ['itemid', 'id'])
            
            df = df.rename(columns={c_item: 'item_name', c_qty: 'quantity', c_name: 'player', c_guild: 'guild', c_time: 'time', c_id: 'id'})
            all_loot.append(df)
        
        loot_df = pd.concat(all_loot).drop_duplicates(subset=['time', 'player', 'id'])
        # EXCLUSIVE FILTER
        loot_df = loot_df[loot_df['guild'] == TARGET_GUILD]

        # 2. PROCESS CHEST
        all_chest = []
        for f in chest_files:
            df = robust_read(f)
            c_item_ch = find_best_column(df, ['item', 'itemname'])
            c_qty_ch = find_best_column(df, ['amount', 'quantity', 'totalinchest'])
            df = df.rename(columns={c_item_ch: 'Item', c_qty_ch: 'Amount'})
            all_chest.append(df)
        chest_df = pd.concat(all_chest).groupby('Item')['Amount'].sum().reset_index()

        # --- TABS ---
        tab1, tab2 = st.tabs([T["tab_full"], T["tab_player"]])

        with tab1:
            l_sum = loot_df.groupby('item_name').agg({
                'quantity': 'sum', 
                'player': lambda x: ', '.join(sorted(list(set(x.astype(str)))))
            }).reset_index()
            
            full_res = pd.merge(l_sum, chest_df, left_on='item_name', right_on='Item', how='left').fillna(0)
            full_res['Missing_Qty'] = full_res['quantity'] - full_res['Amount']
            full_res = full_res[full_res['Missing_Qty'] > 0]
            
            st.dataframe(
                full_res[['item_name', 'quantity', 'Amount', 'Missing_Qty', 'player']].rename(columns={
                    'item_name': T["item_col"], 'quantity': T["looted_col"], 'Amount': T["chest_col"], 
                    'Missing_Qty': T["miss_col"], 'player': T["by_col"]
                }), 
                use_container_width=True, hide_index=True,
                column_config={T["by_col"]: st.column_config.TextColumn(width="large")}
            )

        with tab2:
            search_query = st.text_input(T["search_label"], "").strip()
            if search_query:
                p_loot = loot_df[loot_df['player'].str.contains(search_query, case=False)]
                if not p_loot.empty:
                    p_sum = p_loot.groupby('item_name')['quantity'].sum().reset_index()
                    p_final = pd.merge(p_sum, chest_df, left_on='item_name', right_on='Item', how='left').fillna(0)
                    p_final[T["status_col"]] = p_final.apply(lambda r: T["banked"] if r['Amount'] >= r['quantity'] else T["missing"], axis=1)
                    
                    st.dataframe(
                        p_final[['item_name', 'quantity', T["status_col"]]].rename(columns={'item_name': T["item_col"], 'quantity': T["looted_col"]}),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.warning(f"No data for '{search_query}' in {TARGET_GUILD}.")

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info(f"Waiting for logs for {TARGET_GUILD}...")
