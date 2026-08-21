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

# 지수 대시보드를 그리는 통합 함수
def render_dashboard(ticker_symbol, title):
    df = load_data(ticker_symbol)
    config = {'staticPlot': True}
    
    # ---------------------------------------------
    # 1. 전고점 대비 하락률
    # ---------------------------------------------
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
    
    # ---------------------------------------------
    # 2. 최근 30년 연도별 수익률
    # ---------------------------------------------
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
    
    # ---------------------------------------------
    # 3. 최근 1년 월간 수익률
    # ---------------------------------------------
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

    # ---------------------------------------------
    # 4. 초기 투자금 시뮬레이터 (백테스트)
    # ---------------------------------------------
    st.markdown("---")
    st.markdown(f"## 4. 💰 {title} 장기 투자 시뮬레이터")
    
    # 최근 30년 리스트 생성 (올해 제외)
    current_year = datetime.now().year
    years_list = list(range(current_year - 30, current_year + 1))
    
    # 입력 UI (key 파라미터 추가로 탭 충돌 에러 방지)
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        selected_year = st.selectbox("투자를 시작한 연도 (연초 매수)", years_list, index=len(years_list)-11, key=f"{title}_year") 
    with col_input2:
        initial_amount = st.number_input("초기 투자 금액 (원/달러 등)", value=10000000, step=1000000, key=f"{title}_amount")

    # 선택한 연도부터의 데이터만 필터링
    df_sim = df[df.index.year >= selected_year].copy()
    
    if not df_sim.empty:
        # 매수가 (해당 연도의 가장 첫 거래일 종가)
        buy_price = df_sim.iloc[0]['Close']
        buy_date = df_sim.index[0]
        
        # 포트폴리오 가치 계산
        df_sim['Portfolio Value'] = initial_amount * (df_sim['Close'] / buy_price)
        final_value = df_sim['Portfolio Value'].iloc[-1]
        cumulative_roi = ((final_value - initial_amount) / initial_amount) * 100
        
        # --- CAGR (연평균 복리 수익률) 계산 ---
        days_held = (df_sim.index[-1] - buy_date).days
        years_held = days_held / 365.25
        cagr = ((final_value / initial_amount) ** (1 / years_held) - 1) * 100 if years_held > 0 else 0
        
        # 결과 텍스트 출력 (3칸으로 분할)
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric(f"초기금액 ({buy_date.strftime('%y년')})", f"{initial_amount:,.0f}")
        
        roi_color = "#d32f2f" if cumulative_roi < 0 else "#2e7d32"
        roi_sign = "+" if cumulative_roi >= 0 else ""
        
        with col_res2:
            st.markdown(
                f'<div style="font-size: 12px; color: #31333F; margin-bottom: 4px;">현재 평가 금액</div>'
                f'<div style="color: {roi_color}; font-size: 18px; font-weight: bold;">{final_value:,.0f} <br><span style="font-size: 13px;">({roi_sign}{cumulative_roi:,.1f}%)</span></div>', 
                unsafe_allow_html=True
            )
            
        with col_res3:
            st.markdown(
                f'<div style="font-size: 12px; color: #31333F; margin-bottom: 4px;">연평균 복리(CAGR)</div>'
                f'<div style="color: {roi_color}; font-size: 18px; font-weight: bold;"><br>{roi_sign}{cagr:,.1f}%</div>', 
                unsafe_allow_html=True
            )
            
        # 자산 성장 그래프
        fig_sim = px.line(df_sim, x=df_sim.index, y='Portfolio Value')
        fig_sim.update_layout(
            showlegend=False, xaxis_title=None, yaxis_title="자산 평가액",
            margin=dict(l=0, r=0, t=20, b=0),
            hovermode="x unified"
        )
        line_color = "#1f77b4" if "S&P" in title else "#ff7f0e"
        fig_sim.update_traces(line=dict(color=line_color, width=2))
        st.plotly_chart(fig_sim, use_container_width=True)

    st.caption(f"최종 업데이트: {latest_date.strftime('%Y-%m-%d')}")

# --- 페이지 분할 (탭 기능) ---
tab1, tab2 = st.tabs(["S&P 500", "NASDAQ 100"])

with tab1:
    render_dashboard("^GSPC", "S&P 500")

with tab2:
    render_dashboard("^NDX", "나스닥 100")
