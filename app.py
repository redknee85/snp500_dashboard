import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

# 모바일에 최적화된 화면 너비 설정
st.set_page_config(page_title="Market Dashboard", layout="centered")

# 1. 폰트 크기 및 여백 조절 (CSS 주입)
st.markdown('''
<style>
    /* 제목 크기 대폭 축소 */
    h1 { font-size: 24px !important; padding-bottom: 0px !important; }
    h2 { font-size: 18px !important; padding-top: 10px !important; margin-bottom: -10px !important; }
    
    /* 숫자(Metric) 크기 축소 */
    div[data-testid="stMetricValue"] { font-size: 20px !important; }
    div[data-testid="stMetricLabel"] { font-size: 12px !important; }
    
    /* 상하 여백 줄이기 */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    
    /* 탭(Tab) 글자 크기 키우기 */
    button[data-baseweb="tab"] { font-size: 16px !important; font-weight: bold !important; }
</style>
''', unsafe_allow_html=True)

st.markdown("# 📈 Market Dashboard")

@st.cache_data
def load_data(ticker):
    session = requests.Session()
    session.headers.update(
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    data = yf.Ticker(ticker, session=session)
    df = data.history(period="max")
    df.index = df.index.tz_localize(None)
    return df

# 지수 대시보드를 그리는 통합 함수
def render_dashboard(ticker_symbol, title):
    df = load_data(ticker_symbol)
    
    # 1. 전고점 대비 하락률
    st.markdown(f"## 1. {title} 고점 대비 하락률 (MDD)")
    all_time_high = df['High'].max()
    ath_date = df['High'].idxmax()
    current_price = df['Close'].iloc[-1]
    latest_date = df.index[-1]
    current_drawdown = ((current_price - all_time_high) / all_time_high) * 100
    
    col1, col2, col3 = st.columns(3)
    col1.metric("현재 지수", f"{current_price:,.2f}", f"{current_price - df['Close'].iloc[-2]:.2f}")
    col2.metric("최고가(ATH)", f"{all_time_high:,.2f}", f"{ath_date.strftime('%y-%m-%d')}")
    
    # 하락률 강제 빨간색 적용 (HTML 주입)
    with col3:
        st.markdown(
            f'<div style="font-size: 12px; color: #31333F; margin-bottom: 4px;">하락률</div>'
            f'<div style="color: #d32f2f; font-size: 22px; font-weight: bold;">{current_drawdown:.2f}%</div>', 
            unsafe_allow_html=True
        )
    
    # --- 차트 설정 공통 옵션 (터치 고정 모드) ---
    config = {'staticPlot': True}
    
    # 2. 최근 30년 연도별 수익률
    st.markdown("## 2. 연도별 수익률 (최근 30년)")
    try:
        yearly_df = df['Close'].resample('YE').last()
    except ValueError:
        yearly_df = df['Close'].resample('Y').last()
        
    yearly_ret = (yearly_df.pct_change() * 100).dropna().tail(30).reset_index()
    yearly_ret.columns = ['Date', 'Return']
    # 연도를 2자리로 축약 (예: 2024 -> '24)
    yearly_ret['Year'] = yearly_ret['Date'].dt.strftime("'%y")
    yearly_ret['Color'] = yearly_ret['Return'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')
    
    fig_yearly = px.bar(yearly_ret, x='Year', y='Return', text_auto='.0f', 
                        color='Color', color_discrete_map={'Positive': '#2e7d32', 'Negative': '#d32f2f'})
    fig_yearly.update_layout(
        showlegend=False, xaxis_title=None, yaxis_title=None,
        margin=dict(l=0, r=0, t=30, b=0),
        font=dict(size=10, family="Arial Black, Arial, sans-serif")
    )
    # [수정됨] x축 카테고리 고정, 세로 회전, 시간순 정렬 강제 적용
    fig_yearly.update_xaxes(type='category', tickangle=-90, categoryorder='array', categoryarray=yearly_ret['Year'])
    fig_yearly.update_traces(textfont_size=11, textfont_color="black", textangle=-90, textposition="outside", cliponaxis=False) 
    st.plotly_chart(fig_yearly, use_container_width=True, config=config)
    
    # 3. 최근 1년 월간 수익률
    st.markdown("## 3. 월간 수익률 (최근 1년)")
    try:
        monthly_df = df['Close'].resample('ME').last()
    except ValueError:
        monthly_df = df['Close'].resample('M').last()
        
    monthly_ret = (monthly_df.pct_change() * 100).dropna().tail(12).reset_index()
    monthly_ret.columns = ['Date', 'Return']
    monthly_ret['Month'] = monthly_ret['Date'].dt.strftime("'%y.%m") 
    monthly_ret['Color'] = monthly_ret['Return'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')
    
    fig_monthly = px.bar(monthly_ret, x='Month', y='Return', text_auto='.1f', 
                         color='Color', color_discrete_map={'Positive': '#2e7d32', 'Negative': '#d32f2f'})
    fig_monthly.update_layout(
        showlegend=False, xaxis_title=None, yaxis_title=None,
        margin=dict(l=0, r=0, t=30, b=0),
        font=dict(size=12, family="Arial Black, Arial, sans-serif")
    )
    # [수정됨] 월간 X축도 시간순 정렬 강제 적용
    fig_monthly.update_xaxes(type='category', tickangle=-45, categoryorder='array', categoryarray=monthly_ret['Month'])
    fig_monthly.update_traces(textfont_size=13, textfont_color="black", textangle=0, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_monthly, use_container_width=True, config=config)
    
    st.caption(f"최종 업데이트: {latest_date.strftime('%Y-%m-%d')}")

# --- 페이지 분할 (탭 기능) ---
tab1, tab2 = st.tabs(["S&P 500", "NASDAQ 100"])

with tab1:
    # S&P 500 티커(^GSPC)
    render_dashboard("^GSPC", "S&P 500")

with tab2:
    # 나스닥 100 티커(^NDX)로 변경
    render_dashboard("^NDX", "나스닥 100")
