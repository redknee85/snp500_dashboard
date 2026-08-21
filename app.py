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
    h1 { font-size: 24px !important; padding-bottom: 0px !important; }
    h2 { font-size: 18px !important; padding-top: 10px !important; margin-bottom: -10px !important; }
    div[data-testid="stMetricValue"] { font-size: 20px !important; }
    div[data-testid="stMetricLabel"] { font-size: 12px !important; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
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
    
    with col3:
        st.markdown(
            f'<div style="font-size: 12px; color: #31333F; margin-bottom: 4px;">하락률</div>'
            f'<div style="color: #d32f2f; font-size: 22px; font-weight: bold;">{current_drawdown:.2f}%</div>', 
            unsafe_allow_html=True
        )
    
    config = {'staticPlot': True}
    
    # 2. 최근 30년 연도별 수익률
    st.markdown("## 2. 연도별 수익률 (최근 30년)")
    try:
        yearly_df = df['Close'].resample('YE').last()
    except ValueError:
        yearly_df = df['Close'].resample('Y').last()
        
    yearly_ret = (yearly_df.pct_change() * 100).dropna().tail(30).reset_index()
    yearly_ret.columns = ['Date', 'Return']
    yearly_ret['Year'] = yearly_ret['Date'].dt.strftime("'%y")
    yearly_ret['Color'] = yearly_ret['Return'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')
    
    fig_yearly = px.bar(yearly_ret, x='Year', y='Return', text_auto='.0f', 
                        color='Color', color_discrete_map={'Positive': '#2e7d32', 'Negative': '#d32f2f'})
    fig_yearly.update_layout(
        showlegend=False, xaxis_title=None, yaxis_title=None,
        margin=dict(l=0, r=0, t=30, b=0),
        font=dict(size=10, family="Arial Black, Arial, sans-serif")
    )
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
    fig_monthly.update_xaxes(type='category', tickangle=-45, categoryorder='array', categoryarray=monthly_ret['Month'])
    fig_monthly.update_traces(textfont_size=13, textfont_color="black", textangle=0, textposition="outside", cliponaxis=False)
    st.plotly_chart(fig_monthly, use_container_width=True, config=config)
    
    # --- 4. 초기 투자금 백테스트 시뮬레이터 (신규 추가) ---
    st.markdown("---")
    st.markdown(f"## 💰 {title} 장기 투자 시뮬레이터")
    
    # 데이터가 존재하는 연도 목록 추출 (최근 30년 제한)
    available_years = sorted(list(set(df.index.year)))[-30:]
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        # 기본값은 10년 전으로 설정
        default_year_index = len(available_years) - 11 if len(available_years) > 10 else 0
        selected_year = st.selectbox("투자 시작 연도", available_years, index=default_year_index)
    with col_input2:
        # 입력 금액 (단위: 원, 기본값 1천만원)
        initial_amount = st.number_input("초기 투자금 (원)", min_value=0, value=10000000, step=1000000, format="%d")
        
    # 선택한 연도의 가장 첫 번째 거래일 가격을 매수가로 산정
    start_data = df[df.index.year == selected_year]
    if not start_data.empty:
        start_price = start_data['Close'].iloc[0]
        
        # 수익률 및 최종 금액 계산
        calc_return_rate = ((current_price - start_price) / start_price) * 100
        final_amount = initial_amount * (1 + calc_return_rate / 100)
        
        # 결과 렌더링 (플러스면 초록, 마이너스면 빨강)
        res_color = "#d32f2f" if calc_return_rate < 0 else "#2e7d32"
        res_sign = "+" if calc_return_rate >= 0 else ""
        
        st.markdown(
            f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin-top: 10px; border-left: 5px solid {res_color};">
                <div style="font-size: 14px; color: #555;">현재 평가 금액</div>
                <div style="font-size: 26px; font-weight: bold; color: {res_color};">{final_amount:,.0f} 원</div>
                <div style="font-size: 14px; color: #555; margin-top: 10px;">누적 수익률</div>
                <div style="font-size: 20px; font-weight: bold; color: {res_color};">{res_sign}{calc_return_rate:,.2f}%</div>
            </div>
            """, unsafe_allow_html=True
        )
    
    st.caption(f"최종 데이터 업데이트: {latest_date.strftime('%Y-%m-%d')}")

# --- 페이지 분할 (탭 기능) ---
tab1, tab2 = st.tabs(["S&P 500", "NASDAQ 100"])

with tab1:
    render_dashboard("^GSPC", "S&P 500")

with tab2:
    render_dashboard("^NDX", "나스닥 100")
