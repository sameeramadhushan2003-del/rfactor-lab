import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="rFactor Lab",
    page_icon="📊",
    layout="wide"
)


# =========================================================
# FILES
# =========================================================

AUTOPSY_FILE = Path(
    "data/factor_autopsy_summary.csv"
)

EXECUTION_FILE = Path(
    "data/v2_turnover_cap_final_validation.csv"
)

CANDIDATE_FILE = Path(
    "data/v2_development_factor_candidates.csv"
)

REPORT_FILE = Path(
    "factor_autopsy_report.md"
)


# =========================================================
# TITLE
# =========================================================

st.title("📊 rFactor Lab")

st.caption(
    "Research, validation and autopsy framework "
    "for Bitget Reality rToken factors"
)


# =========================================================
# LOAD DATA
# =========================================================

autopsy = pd.read_csv(
    AUTOPSY_FILE
)

execution = pd.read_csv(
    EXECUTION_FILE
)

candidates = pd.read_csv(
    CANDIDATE_FILE
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title(
    "rFactor Lab"
)

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Factor Validation",
        "Execution",
        "Factor Autopsy"
    ]
)


# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    st.header(
        "Research Overview"
    )


    col1, col2, col3, col4 = st.columns(4)


    col1.metric(
        "Final Factor",
        "1H Reversal"
    )


    col2.metric(
        "Development IC",
        "-0.0744"
    )


    col3.metric(
        "Validation IC",
        "-0.0351"
    )


    col4.metric(
        "Final Holdout IC",
        "-0.0708"
    )


    st.divider()


    st.subheader(
        "What did rFactor Lab discover?"
    )


    st.write(
        """
        The research discovered a persistent
        **short-term cross-sectional reversal effect**
        across Bitget Reality rTokens.

        rTokens that performed strongly during the
        previous hour tended to rank weaker during
        the following hour, while recent relative
        losers tended to recover.
        """
    )


    st.subheader(
        "Research Pipeline"
    )


    st.code(
        """
2,587 Reality pairs
        ↓
90 weekend-tradable assets
        ↓
Historical coverage analysis
        ↓
365-day V2 dataset
        ↓
23 quality-approved assets
        ↓
14 Development assets
        ↓
4 walk-forward folds
        ↓
6 Validation assets
        ↓
65-day future holdout
        ↓
AMD / GLW / META asset holdout
        ↓
Factor Autopsy
        """
    )


    st.info(
        "The factor was frozen before validation "
        "and holdout testing."
    )


# =========================================================
# FACTOR VALIDATION
# =========================================================

elif page == "Factor Validation":

    st.header(
        "Factor Validation"
    )


    st.write(
        """
        **Information Coefficient (IC)** measures how
        well the factor ranking predicts the ranking
        of future returns.

        Negative IC is expected for the reversal factor.
        """
    )


    display = autopsy.copy()


    display[
        "mean_ic"
    ] = display[
        "mean_ic"
    ].round(4)


    display[
        "median_ic"
    ] = display[
        "median_ic"
    ].round(4)


    st.dataframe(
        display,
        use_container_width=True
    )


    fig = px.bar(
        autopsy,
        x="stage",
        y="mean_ic",
        title="Mean IC Across Research Stages"
    )


    fig.add_hline(
        y=0
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.success(
        """
        The IC remained negative during Development,
        Validation, Final Time Holdout and Final
        Asset Holdout.
        """
    )


# =========================================================
# EXECUTION
# =========================================================

elif page == "Execution":

    st.header(
        "Portfolio Execution"
    )


    st.write(
        """
        Frozen portfolio:

        - Long bottom 25% of 1-hour momentum
        - Short top 25%
        - Cross-sectional market-neutral design
        - Maximum hourly turnover = 0.50
        """
    )


    cost = st.selectbox(
        "Transaction cost assumption",
        sorted(
            execution[
                "cost_bps"
            ].unique()
        )
    )


    filtered = execution[
        execution[
            "cost_bps"
        ]
        ==
        cost
    ].copy()


    st.dataframe(
        filtered,
        use_container_width=True
    )


    fig = px.bar(
        filtered,
        x="test",
        y="cumulative_return_pct",
        title=(
            f"Cumulative Return — {cost} bps"
        ),
        text_auto=".2f"
    )


    fig.add_hline(
        y=0
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.subheader(
        "Transaction Cost Sensitivity"
    )


    fig2 = px.line(
        execution,
        x="cost_bps",
        y="cumulative_return_pct",
        color="test",
        markers=True,
        title="Return vs Transaction Cost"
    )


    fig2.add_hline(
        y=0
    )


    st.plotly_chart(
        fig2,
        use_container_width=True
    )


    st.warning(
        """
        The factor produces strong gross returns,
        but performance deteriorates as transaction
        costs increase because the signal requires
        frequent rebalancing.
        """
    )


# =========================================================
# FACTOR AUTOPSY
# =========================================================

elif page == "Factor Autopsy":

    st.header(
        "🧪 Factor Autopsy"
    )


    col1, col2 = st.columns(2)


    with col1:

        st.subheader(
            "Factor Status"
        )

        st.success(
            "VALIDATED"
        )

        st.write(
            """
            The reversal relationship survived:

            - Four development folds
            - Different validation assets
            - Future-time validation
            - Future-time holdout
            - Separate-asset holdout
            """
        )


    with col2:

        st.subheader(
            "Implementation Status"
        )

        st.warning(
            "COST-SENSITIVE"
        )

        st.write(
            """
            The economic implementation is limited
            by high turnover and transaction-cost
            sensitivity.
            """
        )


    st.divider()


    st.subheader(
        "Why this matters"
    )


    st.write(
        """
        A statistically strong factor does not
        automatically mean a profitable trading
        strategy.

        rFactor Lab separates:

        **Factor discovery**

        from

        **economic implementation**

        and reports when transaction costs destroy
        an otherwise persistent predictive effect.
        """
    )


    if REPORT_FILE.exists():

        st.divider()

        st.subheader(
            "Full Autopsy Report"
        )

        report = REPORT_FILE.read_text(
            encoding="utf-8"
        )

        st.markdown(
            report
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "rFactor Lab — Bitget Reality Factor Research"
)