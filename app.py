# app.py
# 人工智能板块上市公司数字化转型综合分析系统（含底部二维码）
# 运行：streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import qrcode
from io import BytesIO
import os

# --------------------------------------------------
# 1. 全局配置
# --------------------------------------------------
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

# --------------------------------------------------
# 2. 数据加载
# --------------------------------------------------
@st.cache_data
def load_data(file_path=None):
    if file_path is None:
        file_path = "merged_data.xlsx"
    try:
        df = pd.read_excel(file_path)
        if "Unnamed: 0" in df.columns:
            df = df.rename(columns={"Unnamed: 0": "股票代码"})
        required = ["股票代码"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            st.error(f"缺少必要列: {', '.join(missing)}")
            return None
        return df
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return None

# --------------------------------------------------
# 3. 综合图表
# --------------------------------------------------
def plot_overall_interactive_chart(df):
    st.subheader("人工智能板块上市公司数字化转型综合分析")

    # 行业列
    industry_column = None
    for c in ["行业", "所属行业", "行业分类", "industry", "Industry"]:
        if c in df.columns:
            industry_column = c
            break

    numeric_columns = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
    if "股票代码" in numeric_columns:
        numeric_columns.remove("股票代码")

    # 1. 行业分布 & 直方图
    st.markdown("### 行业分布与数字化转型指数概览")
    col1, col2 = st.columns(2)
    with col1:
        if industry_column:
            tmp = df[industry_column].value_counts().reset_index()
            tmp.columns = [industry_column, "企业数量"]
            fig = px.pie(tmp, values="企业数量", names=industry_column, title="各行业企业数量占比")
            st.plotly_chart(fig, use_container_width=True)
    with col2:
        if numeric_columns:
            def_col = "数字化转型总指数" if "数字化转型总指数" in numeric_columns else numeric_columns[0]
            fig = px.histogram(df, x=def_col, nbins=20, title=f"{def_col}分布")
            st.plotly_chart(fig, use_container_width=True)

    # 2. 散点关联
    st.markdown("### 数字化转型指标交互式关联分析")
    if len(numeric_columns) >= 2:
        x_def = "数字化转型总指数" if "数字化转型总指数" in numeric_columns else numeric_columns[0]
        y_def = "技术应用" if "技术应用" in numeric_columns else numeric_columns[1]
        x_col = st.selectbox("X轴指标", numeric_columns, index=numeric_columns.index(x_def))
        y_col = st.selectbox("Y轴指标", numeric_columns, index=numeric_columns.index(y_def))
        color_by = st.selectbox("颜色分组", ["无分组"] + ([industry_column] if industry_column else []))
        fig = px.scatter(df, x=x_col, y=y_col,
                         color=None if color_by == "无分组" else color_by,
                         hover_name="企业名称" if "企业名称" in df.columns else "股票代码",
                         title=f"{x_col} 与 {y_col} 关联分析")
        if st.checkbox("显示趋势线"):
            fig = px.scatter(df, x=x_col, y=y_col, trendline="ols")
        st.plotly_chart(fig, use_container_width=True)

    # 3. 行业雷达
    st.markdown("### 各行业数字化转型指标对比")
    if industry_column and numeric_columns:
        key = ["数字化转型总指数", "战略转型", "技术应用", "组织变革", "数据价值", "流程优化"]
        avail = [c for c in key if c in numeric_columns] or numeric_columns[:3]
        selected = st.multiselect("选择要比较的指标", avail, default=avail)
        if selected:
            radar_df = df.groupby(industry_column)[selected].mean().reset_index()
            radar_df = radar_df.melt(id_vars=industry_column, var_name="指标", value_name="平均值")
            fig = px.line_polar(radar_df, r="平均值", theta="指标", color=industry_column, line_close=True,
                                title="各行业数字化转型指标雷达图对比")
            st.plotly_chart(fig, use_container_width=True)

    # 4. 排名榜单
    st.markdown("### 企业数字化转型排名榜单")
    if numeric_columns:
        rank_col = st.selectbox("选择排名指标", numeric_columns,
                                index=numeric_columns.index("数字化转型总指数") if "数字化转型总指数" in numeric_columns else 0)
        top_n = st.slider("显示数量", 5, 50, 10, 5)
        asc = st.radio("排序方式", ["降序（从高到低）", "升序（从低到高）"]) == "升序（从低到高）"
        ranking = df.sort_values(rank_col, ascending=asc).head(top_n)
        display_cols = ["企业名称", "股票代码", rank_col] if "企业名称" in df.columns else ["股票代码", rank_col]
        st.dataframe(ranking[display_cols].reset_index(drop=True), use_container_width=True)

    return numeric_columns, industry_column

# --------------------------------------------------
# 4. 底部二维码
# --------------------------------------------------
def show_qr_code():
    """在页面最底部居中显示当前页面二维码"""
    # 取当前 URL（部署后会自动识别）
    url = st.experimental_get_query_params().get("_url", [""])[0]
    if not url:
        # 本地默认
        url = "http://localhost:8501"
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#000000", back_color="#FFFFFF")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    st.write("---")
    st.markdown("<h5 style='text-align: center;'>手机扫码，直接访问本页面</h5>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.image(buf, width=200)
    st.markdown(f"<p style='text-align: center; font-size: 12px; color: grey;'>{url}</p>",
                unsafe_allow_html=True)

# --------------------------------------------------
# 5. 页面主体
# --------------------------------------------------
def main():
    st.set_page_config(page_title="数字化转型综合分析系统", layout="wide", page_icon="📊")
    st.title("人工智能板块上市公司数字化转型综合分析系统")
    st.markdown("本系统通过交互式图表展示人工智能板块上市公司数字化转型整体情况，下方支持检索特定企业详细数据。")

    st.sidebar.header("数据设置")
    uploaded = st.sidebar.file_uploader("上传Excel文件", type=["xlsx", "xls"])
    df = load_data(uploaded) if uploaded else load_data()

    if df is not None:
        numeric_columns, industry_column = plot_overall_interactive_chart(df)

        # 企业查询
        st.subheader("企业数字化转型数据查询")
        if st.checkbox("查看数据结构预览"):
            st.dataframe(df.head(5), use_container_width=True)
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            query_text = st.text_input("请输入股票代码或企业名称", placeholder="例如: 300884 或 科大讯飞")
        with col2:
            query_by = st.radio("查询依据", ["股票代码"] + (["企业名称"] if "企业名称" in df.columns else []))
        with col3:
            query_method = st.radio("查询方式", ["精确查询", "模糊查询"])
        if st.button("查询", type="primary"):
            if not query_text.strip():
                st.warning("请输入查询内容")
            else:
                qt = query_text.strip()
                try:
                    if query_by == "股票代码":
                        if query_method == "精确查询":
                            res = df[df["股票代码"] == int(qt)]
                        else:
                            res = df[df["股票代码"].astype(str).str.contains(qt)]
                    else:
                        if query_method == "精确查询":
                            res = df[df["企业名称"] == qt]
                        else:
                            res = df[df["企业名称"].str.contains(qt, na=False)]
                    if res.empty:
                        st.warning("未找到符合条件的企业记录")
                    else:
                        st.subheader(f"查询结果：共找到{len(res)}家企业")
                        st.dataframe(res, use_container_width=True)
                        # 可视化略（与原逻辑一致）
                except ValueError:
                    st.error("股票代码需为整数")
    else:
        st.error("数据加载失败")

    # 统一底部二维码
    show_qr_code()

# --------------------------------------------------
# 6. 入口
# --------------------------------------------------
if __name__ == "__main__":
    main()