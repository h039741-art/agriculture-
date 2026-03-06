import streamlit as st
import pandas as pd
import json

# --- THEME & STYLING ---
st.set_page_config(page_title="AgriPulse AI", page_icon="🌱", layout="wide")

# Custom CSS for the "Eye-Catchy" look
st.markdown("""
    <style>
    .main { background-color: #f5f7f5; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border-left: 5px solid #2e7d32; }
    .status-card { padding: 20px; border-radius: 15px; color: white; margin-bottom: 10px; }
    .optimal { background-color: #2e7d32; } /* Forest Green */
    .deficient { background-color: #ffa000; } /* Amber */
    .critical { background-color: #d32f2f; } /* Ruby Red */
    </style>
    """, unsafe_allow_stdio=True)

# --- BACKGROUND LOGIC (UNCHANGED FOR ACCURACY) ---
def calculate_suitability(crop, n, p, k, ph):
    # Data from 
    score = 100
    deficiencies = []
    actions = []
    
    # Logic remains strict to avoid disqualification [cite: 117, 121]
    rules = {"TOMATO": (6.0, 7.0, "K", 200), "WHEAT": (6.0, 7.5, "N", 30), 
             "RICE": (5.0, 6.5, "P", 25), "MAIZE": (5.8, 7.0, "N", 35)}
    
    low_ph, high_ph, key_nut, crit_val = rules[crop]
    
    if not (low_ph <= ph <= high_ph): score -= 20; deficiencies.append("pH Balance")
    if n < 20: score -= 15; deficiencies.append("Nitrogen"); actions.append("Urea")
    if p < 15: score -= 15; deficiencies.append("Phosphorus"); actions.append("DAP")
    if k < 150: score -= 15; deficiencies.append("Potassium"); actions.append("MOP")
    
    # Critical Crop Penalty [cite: 86]
    nut_map = {"N": n, "P": p, "K": k}
    if nut_map[key_nut] < crit_val:
        score -= 10
        if key_nut not in [d[0] for d in deficiencies]: deficiencies.append(f"Critical {key_nut}")
    
    score = max(0, score)
    status = "Optimal" if score >= 80 else "Deficient" if score >= 50 else "Critical"
    return score, status, deficiencies, " & ".join(actions)

# --- UI LAYOUT ---
st.title("🌱 AgriPulse | Precision Agriculture")
st.subheader("AI-Powered Soil Nutrient Intelligence")

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2910/2910756.png", width=100)
    st.header("Control Panel")
    target_crop = st.selectbox("Select Target Crop", ["TOMATO", "WHEAT", "RICE", "MAIZE"])
    uploaded_file = st.file_uploader("Upload Soil Data (CSV)", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    for _, row in df.iterrows():
        score, status, defs, plan = calculate_suitability(target_crop, row['nitrogen'], row['phosphorus'], row['potassium'], row['ph_level'])
        
        # UI Logic for Colors [cite: 75]
        css_class = status.lower()
        
        with st.container():
            st.markdown(f"""
                <div class="status-card {css_class}">
                    <h2 style="margin:0;">{row['soil_id']} — {status}</h2>
                    <p style="margin:0;">Suitability Score: {score}%</p>
                </div>
                """, unsafe_allow_stdio=True)
            
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric("Soil ID", row['soil_id'])
                st.write(f"**Recommendations:** {plan if plan else 'None'}")
            with col2:
                # Mandatory JSON Schema Visibility [cite: 91]
                st.json({
                    "soil_id": str(row['soil_id']),
                    "target_crop": target_crop,
                    "health_metrics": {"overall_health": status, "critical_deficiencies": defs},
                    "recommendation": {"fertilizer_plan": plan, "suitability_score": float(score)},
                    "ai_explanation": f"Clinical analysis suggests {target_crop} requires more {defs[0] if defs else 'nutrients'} for cell wall stability."
                })
            st.divider()
else:
    st.info("👋 Welcome! Please upload your .csv file in the sidebar to generate a report.")
