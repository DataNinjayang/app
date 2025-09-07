# app.py
# 扫码永久直达 https://hczjdm4tkq6cg9jsanhepj.streamlit.app/
# 运行：streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import qrcode
from io import BytesIO

# ---------------- 全局配置（原第一版） ----------------
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False

# ---------------- 数据加载（固定文件） ----------------
@st.cache_data
def load_data(file_path=None):
    file_path = "merged_data.xlsx"
    try:
        df = pd.read_excel(file_path)
        if "Unnamed: 0" in df.columns:
            df = df.rename(columns={"Unnamed: 0": "股票代码"})
        required_columns = ["股票代码"]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"数据中缺少必要列: {', '.join(missing_cols)}")
            return None
        return df
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return None

# ---------------- 综合图表（第一版原样） ----------------
def plot_overall_interactive_chart(df):
    st.subheader("人工智能板块上市公司数字化转型综合分析")
    industry_column = None
    for col in ['行业', '所属行业', '行业分类', 'industry', 'Industry']:
        if col in df.columns:
            industry_column = col
            break
    numeric_columns = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    if "股票代码" in numeric_columns:
        numeric_columns.remove("股票代码")

    # 1. 行业分布与指数概览
    st.markdown("### 行业分布与数字化转型指数概览")
    col1, col2 = st.columns([1, 1])
    with col1:
        if industry_column:
            tmp = df[industry_column].value_counts().reset_index()
            tmp.columns = [industry_column, '企业数量']
            fig_pie = px.pie(tmp, values='企业数量', names=industry_column,
                             title='各行业企业数量占比', template='plotly_white')
            st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        if numeric_columns:
            def_metric = "数字化转型总指数" if "数字化转型总指数" in numeric_columns else numeric_columns[0]
            fig_hist = px.histogram(df, x=def_metric, nbins=20,
                                    title=f'{def_metric}分布情况', template='plotly_white')
            fig_hist.add_vline(x=df[def_metric].mean(), line_dash="dash", line_color="red",
                               annotation_text="平均值", annotation_position="top left")
            fig_hist.add_vline(x=df[def_metric].median(), line_dash="dash", line_color="green",
                               annotation_text="中位数", annotation_position="top right")
            st.plotly_chart(fig_hist, use_container_width=True)

    # 2. 指标关联交互式分析
    st.markdown("### 数字化转型指标交互式关联分析")
    if len(numeric_columns) >= 2:
        x_def = "数字化转型总指数" if "数字化转型总指数" in numeric_columns else numeric_columns[0]
        y_def = "技术应用" if "技术应用" in numeric_columns else numeric_columns[1]
        x_col = st.selectbox("X轴指标", numeric_columns, index=numeric_columns.index(x_def))
        y_col = st.selectbox("Y轴指标", numeric_columns, index=numeric_columns.index(y_def))
        color_options = ["无分组"] + ([industry_column] if industry_column else [])
        color_by = st.selectbox("颜色分组", color_options, index=1 if industry_column else 0)
        hover_name = "企业名称" if "企业名称" in df.columns else "股票代码"
        fig_scatter = px.scatter(df, x=x_col, y=y_col,
                                 color=None if color_by == "无分组" else color_by,
                                 hover_name=hover_name,
                                 title=f'{x_col} 与 {y_col} 关联分析',
                                 template='plotly_white')
        if st.checkbox("显示趋势线"):
            fig_scatter = px.scatter(df, x=x_col, y=y_col, trendline="ols")
        st.plotly_chart(fig_scatter, use_container_width=True)

    # 3. 行业指标对比雷达图
    st.markdown("### 各行业数字化转型指标对比")
    if industry_column and numeric_columns:
        key_metrics = ["数字化转型总指数", "战略转型", "技术应用", "组织变革", "数据价值", "流程优化"]
        avail = [c for c in key_metrics if c in numeric_columns] or numeric_columns[:3]
        selected = st.multiselect("选择要比较的指标", avail, default=avail)
        if selected:
            radar_df = df.groupby(industry_column)[selected].mean().reset_index()
            radar_melt = pd.melt(radar_df, id_vars=[industry_column],
                                  value_vars=selected, var_name='指标', value_name='平均值')
            fig_radar = px.line_polar(radar_melt, r='平均值', theta='指标',
                                      color=industry_column, line_close=True,
                                      title='各行业数字化转型指标雷达图对比')
            st.plotly_chart(fig_radar, use_container_width=True)

    # 4. 企业排名榜单
    st.markdown("### 企业数字化转型排名榜单")
    if numeric_columns:
        rank_col = st.selectbox("选择排名指标", numeric_columns,
                                index=numeric_columns.index("数字化转型总指数") if "数字化转型总指数" in numeric_columns else 0)
        top_n = st.slider("显示数量", 5, 50, 10, 5)
        ascending = st.radio("排序方式", ["降序（从高到低）", "升序（从低到高）"], index=0) == "升序（从低到高）"
        ranking = df.sort_values(by=rank_col, ascending=ascending).head(top_n)
        display_cols = ["企业名称", "股票代码", rank_col] if "企业名称" in df.columns else ["股票代码", rank_col]
        st.dataframe(ranking[display_cols].reset_index(drop=True), use_container_width=True)

    return numeric_columns, industry_column

# ---------------- 企业查询（第一版原样） ----------------
def query_section(df, numeric_columns):
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
            st.warning("请输入查询内容", icon="⚠️")
            return
        query_text = query_text.strip()
        try:
            if query_by == "股票代码":
                if query_method == "精确查询":
                    matching_data = df[df["股票代码"] == int(query_text)]
                else:
                    matching_data = df[df["股票代码"].astype(str).str.contains(query_text)]
            else:
                if query_method == "精确查询":
                    matching_data = df[df["企业名称"] == query_text]
                else:
                    matching_data = df[df["企业名称"].str.contains(query_text, na=False)]
        except ValueError:
            st.error("股票代码需为整数", icon="🚨")
            return

        if matching_data.empty:
            st.warning("未找到符合条件的企业记录", icon="⚠️")
        else:
            st.subheader(f"查询结果：共找到{len(matching_data)}家企业")
            st.dataframe(matching_data, use_container_width=True, height=300)

# ---------------- 底部二维码（固定网址） ----------------
def show_qr_code():
    url = "https://hczjdm4tkq6cg9jsanhepj.streamlit.app/"
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
    st.set_page_config(page_title="数字化转型综合分析系统", layout="wide", page_icon="📊")
    st.title("人工智能板块上市公司数字化转型综合分析系统")
    st.markdown("""
    本系统通过交互式图表展示人工智能板块上市公司数字化转型整体情况，
    下方查询功能支持检索特定企业的详细数据。
    """, unsafe_allow_html=False)

    df = load_data()
    if df is not None:
        numeric_columns, industry_column = plot_overall_interactive_chart(df)
        query_section(df, numeric_columns)
    else:
        st.error("数据加载失败，请检查文件路径是否正确或文件格式是否支持", icon="🚨")

    show_qr_code()

if __name__ == "__main__":
    main()
