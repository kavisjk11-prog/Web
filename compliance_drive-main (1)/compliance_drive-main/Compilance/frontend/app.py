# frontend/app.py
import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:5000"

# ---------- Page Config ----------
st.set_page_config(page_title="Invoicing ROI Simulator", page_icon="💸", layout="wide")

# ---------- Global CSS ----------
st.markdown(
    """
    <style>
    /* Background */
    .stApp { background: linear-gradient(to bottom, #f0f4f8, #ffffff); }

    /* Input boxes */
    div.stTextInput > label, div.stNumberInput > label {
        color: #111827 !important;  /* dark text for labels */
        font-weight: 600;
    }

    div.stTextInput > div > input, div.stNumberInput > div > input {
        background-color: #f9fafb !important;  /* light background for input */
        color: #111827 !important;            /* dark input text */
        border-radius: 8px;
        padding: 5px 10px;
    }

    /* Buttons */
    .stButton>button {
        background-color: #2563EB !important;
        color: white !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #1d4ed8 !important;
        color: #ffffff !important;
    }

    /* Headers / Titles */
    h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #111827 !important;  /* dark headers */
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True
)

# ---------- Page Title ----------
st.title("💸 Invoicing ROI Simulator")
st.write("Visualize **savings**, **ROI**, and **payback** when automating invoice processing.")

# ---------- Input Section ----------
st.header("Input Parameters ✏️")
scenario_name = st.text_input("Scenario Name", "Demo Scenario")
monthly_invoice_volume = st.number_input("Monthly Invoices", 100, 100000, 2000)
num_ap_staff = st.number_input("AP Staff", 1, 50, 3)
avg_hours_per_invoice = st.number_input("Avg Hours/Invoice", 0.01, 5.0, 0.17, step=0.01)
hourly_wage = st.number_input("Hourly Wage ($)", 1, 500, 30)
error_rate_manual = st.number_input("Error Rate (Manual %)", 0.0, 100.0, 0.5)
error_cost = st.number_input("Error Fix Cost ($)", 0, 10000, 100)
time_horizon_months = st.number_input("Time Horizon (Months)", 1, 360, 36)
one_time_cost = st.number_input("Implementation Cost ($)", 0, 1000000, 50000)

# ---------- Run Simulation ----------
if st.button("Run Simulation"):
    payload = {
        "scenario_name": scenario_name,
        "monthly_invoice_volume": monthly_invoice_volume,
        "num_ap_staff": num_ap_staff,
        "avg_hours_per_invoice": avg_hours_per_invoice,
        "hourly_wage": hourly_wage,
        "error_rate_manual": error_rate_manual,
        "error_cost": error_cost,
        "time_horizon_months": time_horizon_months,
        "one_time_implementation_cost": one_time_cost,
    }
    with st.spinner("Calculating..."):
        try:
            response = requests.post(f"{API}/simulate", json=payload, timeout=10)
            response.raise_for_status()
            results = response.json()
            st.session_state.results = results
            st.success("Simulation Complete ✅")
        except Exception as e:
            st.error(f"Simulation failed: {str(e)}")
            st.session_state.results = None

# ---------- Show Results ----------
results = st.session_state.get("results")
if results:
    st.markdown("### Key Metrics")
    col1, col2, col3 = st.columns(3)

    # Dynamic colors for KPI values
    def color_value(val):
        if val >= 0:
            return "#22c55e"  # green positive
        else:
            return "#ef4444"  # red negative

    with col1:
        st.markdown(f"""
        <div class="card">
        <h3>Monthly Savings</h3>
        <h1 style="color:{color_value(results.get('monthly_savings',0))}">${results.get('monthly_savings',0):,.2f}</h1>
        <p class="muted">Estimated monthly cost reduction</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="card">
        <h3>Payback</h3>
        <h1 style="color:{color_value(-results.get('payback_months',0))}">{results.get('payback_months','-')}</h1>
        <p class="muted">Months to recoup investment</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="card">
        <h3>ROI</h3>
        <h1 style="color:{color_value(results.get('roi_percentage',0))}">{results.get('roi_percentage','-')}%</h1>
        <p class="muted">Return over projection period</p>
        </div>
        """, unsafe_allow_html=True)

    # Cumulative savings chart
    st.markdown("### Savings Projection Over Time")
    monthly_savings = results.get("monthly_savings", 0)
    months = time_horizon_months
    cumulative_savings = [monthly_savings*(i+1) for i in range(months)]
    chart_data = pd.DataFrame({
        "Month": list(range(1, months+1)),
        "Cumulative Savings": cumulative_savings
    })
    st.line_chart(chart_data.rename(columns={"Month": "index"}).set_index("index"))

    # Detailed JSON
    with st.expander("Show Detailed Numbers"):
        st.json(results)

    # Save Scenario & Report
    st.markdown("### Save Scenario / Generate Report")
    save_name = st.text_input("Scenario Name to Save", value=scenario_name)
    email = st.text_input("Email for Report")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("Save Scenario"):
            save_payload = {"scenario_name": save_name, "inputs": payload, "results": results}
            try:
                s = requests.post(f"{API}/scenarios", json=save_payload, timeout=5)
                if s.status_code in (200,201):
                    st.success("Scenario Saved ✅")
                else:
                    st.error("Failed to save scenario")
            except Exception as e:
                st.error(str(e))
    with col2:
        if st.button("Generate Report"):
            if not email:
                st.warning("Please enter an email first")
            else:
                try:
                    rep_payload = {"email": email, "scenario": {"scenario_name": save_name, "inputs": payload, "results": results}}
                    rr = requests.post(f"{API}/report/generate", json=rep_payload, timeout=10)
                    rr.raise_for_status()
                    st.success("Report generated! ✅")
                    st.write("Report Info:", rr.json())
                except Exception as e:
                    st.error("Failed to generate report: "+str(e))
