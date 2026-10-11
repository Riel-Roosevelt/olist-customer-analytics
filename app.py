import streamlit as st
import pandas as pd
import plotly.express as px

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Brazilian E-Commerce Analytics",
    layout="wide"
)

# Custom CSS untuk merapikan tampilan & mencegah angka kepotong
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    [data-testid="stMetricValue"] {
        font-size: 26px !important;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data
def load_data():
    df = pd.read_csv('olist_customers_processed_data.csv')
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['order_month'] = df['order_purchase_timestamp'].dt.to_period('M').astype(str)
    df['cohort_month'] = pd.to_datetime(df['order_purchase_timestamp']).groupby(df['customer_unique_id']).transform('min').dt.to_period('M').astype(str)
    return df

df_raw = load_data()

# --- SIDEBAR FILTERS ---
st.sidebar.title("Filter Options")
state_list = ['All'] + sorted(df_raw['customer_state'].unique().tolist())
selected_state = st.sidebar.selectbox("State / Region", state_list)

if selected_state != 'All':
    df = df_raw[df_raw['customer_state'] == selected_state]
else:
    df = df_raw.copy()

# --- HEADER & KPI SUMMARY ---
st.title("Brazilian E-Commerce Customer Analytics")
st.caption("End-to-End Portfolio Project | Cohort Retention, RFM Segmentation & LTV Analysis")

st.markdown("---")

# Format angka revenue agar tidak kepotong (diubah ke jutaan / M)
total_rev = df['total_order_value'].sum()
formatted_rev = f"R$ {total_rev/1e6:.2f}M" if total_rev >= 1e6 else f"R$ {total_rev:,.2f}"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Customers", f"{df['customer_unique_id'].nunique():,}")
col2.metric("Total Orders", f"{df['order_id'].nunique():,}")
col3.metric("Total Revenue", formatted_rev)
col4.metric("Avg Order Value", f"R$ {df['total_order_value'].mean():,.2f}")

st.markdown("---")

# --- TABS ANALYSIS ---
tab1, tab2, tab3 = st.tabs(["Cohort Analysis", "RFM Segmentation", "Customer LTV & Insights"])

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
        labels=dict(x="Cohort Index (Months)", y="Cohort Month", color="Retention (%)"),
        x=retention_matrix.columns,
        y=retention_matrix.index,
        color_continuous_scale="Blues",
        aspect="auto",
        text_auto=".1f"
    )
    fig_cohort.update_layout(height=480, margin=dict(l=0, r=0, t=30, b=0))
    st.plotly_chart(fig_cohort, use_container_width=True)
    st.info("Key Insight: Retention rate di seluruh cohort berada di bawah 1% pada bulan berikutnya. Ini mengindikasikan dominasi transaksi bersifat one-time purchase.")

# TAB 2: RFM SEGMENTATION
with tab2:
    st.subheader("Customer Segmentation (RFM Model)")
    col_rfm1, col_rfm2 = st.columns([1, 1.2])
    
    with col_rfm1:
        segment_counts = df.groupby('customer_segment')['customer_unique_id'].nunique().reset_index()
        fig_seg = px.pie(
            segment_counts, 
            names='customer_segment', 
            values='customer_unique_id',
            title='Customer Segment Distribution',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig_seg.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_seg, use_container_width=True)
        
    with col_rfm2:
        st.write("#### Segment Profile Breakdown")
        rfm_table = df.groupby('customer_segment').agg(
            Total_Customers=('customer_unique_id', 'nunique'),
            Avg_Recency=('recency', 'mean'),
            Avg_Frequency=('frequency', 'mean'),
            Total_Revenue=('monetary', 'sum')
        ).reset_index()
        st.dataframe(rfm_table.style.format({
            'Total_Customers': '{:,}',
            'Avg_Recency': '{:.1f} days',
            'Avg_Frequency': '{:.2f}x',
            'Total_Revenue': 'R$ {:,.2f}'
        }), use_container_width=True)

# TAB 3: CUSTOMER LTV & RECOMMENDATIONS
with tab3:
    st.subheader("Historical Customer Lifetime Value (LTV)")
    ltv_df = df.groupby('customer_segment').agg(Avg_LTV=('monetary', 'mean')).reset_index()
    fig_ltv = px.bar(
        ltv_df,
        x='customer_segment',
        y='Avg_LTV',
        color='customer_segment',
        title='Average Revenue per Customer by Segment',
        labels={'Avg_LTV': 'Avg LTV (R$)', 'customer_segment': 'Segment'},
        text_auto='.2f',
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_ltv.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_ltv, use_container_width=True)
    
    st.markdown("---")
    st.subheader("Strategic Recommendations")
    st.markdown("""
    * **Champions & Loyal Spenders:** Pertahankan nilai transaksi tinggi melalui reward program khusus dan layanan prioritas.
    * **At Risk / Need Attention:** Lakukan pemicu re-engagement dengan penawaran promosi terbatas (win-back campaign).
    * **New Customers:** Optimalkan onboarding via email edukasi produk dalam 30 hari pertama pasca pembelian.
    """)
