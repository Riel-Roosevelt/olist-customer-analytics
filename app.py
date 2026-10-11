import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Brazilian E-Commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('olist_processed_data.csv')
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['order_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    df['cohort_month'] = pd.to_datetime(df['order_purchase_timestamp']).groupby(df['customer_unique_id']).transform('min').dt.to_period('M').astype(str)
    return df

df_raw = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.title("🔍 Filter Data")
state_list = ['All'] + sorted(df_raw['customer_state'].unique().tolist())
selected_state = st.sidebar.selectbox("Pilih State/Provinsi:", state_list)

if selected_state != 'All':
    df = df_raw[df_raw['customer_state'] == selected_state]
else:
    df = df_raw.copy()

# --- HEADER & KPI SUMMARY ---
st.title("📊 Brazilian E-Commerce Customer Analytics")
st.markdown("End-to-End Portfolio Project: **Cohort Retention, RFM Segmentation & LTV Analysis**")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers", f"{df['customer_unique_id'].nunique():,}")
col2.metric("Total Orders", f"{df['order_id'].nunique():,}")
col3.metric("Total Revenue", f"R$ {df['total_order_value'].sum():,.2f}")
col4.metric("Avg Order Value (AOV)", f"R$ {df['total_order_value'].mean():,.2f}")

st.divider()

# --- TABS ANALYSIS ---
tab1, tab2, tab3 = st.tabs(["🗓 Cohort Analysis", "🎯 RFM Segmentation", "💎 Customer LTV & Insights"])

# TAB 1: COHORT ANALYSIS
with tab1:
    st.subheader("Monthly Cohort Retention Rate (%)")
    df_cohort = df.copy()
    df_cohort['cohort_m'] = pd.to_datetime(df_cohort['cohort_month'])
    df_cohort['order_m'] = pd.to_datetime(df_cohort['order_month'])
    
    df_cohort['cohort_index'] = (df_cohort['order_m'].dt.year - df_cohort['cohort_m'].dt.year) * 12 + \
                                (df_cohort['order_m'].dt.month - df_cohort['cohort_m'].dt.month)
    
    cohort_data = df_cohort.groupby(['cohort_month', 'cohort_index'])['customer_unique_id'].nunique().reset_index()
    cohort_matrix = cohort_data.pivot(index='cohort_month', columns='cohort_index', values='customer_unique_id')
    
    cohort_size = cohort_matrix.iloc[:, 0]
    retention_matrix = cohort_matrix.divide(cohort_size, axis=0) * 100
    
    fig_cohort = px.imshow(
        retention_matrix,
        labels=dict(x="Bulan Ke- (Cohort Index)", y="Cohort Month", color="Retention Rate (%)"),
        x=retention_matrix.columns,
        y=retention_matrix.index,
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=".1f"
    )
    fig_cohort.update_layout(height=500)
    st.plotly_chart(fig_cohort, use_container_width=True)
    st.info("💡 **Key Insight:** Sebagian besar cohort menunjukkan retention rate < 1% di bulan berikutnya (*one-time buyers*).")

# TAB 2: RFM SEGMENTATION
with tab2:
    st.subheader("Customer Segmentation Based on RFM Model")
    col_rfm1, col_rfm2 = st.columns([1, 1])
    
    with col_rfm1:
        segment_counts = df.groupby('customer_segment')['customer_unique_id'].nunique().reset_index()
        fig_seg = px.pie(
            segment_counts, 
            names='customer_segment', 
            values='customer_unique_id',
            title='Distribusi Segmen Pelanggan',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_seg, use_container_width=True)
        
    with col_rfm2:
        st.write("### Profile Metric per Segmen")
        rfm_table = df.groupby('customer_segment').agg(
            Total_Customers=('customer_unique_id', 'nunique'),
            Avg_Recency=('recency', 'mean'),
            Avg_Frequency=('frequency', 'mean'),
            Total_Revenue=('monetary', 'sum')
        ).reset_index()
        st.dataframe(rfm_table.style.format({
            'Total_Customers': '{:,}',
            'Avg_Recency': '{:.1f} hari',
            'Avg_Frequency': '{:.2f}x',
            'Total_Revenue': 'R$ {:,.2f}'
        }), use_container_width=True)

# TAB 3: CUSTOMER LTV & RECOMMENDATIONS
with tab3:
    st.subheader("Customer Lifetime Value (LTV) Breakdown")
    ltv_df = df.groupby('customer_segment').agg(Avg_LTV=('monetary', 'mean')).reset_index()
    fig_ltv = px.bar(
        ltv_df,
        x='customer_segment',
        y='Avg_LTV',
        color='customer_segment',
        title='Rata-Rata Revenue per Pelanggan (Historical LTV)',
        labels={'Avg_LTV': 'Avg LTV (R$)', 'customer_segment': 'Segmen Pelanggan'},
        text_auto='.2f'
    )
    st.plotly_chart(fig_ltv, use_container_width=True)
    
    st.subheader("📌 Rekomendasi Strategis Bisnis")
    st.markdown("""
    1. **Champions & Loyal Spenders:** Berikan program loyalitas eksklusif (misal: *free shipping threshold*).
    2. **At Risk / Need Attention:** Jalankan strategi *win-back campaign* berupa kupon diskon bertarget.
    3. **New Customers:** Kirimkan *welcome email series* dalam 30 hari pertama untuk menggenjot *activation*.
    """)
