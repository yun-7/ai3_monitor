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
    # 檔案上傳功能
    uploaded_file = st.file_uploader("選擇一個 CSV 或 Excel 檔案", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file is not None:
        try:
            # 根據檔案類型讀取資料
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
                df = df[df["主管或處理人回應"].notna()]
            else:
                df = pd.read_excel(uploaded_file)
                df = df[df["主管或處理人回應"].notna()]
            
            # 轉換日期時間列
            df['發生日期'] = pd.to_datetime(df['發生日期'])
            df['日期'] = df['發生日期'].dt.date
            df['時間'] = df['發生日期'].dt.time
            df['週'] = df['發生日期'].dt.isocalendar().week
            df['月份'] = df['發生日期'].dt.month
            
            return df
            
        except Exception as e:
            st.error(f'讀取檔案時發生錯誤: {str(e)}')
            return None
    return None

def calculate_stats(df):
    stats = {
        'CPU': {
            'VM CPU\n>90%': len(df[df['異常訊息'].str.contains(r'High CPU utilization \(over 90% for 5m\)', regex=True, na=False)]),
            'RDS CPU\n>85%': len(df[df['異常訊息'].str.contains(r'AWS RDS: High CPU utilization \(over 85% for 15m\)', regex=True, na=False)]),
        },
        '記憶體': {
            'JVM\n>80%': len(df[df['異常訊息'].str.contains('JVM', regex=True, na=False)]),
            '主機可用記憶體\n<500mb': len(df[df['異常訊息'].str.contains(r'Lack of available memory \(<500M', regex=True, na=False)]),
        },
        '硬碟': {
            '可用空間\n>80%': len(df[df['異常訊息'].str.contains('磁碟', regex=True, na=False)]),
        },
        '網頁': {
            '網頁無法<br>連線': len(df[df['異常訊息'].str.contains('網頁', na=False)]),
        }
    }
    return stats

def get_unique_error_types(df):
    # 定義主要錯誤類型的關鍵字及其對應的友好名稱
    error_types = {
        'JVM': 'ECP-JVM低於20%',
        'AWS RDS': 'AWS RDS',
        'swap': 'swap',
        '磁碟空間': '磁碟',
        'Interface': 'Link down',
        'ICMP': 'ICMP',
        'Web': '網頁',
        'memory < 500M': '<500M',
        'CPU >90%': r'High CPU utilization \(over 90% for 5m\)'
    }
    return error_types

def filter_data_host(df, start_date, end_date, exclude_hosts):
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

def filter_data(df, start_date, end_date):
    """過濾數據基於日期範圍和排除的主機"""
    # 轉換日期格式確保可以比較
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # 過濾日期範圍
    mask = (df['發生日期'].dt.date >= start_date.date()) & (df['發生日期'].dt.date <= end_date.date())
    filtered_df = df[mask]
    
    return filtered_df

def create_dashboard():
    
    # 讀取數據
    df = load_data()
    if df is None:
        st.error("請上傳有效的 CSV 或 Excel 檔案")
        return
        
    st.subheader("系統監控儀表板")

    # 取得錯誤類型
    error_types = get_unique_error_types(df)

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
        filtered_df_host = filter_data_host(df, start_date, end_date, EXCLUDED_HOSTS)
        filtered_df=filter_data(df, start_date, end_date)
    else:
        st.error("請選擇完整的日期範圍")
        return
    
    # 主機告警統計 (已排除測試主機)
    host_alerts = filtered_df_host['主機(Host)'].value_counts()
    top_5_hosts = host_alerts.head()
    
    # 頂部統計數字
    total_alerts = len(filtered_df_host)
    unique_hosts = filtered_df_host['主機(Host)'].nunique()
    max_host_alerts = host_alerts.max() if not host_alerts.empty else 0
    
    col1, col2, col3= st.columns(3)
    with col1:
        st.metric("總告警數", f"{total_alerts:,}")
    with col2:
        st.metric("影響主機數", f"{unique_hosts:,}")
    with col3:
        st.metric("單主機最高告警數", f"{max_host_alerts:,}")
    
    
    stats = calculate_stats(filtered_df)
    
    # 創建統計表格
    st.subheader('異常統計表')
    
    # 使用 CSS 來設定表格樣式
    st.markdown("""
    <style>
    .stats-table {
        width: 100%;
        border-collapse: collapse;
    }
    .stats-table th, .stats-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: center;
    }
    .stats-table th {
        background-color: #1e88e5;
        color: white;
    }
    .stats-table tr:nth-child(1) {
        background-color: #4CAF50;
        color: white;
    }
    .stats-table td {
        background-color: #f5f5f5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 創建表格 HTML
    table_html = """
    <table class="stats-table">
        <tr>
            <th>處理方式</th>
            <th colspan="2">CPU</th>
            <th colspan="2">記憶體</th>
            <th>硬碟</th>
            <th>網頁</th>
        </tr>
        <tr>
            <td></td>
            <td>VM CPU<br>>90%</td>
            <td>RDS CPU<br>>85%</td>
            <td>JVM<br>>80%</td>
            <td>主機可用記憶體<br><500mb</td>
            <td>可用空間<br>>80%</td>
            <td>網頁無法<br>連線</td>
        </tr>
        <tr>
            <td>已通知客戶<br>並處理</td>
    """
    
    # 添加數據到表格
    for category in stats:
        for subcategory in stats[category]:
            table_html += f"<td>{stats[category][subcategory]}</td>"
    
    table_html += """
        </tr>
    </table>
    """
    st.markdown(table_html, unsafe_allow_html=True)
    # 選擇要顯示的欄位
    st.write(f'*設備障礙或線路異常需查看服務請求以及有報修局端之線路，其他請自行查看該月（週）是否有異常')

    st.subheader('詳細資料')
    col1, col2 = st.columns([2, 1])
    with col1:
        # 創建多選框
        selected_errors = st.multiselect(
            '選擇異常類型',
            list(error_types.keys()),
            default=list(error_types.keys())
        )
    display_columns = ['日期', '主機(Host)', '異常訊息', '異常等級', '主管或處理人回應']

    if selected_errors:
        mask = pd.Series(False, index=filtered_df.index)
        for error_key in selected_errors:
            mask |= filtered_df['異常訊息'].str.contains(error_types[error_key], na=False)
        filtered_df = filtered_df[mask]
        
        # 顯示篩選後的數據，只顯示指定欄位
        
        st.write(f'共找到 {len(filtered_df)} 筆記錄')
        st.dataframe(filtered_df[display_columns])

    # 主要圖表區域
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("每日告警總數")
        daily_alerts = filtered_df_host.groupby('日期').size().reset_index(name='告警次數')
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
    
    # 異常分布圓餅圖
    st.subheader("異常等級分布")
    severity_dist = filtered_df_host['異常等級'].value_counts()
    fig_severity = px.pie(
        values=severity_dist.values, 
        names=severity_dist.index,
        template='plotly_white'
    )
    fig_severity.update_layout(height=400)
    st.plotly_chart(fig_severity, use_container_width=True)
    
   
    # 顯示選擇的日期範圍
    st.sidebar.write(f"當前顯示: {start_date} 到 {end_date}")

if __name__ == "__main__":
    create_dashboard()