import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

# 모바일에 최적화된 화면 너비 설정
st.set_page_config(page_title="S&P 500 Dashboard", layout="centered")

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
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; }
</style>
''', unsafe_allow_html=True)

st.markdown("# 📈 S&P 500 Market Dashboard")

@st.cache_data
def load_data():
    session = requests.Session()
    session.headers.update(
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    sp500 = yf.Ticker("^GSPC", session=session)
    df = sp500.history(period="max")
    df.index = df.index.tz_localize(None)
    return df

df = load_data()

# 1. 전고점 대비 하락률
st.markdown("## 1. 현재 고점 대비 하락률 (MDD)")
all_time_high = df['High'].max()
ath_date = df['High'].idxmax()
current_price = df['Close'].iloc[-1]
latest_date = df.index[-1]
current_drawdown = ((current_price - all_time_high) / all_time_high) * 100

col1, col2, col3 = st.columns(3)
col1.metric("현재 지수", f"{current_price:,.2f}", f"{current_price - df['Close'].iloc[-2]:.2f}")
col2.metric("최고가(ATH)", f"{all_time_high:,.2f}", f"{ath_date.strftime('%y-%m-%d')}")
col3.metric("하락률", f"{current_drawdown:.2f}%", delta_color="inverse")

st.info("💡 역사적 고점 대비 현재 지수가 얼마나 떨어져 있는지 보여줍니다.")

# --- 차트 설정 공통 옵션 (터치 고정 모드) ---
config = {'staticPlot': True} # 스크롤 시 차트가 눌리지 않게 이미지처럼 고정

# 2. 최근 10년 연도별 수익률
st.markdown("## 2. 연도별 수익률 (최근 10년)")
try:
    yearly_df = df['Close'].resample('YE').last()
except ValueError:
    yearly_df = df['Close'].resample('Y').last()
    
yearly_ret = (yearly_df.pct_change() * 100).dropna().tail(10).reset_index()
yearly_ret.columns = ['Date', 'Return']
yearly_ret['Year'] = yearly_ret['Date'].dt.strftime('%Y')
yearly_ret['Color'] = yearly_ret['Return'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')

fig_yearly = px.bar(yearly_ret, x='Year', y='Return', text_auto='.1f', 
                    color='Color', color_discrete_map={'Positive': '#2e7d32', 'Negative': '#d32f2f'})
fig_yearly.update_layout(
    showlegend=False, 
    xaxis_title=None, 
    yaxis_title=None,
    margin=dict(l=0, r=0, t=30, b=0), # 차트 여백 최소화
    font=dict(size=12, family="Arial Black, Arial, sans-serif") # 축 글자 설정
)
# 그래프 안의 글자를 크고 두껍게, 그리고 막대 바깥으로 배치
fig_yearly.update_traces(textfont_size=15, textfont_color="black", textangle=0, textposition="outside", cliponaxis=False) 
st.plotly_chart(fig_yearly, use_container_width=True, config=config)

# 3. 최근 1년 월간 수익률
st.markdown("## 3. 월간 수익률 (최근 1년)")
try:
    monthly_df = df['Close'].resample('ME').last()
except ValueError:
    monthly_df = df['Close'].resample('M').last()
    
monthly_ret = (monthly_df.pct_change() * 100).dropna().tail(12).reset_index()
monthly_ret.columns = ['Date', 'Return']
# 모바일에서 글자가 겹치지 않도록 '26-08' 형태로 짧게 변환
monthly_ret['Month'] = monthly_ret['Date'].dt.strftime('%y-%m') 
monthly_ret['Color'] = monthly_ret['Return'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')

fig_monthly = px.bar(monthly_ret, x='Month', y='Return', text_auto='.1f', 
                     color='Color', color_discrete_map={'Positive': '#2e7d32', 'Negative': '#d32f2f'})
fig_monthly.update_layout(
    showlegend=False, 
    xaxis_title=None, 
    yaxis_title=None,
    margin=dict(l=0, r=0, t=30, b=0),
    font=dict(size=12, family="Arial Black, Arial, sans-serif")
)
# 그래프 안의 글자를 크고 두껍게, 그리고 막대 바깥으로 배치
fig_monthly.update_traces(textfont_size=15, textfont_color="black", textangle=0, textposition="outside", cliponaxis=False)
st.plotly_chart(fig_monthly, use_container_width=True, config=config)

st.caption(f"최종 업데이트: {latest_date.strftime('%Y-%m-%d')}")
