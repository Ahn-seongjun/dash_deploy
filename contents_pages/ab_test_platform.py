import streamlit as st
import pandas as pd
import numpy as np
import scipy.stats
from scipy.stats import norm
import altair as alt

st.set_page_config(
    page_title="A/B Testing App", initial_sidebar_state="expanded", layout="wide")

def conversion_rate(conversions, visitors):
    return (conversions / visitors) * 100


def lift(cra, crb):
    return ((crb - cra) / cra) * 100


def std_err(cr, visitors):
    return np.sqrt((cr / 100 * (1 - cr / 100)) / visitors)


def std_err_diff(sea, seb):
    return np.sqrt(sea ** 2 + seb ** 2)


def z_score(cra, crb, error):
    return ((crb - cra) / error) / 100


def p_value(z, hypothesis):
    if hypothesis == "One-sided" and z < 0:
        return 1 - norm().sf(z)
    elif hypothesis == "One-sided" and z >= 0:
        return norm().sf(z) / 2
    else:
        return norm().sf(z)


def significance(alpha, p):
    return "YES" if p < alpha else "NO"


def plot_chart(df):
    chart = (
        alt.Chart(df)
        .mark_bar(color="#61b33b")
        .encode(
            x=alt.X("Group:O", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Conversion:Q", title="Conversion rate (%)"),
            opacity="Group:O",
        )
        .properties(width=500, height=500)
    )

    # Place conversion rate as text above each bar
    chart_text = chart.mark_text(
        align="center", baseline="middle", dy=-10, color="black"
    ).encode(text=alt.Text("Conversion:Q", format=",.3g"))

    return st.altair_chart((chart + chart_text).interactive())


def style_negative(v, props=""):
    return props if v < 0 else None


def style_p_value(v, props=""):
    return np.where(v < st.session_state.alpha, "color:green;", props)


def calculate_significance(conversions_a, conversions_b, visitors_a, visitors_b, hypothesis, alpha):
    st.session_state.cra = conversion_rate(int(conversions_a), int(visitors_a))
    st.session_state.crb = conversion_rate(int(conversions_b), int(visitors_b))
    st.session_state.uplift = lift(st.session_state.cra, st.session_state.crb)
    st.session_state.sea = std_err(st.session_state.cra, float(visitors_a))
    st.session_state.seb = std_err(st.session_state.crb, float(visitors_b))
    st.session_state.sed = std_err_diff(st.session_state.sea, st.session_state.seb)
    st.session_state.z = z_score(
        st.session_state.cra, st.session_state.crb, st.session_state.sed
    )
    st.session_state.p = p_value(st.session_state.z, st.session_state.hypothesis)
    st.session_state.significant = significance(
        st.session_state.alpha, st.session_state.p
    )


st.write(
    """
# A/B Testing App
- 실험 데이터를 업로드하여 A/B test 진행
- 대시보드 출처) Streamlit Gallery
- 데이터 출처) https://www.kaggle.com/code/ekrembayar/a-b-testing-step-by-step-hypothesis-testing
"""
)

uploaded_file = st.file_uploader("Upload CSV", type=".csv")

use_example_file = st.checkbox(
    "예제 파일 활용", True, help="App 활용 예시로 예제 파일 제공"
)

ab_default = None
result_default = None

# If CSV is not uploaded and checkbox is filled, use values from the example file
# and pass them down to the next if block
if use_example_file:
    uploaded_file = "./data/cookie_cats.csv"
    ab_default = ["version"]
    result_default = ["retention_1"]


if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.markdown("### Data preview")
    st.dataframe(df.head())

    st.markdown("### 분석 대상 컬럼 선택")
    with st.form(key="my_form"):
        for i, col in enumerate(df.columns):
            if df[col].dtype == 'object' and df[col].nunique() == 2:
                col_default = i
        ab = st.selectbox("A/B column", options= df.columns, help="그룹 컬럼 선택(그룹 컬럼의 고유값은 2입니다.)",index = col_default)

        if ab:
            control = df[ab].unique()[0]
            treatment = df[ab].unique()[1]
            decide = st.radio(
                f" **{treatment}**가 Group B(처리집단) 인가요?",
                options=["Yes", "No"],
                #help="Select yes if this is group B (or the treatment group) from your test.",
            )
            if decide == "No":
                control, treatment = treatment, control
            visitors_a = df[ab].value_counts()[control]
            visitors_b = df[ab].value_counts()[treatment]
        bool_col_indices = [i for i, dtype in enumerate(df.dtypes) if dtype == bool]
        result = st.selectbox("Result column", options=df.columns, help = "결과 컬럼 선택(결과 컬럼의 형태는 Boolean이어야 함.)",index=bool_col_indices[0])

        if result:
            conversions_a = (
                df[[ab, result]].groupby(ab).agg("sum")[result][control]
            )
            conversions_b = (
                df[[ab, result]].groupby(ab).agg("sum")[result][treatment]
            )

        with st.expander("Adjust test parameters", expanded= True):
            st.markdown("### Parameters")
            st.radio(
                "Hypothesis type",
                options=["One-sided", "Two-sided"],
                index=0,
                key="hypothesis",
                help="양측검정/단측검정 옵션 선택",
            )
            st.slider(
                "Significance level (α)",
                min_value=0.01,
                max_value=0.10,
                value=0.05,
                step=0.01,
                key="alpha",
                help=" The probability of mistakenly rejecting the null hypothesis, if the null hypothesis is true. This is also called false positive and type I error. ",
            )

        submit_button = st.form_submit_button(label="Submit")

    if not ab or not result:
        st.warning("Please select both an **A/B column** and a **Result column**.")
        st.stop()

    # type(uploaded_file) == str, means the example file was used
    name = (
        "Website_Results.csv" if isinstance(uploaded_file, str) else uploaded_file.name
    )
    st.write("")
    st.write("## Results for A/B test from ", name)
    st.write("")

    # Obtain the metrics to display
    calculate_significance(
        conversions_a,
        conversions_b,
        visitors_a,
        visitors_b,
        st.session_state.hypothesis,
        st.session_state.alpha,
    )

    mcol1, mcol2 = st.columns(2)

    # Use st.metric to diplay difference in conversion rates
    with mcol1:
        st.metric(
            "Delta",
            value=f"{(st.session_state.crb - st.session_state.cra):.3g}%",
            delta=f"{(st.session_state.crb - st.session_state.cra):.3g}%",
        )
    # Display whether or not A/B test result is statistically significant
    with mcol2:
        st.metric("Significant?", value=st.session_state.significant)

    # Create a single-row, two-column DataFrame to use in bar chart


    #ncol1, ncol2 = st.columns([2, 1])
    ncol1, ncol2 = st.columns(2)
    with ncol1:
        results_df = pd.DataFrame(
            {
                "Group": ["Control", "Treatment"],
                "Conversion": [st.session_state.cra, st.session_state.crb],
            }
        )
        st.write("")
        st.write("")

        # Plot bar chart of conversion rates
        plot_chart(results_df)
    with ncol2:
        #ncol1, ncol2 = st.columns([2, 1])

        table = pd.DataFrame(
            {
                "Converted": [conversions_a, conversions_b],
                "Total": [visitors_a, visitors_b],
                "% Converted": [st.session_state.cra, st.session_state.crb],
            },
            index=pd.Index(["Control", "Treatment"]),
        )

        # Format "% Converted" column values to 3 decimal places
        table1 = ncol2.write(table.style.format(formatter={("% Converted"): "{:.3g}%"}))

        metrics = pd.DataFrame(
            {
                "p-value": [st.session_state.p],
                "z-score": [st.session_state.z],
                "uplift": [st.session_state.uplift],
            },
            index=pd.Index(["Metrics"]),
        )
    #with ncol3:
        # Color negative values red; color significant p-value green and not significant red
        table2 = ncol2.write(
            metrics.style.format(
                formatter={("p-value", "z-score"): "{:.3g}", ("uplift"): "{:.3g}%"}
            )
            .applymap(style_negative, props="color:red;")
            .apply(style_p_value, props="color:red;", axis=1, subset=["p-value"])
        )
