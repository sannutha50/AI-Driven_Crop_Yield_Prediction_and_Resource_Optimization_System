import pickle
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import os

def crop_prediction():
    model_path = os.path.join(os.path.dirname(__file__), "RandomForest.pkl")
    with open(model_path, "rb") as model_file:
        model = pickle.load(model_file)

    #st.set_page_config(page_title="Crop Prediction", layout="centered")

    st.markdown(
        """
        <h1 style="text-align: center; color: #2C3E50;">🌱 Crop Prediction 🌱</h1>
        <p style="text-align: center; font-size: 18px; color: #7D3C98;">Predict the best crop for your field based on soil and weather conditions.</p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("prediction_form", border=True):
        st.markdown("### **Enter Feature Values**")

        features = {}
        fields = {
            "N": "Nitrogen (N)", 
            "P": "Phosphorus (P)", 
            "K": "Potassium (K)", 
            "temperature": "Temperature (°C)", 
            "humidity": "Humidity (%)", 
            "ph": "Soil pH", 
            "rainfall": "Rainfall (mm)"
        }

        for key, label in fields.items():
            if key == "ph":
                features[key] = st.number_input(f"{label}", min_value=0.0, max_value=14.0, step=0.1)
            else:
                features[key] = st.number_input(f"{label}", min_value=0.0, step=0.1)

        submit_button = st.form_submit_button("Predict", type="primary")

    if st.button("🏠 Home"):
        st.session_state.page = "home"
        
    if submit_button:
        features_array = np.array(list(features.values())).reshape(1, -1)
        prediction = model.predict(features_array)[0]
        probabilities = model.predict_proba(features_array)[0]  # Get confidence scores
        classes = model.classes_  # Crop labels
        
        # Get the predicted crop's confidence
        confidence = probabilities[np.where(classes == prediction)][0] * 100
        
        st.markdown(
            f"""
            <div style="text-align: center; padding: 20px; background-color: #D4EDDA; border-radius: 12px; color: #155724; font-size: 20px;">
                <h3>🌾 The Predicted Crop is: {prediction.capitalize()} 🌾</h3>
                <h4>Confidence: {confidence:.2f}%</h4>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        # Improved Visualization of confidence scores
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.barplot(x=classes, y=probabilities * 100, palette="coolwarm", ax=ax)
        ax.set_xlabel("Crops", fontsize=14, fontweight='bold')
        ax.set_ylabel("Confidence (%)", fontsize=14, fontweight='bold')
        ax.set_title("🌾 Confidence Levels for Different Crops 🌾", fontsize=16, fontweight='bold', color='#2C3E50')
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.yticks(fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        st.pyplot(fig)
