import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Debt Dynamics Dashboard", page_icon="📊", layout="wide")

st.title("📊 Debt Dynamics Dashboard")
st.markdown("An interactive exploration of debt, GDP, and leverage over time.")


import pandas as pd
import streamlit as st

st.set_page_config(page_title="Debt Dashboard")

@st.cache_data
def load_data():
    data = {
        "Year": list(range(2010, 2021)),
        "GDP": [500,520,540,560,580,600,620,640,660,680,700],
        "ExternalDebt": [50,60,70,80,90,100,110,120,130,140,150],
        "DomesticDebt": [100,105,110,115,120,125,130,135,140,145,150],
    }
    df = pd.DataFrame(data)
    df["TotalDebt"] = df["ExternalDebt"] + df["DomesticDebt"]
    df["DebtToGDP"] = (df["TotalDebt"]/df["GDP"]).round(3)
    return df

df = load_data()


# ---------- Sidebar controls
st.sidebar.title("Controls")
year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Select year range",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max),
    step=1,
)
ma_on = st.sidebar.checkbox("Show 3-year moving averages (lines)", value=True)
normalize = st.sidebar.selectbox(
    "Normalize composition by", ["Absolute (bn)", "Share of Total (%)"]
)
show_annotations = st.sidebar.checkbox("Annotate notable points", value=True)

df = df[(df["Year"] >= year_range[0]) & (df["Year"] <= year_range[1])].copy()

# ---------- Top KPIs
latest = df.sort_values("Year").iloc[-1]
prev = df.sort_values("Year").iloc[-2] if len(df) > 1 else latest
delta_debt = latest["TotalDebt"] - prev["TotalDebt"]
delta_ratio = latest["DebtToGDP"] - prev["DebtToGDP"]
col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Year", int(latest["Year"]))
col2.metric("Total Debt (bn)", f"{latest['TotalDebt']:.0f}", f"{delta_debt:+.0f} vs prev")
col3.metric("Debt-to-GDP", f"{latest['DebtToGDP']:.2f}", f"{delta_ratio:+.02f}")
col4.metric("GDP (bn)", f"{latest['GDP']:.0f}")

# ---------- Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Composition", "Changes", "Trends", "Insights"]
)

with tab1:
    st.subheader("Treemap of Total Debt and Debt-to-GDP Ratio")
    tdf = df.copy()
    tdf["label"] = tdf["Year"].astype(str)
    fig_treemap = px.treemap(
        tdf,
        path=["label"],
        values="TotalDebt",
        color="DebtToGDP",
        color_continuous_scale="Viridis",
        hover_data={"TotalDebt": ":.0f", "DebtToGDP": ":.2f", "label": False},
    )
    fig_treemap.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=380)
    st.plotly_chart(fig_treemap, use_container_width=True)

    st.subheader("Debt vs GDP with Debt-to-GDP Indicator")
    fig_scatter = px.scatter(
        df,
        x="GDP",
        y="TotalDebt",
        size="DebtToGDP",
        color="Year",
        hover_data={"DebtToGDP": ":.2f", "GDP": ":.0f", "TotalDebt": ":.0f"},
        color_continuous_scale="Plasma",
    )
    if show_annotations:
        # annotate the latest year
        last = df.sort_values("Year").iloc[-1]
        fig_scatter.add_annotation(
            x=last["GDP"],
            y=last["TotalDebt"],
            text=f"{int(last['Year'])} (latest)",
            showarrow=True,
            arrowhead=2,
        )
    fig_scatter.update_layout(height=380, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("Debt Composition")
    comp = df.melt(
        id_vars=["Year", "GDP", "TotalDebt", "DebtToGDP"],
        value_vars=["ExternalDebt", "DomesticDebt"],
        var_name="Type",
        value_name="Amount",
    )
    if normalize == "Share of Total (%)":
        comp["Amount"] = (comp["Amount"] / comp["TotalDebt"] * 100).round(2)
        yaxis_title = "Share (%)"
    else:
        yaxis_title = "Amount (bn)"
    fig_comp = px.area(
        comp,
        x="Year",
        y="Amount",
        color="Type",
        groupnorm="percent" if normalize == "Share of Total (%)" else None,
        hover_data={"Amount": ":.2f"},
    )
    fig_comp.update_layout(
        yaxis_title=yaxis_title, height=400, margin=dict(l=0, r=0, t=0, b=0)
    )
    st.plotly_chart(fig_comp, use_container_width=True)

with tab3:
    st.subheader("Year-over-Year Changes")
    dy = df.sort_values("Year").set_index("Year").diff().fillna(0)
    dy = dy[["ExternalDebt", "DomesticDebt", "TotalDebt", "DebtToGDP"]].reset_index()
    dy_long = dy.melt(id_vars=["Year"], var_name="Metric", value_name="Change")
    fig_heat = px.imshow(
        dy_long.pivot(index="Metric", columns="Year", values="Change"),
        aspect="auto",
        color_continuous_scale="RdBu",
        origin="lower",
    )
    fig_heat.update_layout(height=380, margin=dict(l=0, r=0, t=0, b=0))
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("**Waterfall: Annual Contributions to Total Debt Growth**")
    wd = dy[["Year", "TotalDebt"]].rename(columns={"TotalDebt": "Delta"})
    measure = ["relative"] * len(wd)
    measure[0] = "absolute"
    fig_wf = go.Figure(
        go.Waterfall(
            x=wd["Year"].astype(str),
            measure=measure,
            y=wd["Delta"],
            text=[f"{v:.0f}" for v in wd["Delta"]],
            connector={"line": {"width": 1}},
        )
    )
    fig_wf.update_layout(
        height=360, margin=dict(l=0, r=0, t=0, b=0), yaxis_title="Change (bn)"
    )
    st.plotly_chart(fig_wf, use_container_width=True)

with tab4:
    st.subheader("Debt Dynamics Over Time")
    fig_line = go.Figure()
    for col, name in [
        ("ExternalDebt", "External Debt"),
        ("DomesticDebt", "Domestic Debt"),
        ("DebtToGDP", "Debt-to-GDP"),
    ]:
        fig_line.add_trace(
            go.Scatter(x=df["Year"], y=df[col], mode="lines+markers", name=name)
        )
        if ma_on:
            ma = df[col].rolling(3, min_periods=1).mean()
            fig_line.add_trace(
                go.Scatter(
                    x=df["Year"],
                    y=ma,
                    mode="lines",
                    name=f"{name} 3Y MA",
                    line=dict(dash="dash"),
                )
            )
    fig_line.update_layout(
        height=420, margin=dict(l=0, r=0, t=0, b=0), yaxis_title="Amount / Ratio"
    )
    st.plotly_chart(fig_line, use_container_width=True)

with tab5:
    st.markdown(
        '''
        ### What to notice
        - **Steady leverage:** Total debt rises about 15bn per year; the **Debt-to-GDP** ratio edges up from ~0.30 to ~0.43, indicating debt growing slightly faster than GDP.
        - **Mix shift:** Domestic debt remains the larger share, but external debt grows faster, narrowing the gap.
        - **Efficiency lens:** Use the scatter (Debt vs GDP) to check whether higher debt years also coincide with stronger GDP; the upward slope suggests co-movement, but ratio bubbles reveal leverage risk.
        - **Volatility check:** Turn on *3-year MAs* to smooth noise and spot medium-term trend breaks.
        - **Scenario analysis:** Adjust the year range to focus on sub-periods (e.g., 2013–2016) and see how composition and growth dynamics change.
        '''
    )
    st.info(
        "Tip: All charts react to the sidebar filters. Hover on points/areas for granular tooltips, and use the legend to toggle series."
    )

st.caption("Built with Streamlit + Plotly | Data is illustrative.")
