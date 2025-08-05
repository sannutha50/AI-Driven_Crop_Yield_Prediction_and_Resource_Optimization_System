import pandas as pd
import joblib  
import streamlit as st

def crop_requirement():
    # Set Streamlit page configuration
    # st.set_page_config(page_title="🌾 Crop Requirements Predictor", page_icon="🌱", layout="wide")

    # Title with an icon
    st.title("🌱 Crop Requirements Predictor")
    st.write("Use AI to determine the water and temperature needs of your crops.")

    # Load dataset to get unique options
    original_df = pd.read_csv("../Crop_Requirement/crop_growth_updated_dataset.csv")
    crops = original_df['Crop'].unique()
    growth_stages = original_df['Growth Stage'].unique()
    soil_types = original_df['Soil Type'].unique()
    locations = original_df['Location'].unique()

    # Create dropdown menus for user input with icons
    col1, col2 = st.columns(2)

    with col1:
        selected_crop = st.selectbox("🌾 Select Crop", options=crops)
        selected_growth = st.selectbox("🌿 Select Growth Stage", options=growth_stages)

    with col2:
        selected_soil = st.selectbox("🪵 Select Soil Type", options=soil_types)
        selected_location = st.selectbox("📍 Select Location", options=locations)

    # Create input DataFrame
    input_df = pd.DataFrame([{
        'Crop': selected_crop,
        'Growth Stage': selected_growth,
        'Soil Type': selected_soil,
        'Location': selected_location
    }])

    # Prediction button with an icon
    if st.button("🔍 Predict Requirements"):
        try:
            # Load the scaler and encoder
            scaler_encoder = joblib.load("../Crop_Requirement/scaler.joblib")
            scaler = scaler_encoder['scaler']
            encoder = scaler_encoder['encoder']

            # One-hot encode the input data
            encoded_input = encoder.transform(input_df[['Crop', 'Growth Stage', 'Soil Type', 'Location']])
            encoded_input_df = pd.DataFrame(encoded_input, columns=encoder.get_feature_names_out(['Crop', 'Growth Stage', 'Soil Type', 'Location']))

            # Scale the encoded input data
            input_scaled = scaler.transform(encoded_input_df)

            # Load the models
            water_model = joblib.load("../Crop_Requirement/gb_water.joblib")
            gb_water = water_model['model']
            label_encoders_target_water = water_model['labels']
            temp_model = joblib.load("../Crop_Requirement/gb_temp.joblib")
            gb_temp = temp_model['model']
            label_encoders_target_temp = temp_model['labels']

            # Make predictions
            water_pred = gb_water.predict(input_scaled)[0]
            temp_pred = gb_temp.predict(input_scaled)[0]

            # Decode predictions to original labels
            water_req = list(label_encoders_target_water.keys())[water_pred]
            temp_req = list(label_encoders_target_temp.keys())[temp_pred]

            # Show predictions with icons
            st.success(f"💧 Predicted Water Requirement: {water_req}")
            st.success(f"🌡️ Predicted Temperature Requirement: {temp_req}")

            # Show confidence (probabilities)
            water_proba = gb_water.predict_proba(input_scaled)[0].max()
            temp_proba = gb_temp.predict_proba(input_scaled)[0].max()
            st.info(f"✅ Confidence: Water {water_proba:.1%}, Temperature {temp_proba:.1%}")
        
        except Exception as e:
            st.error(f"❌ Prediction error: {str(e)}")
    if st.button("🏠 Home"):
        st.session_state.page = "home"
