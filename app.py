import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pylab import matplotlib
from matplotlib import font_manager
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="系統監控儀表板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("監控日誌表")
st.header(':grey[]', divider='rainbow')
st.markdown('[*雲端維護組*](https://gemfor.sharepoint.com/:x:/r/sites/cloud-support/17/%E5%80%BC%E7%8F%AD%E7%9B%A3%E6%8E%A7%E6%97%A5%E8%AA%8C/%E4%BE%8B%E8%A1%8C%E5%B7%A5%E4%BD%9C%20%E6%97%A5/202410%E7%9B%A3%E6%8E%A7%E6%97%A5%E8%AA%8C/EXCEL/10%E6%9C%88%E7%9B%A3%E6%8E%A7%E6%97%A5%E8%AA%8C.xlsx?d=w7fc1a66db73f496eb9b0e95877d23dd6&csf=1&web=1&e=myxWU2)')

def load_data():
    # 假設數據已經從Excel讀取並轉換為DataFrame
    df = pd.read_excel("10月監控日誌.xlsx")
    
    # 轉換日期時間列
    df['發生日期'] = pd.to_datetime(df['發生日期'])
    df['日期'] = df['發生日期'].dt.date
    df['週'] = df['發生日期'].dt.isocalendar().week
    df['月份'] = df['發生日期'].dt.month
    
    return df

def filter_data(df, start_date, end_date, exclude_hosts):
    """過濾數據基於日期範圍和排除的主機"""
    # 轉換日期格式確保可以比較
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # 過濾日期範圍
    mask = (df['發生日期'].dt.date >= start_date.date()) & (df['發生日期'].dt.date <= end_date.date())
    filtered_df = df[mask]
    
    # 排除特定主機
    if exclude_hosts:
        filtered_df = filtered_df[~filtered_df['主機(Host)'].isin(exclude_hosts)]
    
    return filtered_df

def create_dashboard():
    st.title("系統監控儀表板")
    
    # 讀取數據
    df = load_data()
    
    # 要排除的測試主機列表
    EXCLUDED_HOSTS = ['Ai3-ECP-IDC-ECP-WebchatTest-192.168.211.5']
    
    # 側邊欄 - 日期過濾
    st.sidebar.header("過濾條件")
    date_range = st.sidebar.date_input(
        "選擇日期範圍",
        [df['發生日期'].min().date(), df['發生日期'].max().date()]
    )
    
    # 確保有兩個日期被選擇
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filter_data(df, start_date, end_date, EXCLUDED_HOSTS)
    else:
        st.error("請選擇完整的日期範圍")
        return
    
    # 主機告警統計 (已排除測試主機)
    host_alerts = filtered_df['主機(Host)'].value_counts()
    top_5_hosts = host_alerts.head()
    
    # 頂部統計數字
    total_alerts = len(filtered_df)
    unique_hosts = filtered_df['主機(Host)'].nunique()
    max_host_alerts = host_alerts.max() if not host_alerts.empty else 0
    
    col1, col2, col3= st.columns(3)
    with col1:
        st.metric("總告警數", f"{total_alerts:,}")
    with col2:
        st.metric("影響主機數", f"{unique_hosts:,}")
    with col3:
        st.metric("單主機最高告警數", f"{max_host_alerts:,}")
    
    # 主要圖表區域
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("每日告警總數")
        daily_alerts = filtered_df.groupby('日期').size().reset_index(name='告警次數')
        fig_daily = px.line(daily_alerts, x='日期', y='告警次數',
                          template='plotly_white')
        fig_daily.update_layout(height=400)
        st.plotly_chart(fig_daily, use_container_width=True)
        
    with chart_col2:
        st.subheader("Top 5 告警主機")
        fig_top_hosts = go.Figure(data=[
            go.Bar(
                x=top_5_hosts.values,
                y=top_5_hosts.index,
                orientation='h',
                text=top_5_hosts.values,
                textposition='auto',
            )
        ])
        fig_top_hosts.update_layout(
            height=400,
            template='plotly_white',
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="告警次數",
            yaxis_title="主機名稱"
        )
        st.plotly_chart(fig_top_hosts, use_container_width=True)
    
    # 主機詳細統計
    st.subheader("主機告警詳細統計")
    host_details = filtered_df.groupby('主機(Host)').agg({
        '異常訊息': 'count',
    }).round(2).reset_index()
    
    host_details.columns = ['主機名稱', '告警次數']
    host_details = host_details.sort_values('告警次數', ascending=False)
    
    # 顯示所有主機的統計資料，但用不同顏色標示 Top 5
    st.dataframe(
        host_details.style.apply(
            lambda x: ['background-color: #e6f3ff' if i < 5 else '' for i in range(len(x))], 
            axis=0
        ),
        use_container_width=True
    )
    
    # 異常分布圓餅圖
    chart_col3, chart_col4 = st.columns(2)
    
    with chart_col3:
        st.subheader("異常等級分布")
        severity_dist = filtered_df['異常等級'].value_counts()
        fig_severity = px.pie(
            values=severity_dist.values, 
            names=severity_dist.index,
            template='plotly_white'
        )
        fig_severity.update_layout(height=400)
        st.plotly_chart(fig_severity, use_container_width=True)
    
    with chart_col4:
        st.subheader("主機告警時間分布")
        fig_time_dist = px.histogram(
            filtered_df, 
            x=filtered_df['發生日期'].dt.hour,
            nbins=24,
            title="每小時告警分布",
            labels={'value': '小時', 'count': '告警次數'},
            template='plotly_white'
        )
        fig_time_dist.update_layout(height=400)
        st.plotly_chart(fig_time_dist, use_container_width=True)
    
    # 異常訊息分析
    st.subheader("異常訊息類型統計")
    message_counts = filtered_df['異常訊息'].value_counts().reset_index()
    message_counts.columns = ['異常訊息', '次數']
    
    fig_messages = go.Figure(data=[
        go.Bar(x=message_counts['異常訊息'], y=message_counts['次數'])
    ])
    fig_messages.update_layout(
        xaxis_tickangle=-45,
        height=400,
        template='plotly_white'
    )
    st.plotly_chart(fig_messages, use_container_width=True)

    # 顯示選擇的日期範圍
    st.sidebar.write(f"當前顯示: {start_date} 到 {end_date}")

if __name__ == "__main__":
    create_dashboard()