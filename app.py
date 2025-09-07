# app.py
# 人工智能板块数字化转型综合分析（底部二维码）
# 运行：streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import qrcode
from io import BytesIO

# ---------------- 页面配置 ----------------
st.set_page_config(
    page_title="数字化转型综合分析",
    layout="wide",
    page_icon="📊",
)

# ---------------- 数据加载 ----------------
@st.cache_data
def load_data(uploaded=None):
    if uploaded is not None:
        return pd.read_excel(uploaded)
    # 演示数据
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "股票代码": [f"30{i+1000:04d}" for i in range(120)],
        "企业名称": [f"公司_{i+1}" for i in range(120)],
        "数字化转型总指数": rng.integers(30, 100, 120),
        "技术应用": rng.integers(20, 95, 120),
        "行业": rng.choice(["AI芯片", "云计算", "大数据", "机器人"], 120),
    })
    return df

# ---------------- 图表 ----------------
def plot_charts(df):
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    if "股票代码" in numeric_cols:
        numeric_cols.remove("股票代码")

    st.markdown("### 行业分布与指数概览")
    c1, c2 = st.columns(2)
    with c1:
        tmp = df["行业"].value_counts().reset_index()
        tmp.columns = ["行业", "企业数量"]
        fig = px.pie(tmp, values="企业数量", names="行业", title="各行业企业数量占比")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        if numeric_cols:
            def_col = "数字化转型总指数" if "数字化转型总指数" in numeric_cols else numeric_cols[0]
            fig = px.histogram(df, x=def_col, nbins=20, title=f"{def_col}分布")
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 指标关联分析")
    if len(numeric_cols) >= 2:
        x = st.selectbox("X 轴", numeric_cols, index=0)
        y = st.selectbox("Y 轴", numeric_cols, index=1)
        fig = px.scatter(df, x=x, y=y, color="行业", hover_name="企业名称",
                         title=f"{x} vs {y}")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 企业排名")
    if numeric_cols:
        rank_col = st.selectbox("排名指标", numeric_cols, index=0)
        top_n = st.slider("显示数量", 5, 50, 10, 5)
        ascending = st.radio("排序", ["降序", "升序"]) == "升序"
        ranking = df.sort_values(rank_col, ascending=ascending).head(top_n)
        display_cols = ["企业名称", "股票代码", rank_col]
        st.dataframe(ranking[display_cols], use_container_width=True)

# ---------------- 底部二维码（新 API） ----------------
def show_qr_code():
    domain = st.query_params.get("_url", "")               # 新 API
    if not domain:
        domain = "localhost:8501"
    url = f"https://{domain}" if not domain.startswith("http") else domain

    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    st.write("---")
    st.markdown("<h5 style='text-align:center;'>手机扫码，直达本页</h5>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image(buf, width=200)
    st.markdown(f"<p style='text-align:center;font-size:12px;color:grey;'>{url}</p>",
                unsafe_allow_html=True)

# ---------------- 主入口 ----------------
def main():
    st.title("人工智能板块数字化转型综合分析系统")
    uploaded = st.sidebar.file_uploader("上传 Excel", type=["xlsx", "xls"])
    df = load_data(uploaded)
    plot_charts(df)
    show_qr_code()

if __name__ == "__main__":
    main()
