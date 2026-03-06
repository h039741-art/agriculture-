import streamlit as st
import pandas as pd
import json

# --- CONSTANTS & DOMAIN LOGIC (THE "CONTRACT") ---
CROP_RULES = {
    "TOMATO": {"ph": (6.0, 7.0), "key": "K", "threshold": 200},
    "WHEAT": {"ph": (6.0, 7.5), "key": "N", "threshold": 30},
    "RICE": {"ph": (5.0, 6.5), "key": "P", "threshold": 25},
    "MAIZE": {"ph": (5.8, 7.0), "key": "N", "threshold": 35}
}

UNIVERSAL_THRESHOLD = {"N": 20, "P": 15, "K": 150}
FERTILIZERS = {
    "N": "Apply Urea Fertilizer",
    "P": "Apply DAP (Diammonium Phosphate)",
    "K": "Apply MOP (Muriate of Potash)"
}

def calculate_agripulse(crop, n, p, k, ph):
    score = 100
    deficiencies = []
    actions = []
    
    rule = CROP_RULES[crop]
    
    # 1. pH Penalty (-20 pts) [cite: 84]
    if not (rule["ph"][0] <= ph <= rule["ph"][1]):
        score -= 20
        deficiencies.append("pH (Out of Range)")

    # 2. Standard Deficiency (-15 pts each) [cite: 85]
    if n < UNIVERSAL_THRESHOLD["N"]:
        score -= 15
        deficiencies.append("Nitrogen")
        actions.append(FERTILIZERS["N"])
    if p < UNIVERSAL_THRESHOLD["P"]:
        score -= 15
        deficiencies.append("Phosphorus")
        actions.append(FERTILIZERS["P"])
    if k < UNIVERSAL_THRESHOLD["K"]:
        score -= 15
        deficiencies.append("Potassium")
        actions.append(FERTILIZERS["K"])

    # 3. Critical Crop Penalty (-10 pts) [cite: 86]
    nutrient_vals = {"N": n, "P": p, "K": k}
    if nutrient_vals[rule["key"]] < rule["threshold"]:
        score -= 10
        if rule["key"] not in [d[0] for d in deficiencies]:
            deficiencies.append(f"{rule['key']} (Critical for {crop})")

    # Final Score & Health Status [cite: 97]
    score = max(0, score)
    health = "Optimal" if score >= 80 else "Deficient" if score >= 50 else "Critical"
    
    return {
        "score": float(score),
        "health": health,
        "deficiencies": deficiencies,
        "action": " & ".join(actions) if actions else "Soil health is optimal for planting."
    }

# --- FRONT END UI ---
st.set_page_config(page_title="AgriPulse | Precision Agriculture", layout="wide")

st.markdown("# 🌱 AgriPulse: AI-Powered Soil Analysis")
st.write("Translate raw chemical data into actionable planting strategies.")

# Sidebar for controls
st.sidebar.header("Deployment Settings")
selected_crop = st.sidebar.selectbox("Select Target Crop", list(CROP_RULES.keys()))
uploaded_file = st.sidebar.file_uploader("Upload Soil Data (.CSV)", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        # Ensure mandatory headers exist [cite: 90]
        required_cols = ['soil_id', 'nitrogen', 'phosphorus', 'potassium', 'ph_level']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Invalid CSV format. Required headers: {', '.join(required_cols)}")
        else:
            for _, row in df.iterrows():
                res = calculate_agripulse(selected_crop, row['nitrogen'], row['phosphorus'], row['potassium'], row['ph_level'])
                
                # Mandatory JSON Schema [cite: 105]
                result_json = {
                    "soil_id": str(row['soil_id']),
                    "target_crop": selected_crop,
                    "health_metrics": {
                        "overall_health": res["health"],
                        "critical_deficiencies": res["deficiencies"]
                    },
                    "recommendation": {
                        "fertilizer_plan": res["action"],
                        "suitability_score": res["score"]
                    },
                    "ai_explanation": f"The soil health is rated as {res['health']}. {res['action']} Biological necessity: {selected_crop} requires high levels of {CROP_RULES[selected_crop]['key']} for structural integrity."
                }

                # Color-Coded Dashboard [cite: 75, 115]
                color = "green" if res["health"] == "Optimal" else "orange" if res["health"] == "Deficient" else "red"
                
                with st.expander(f"Analysis for {row['soil_id']} - Score: {res['score']}%", expanded=True):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric("Suitability", f"{res['score']}%", delta=res["health"], delta_color="normal")
                        st.markdown(f"**Status:** :{color}[{res['health']}]")
                    with col2:
                        st.code(json.dumps(result_json, indent=2), language="json")
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("Waiting for CSV upload. Use the sidebar to upload your soil data.")
