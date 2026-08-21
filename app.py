import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

st.set_page_config(page_title="S&P 500 Dashboard", layout="wide")
st.title("📈 S&P 500 Market Dashboard")

@st.cache_data
def load_data():
    # 차단을 피하기 위해 크롬 브라우저인 것처럼 위장 (User-Agent 설정)
    session = requests.Session()
    session.headers.update(
        {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    # ^GSPC는 S&P 500의 티커입니다. session을 포함하여 데이터 호출.
    sp500 = yf.Ticker("^GSPC", session=session)
    df = sp500.history(period="max")
    df.index = df.index.tz_localize(None)
    return df

df = load_data()

# 1. 전고점 대비 하락률 (Current Drawdown)
st.header("1. 현재 고점 대비 하락률 (Current Drawdown)")
all_time_high = df['High'].max()
ath_date = df['High'].idxmax()
current_price = df['Close'].iloc[-1]
latest_date = df.index[-1]
current_drawdown = ((current_price - all_time_high) / all_time_high) * 100

col1, col2, col3 = st.columns(3)
col1.metric("현재 S&P 500 지수", f"{current_price:,.2f}", f"{current_price - df['Close'].iloc[-2]:.2f}")
col2.metric("역사적 최고가 (ATH)", f"{all_time_high:,.2f}", f"{ath_date.strftime('%Y-%m-%d')}")
col3.metric("전고점 대비 하락률", f"{current_drawdown:.2f}%", delta_color="inverse")

st.info("💡 과거 구간의 최대 낙폭이 아닌, **역사적 고점(ATH) 대비 현재 지수가 얼마나 떨어져 있는지**를 직관적으로 보여줍니다.")

# 2. 최근 10년 연도별 수익률
st.header("2. 연도별 수익률 (최근 10년)")
try:
    yearly_df = df['Close'].resample('YE').last()
except ValueError:
    yearly_df = df['Close'].resample('Y').last()
    
yearly_ret = (yearly_df.pct_change() * 100).dropna().tail(10).reset_index()
yearly_ret.columns = ['Date', 'Return']
yearly_ret['Year'] = yearly_ret['Date'].dt.strftime('%Y')
yearly_ret['Color'] = yearly_ret['Return'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')

fig_yearly = px.bar(yearly_ret, x='Year', y='Return', text_auto='.2f', 
                    color='Color', color_discrete_map={'Positive': '#2e7d32', 'Negative': '#d32f2f'})
fig_yearly.update_layout(showlegend=False, xaxis_title="연도", yaxis_title="수익률 (%)")
st.plotly_chart(fig_yearly, use_container_width=True)

# 3. 최근 1년 월간 수익률
st.header("3. 월간 수익률 (최근 1년)")
try:
    monthly_df = df['Close'].resample('ME').last()
except ValueError:
    monthly_df = df['Close'].resample('M').last()
    
monthly_ret = (monthly_df.pct_change() * 100).dropna().tail(12).reset_index()
monthly_ret.columns = ['Date', 'Return']
monthly_ret['Month'] = monthly_ret['Date'].dt.strftime('%Y-%m')
monthly_ret['Color'] = monthly_ret['Return'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')

fig_monthly = px.bar(monthly_ret, x='Month', y='Return', text_auto='.2f', 
                     color='Color', color_discrete_map={'Positive': '#2e7d32', 'Negative': '#d32f2f'})
fig_monthly.update_layout(showlegend=False, xaxis_title="월", yaxis_title="수익률 (%)")
st.plotly_chart(fig_monthly, use_container_width=True)

st.caption(f"최종 업데이트: {latest_date.strftime('%Y-%m-%d')}")
