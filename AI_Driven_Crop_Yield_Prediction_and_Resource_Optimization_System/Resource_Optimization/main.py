import streamlit as st
import pandas as pd
import mysql.connector
import matplotlib.pyplot as plt
from datetime import datetime
from auth_utils import login_user, register_user
from email_utils import send_mail
import google.generativeai as genai
from graphviz import Digraph
import textwrap
import re
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

#rom app import crop_prediction

st.markdown('<style>' + open('styles.css').read() + '</style>', unsafe_allow_html=True)


# MySQL Connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Cpk@02042003",
        database="resource_optimization"
    )

# Initialize session states
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'email_history' not in st.session_state:
    st.session_state.email_history = []

# Database fetch functions
def fetch_resources():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM resources", conn)
    conn.close()
    return df

# ---------- Login/Register ----------
def login_register():
    st.title("🌾 AI-Powered Crop Yield Prediction & Resource Optimization")
    option = st.radio("Choose option", ["Login", "Register"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if option == "Login":
        if st.button("Login"):
            if login_user(email, password):
                st.session_state.page = "home"
                st.success("✅ Logged in successfully!")
            else:
                st.error("❌ Invalid credentials.")

    elif option == "Register":
        if st.button("Register"):
            if register_user(email, password):
                st.success("✅ Registered! Now log in.")
            else:
                st.warning("⚠️ Email already exists.")

# ---------- Home ----------
def home():
    st.title("🏡 Home - AI Resource System")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🌾 Crop Yield Prediction"):
            st.session_state.page = "crop_yield"
        if st.button("🧪 Crop Recommendation"):
            st.session_state.page = "crop_recommendation"
            # st.success("➡️ Go to the sidebar and click on 'Crop Recommendation'")
        if st.button("🌡️ Requirement Estimation"):
            st.session_state.page = "crop_requirements"
    with col2:
        if st.button("🔄 Update Resource"):
            st.session_state.page = "update"
        if st.button("📦 Request Resource"):
            st.session_state.page = "request"
        if st.button("🤖 Ask Bot"):
            st.session_state.page = "ask_bot"

# ---------- Update Resource ----------
def update_resource():
    st.title("🔄 Update Resource")
    df = fetch_resources()
    st.dataframe(df)

    new_data = {}
    with st.form("update_form"):
        for _, row in df.iterrows():
            qty = st.number_input(f"{row['resource']}", min_value=0, value=int(row['quantity']))
            new_data[row['resource']] = qty
        submitted = st.form_submit_button("Update")

    if submitted:
        conn = get_connection()
        cursor = conn.cursor()
        for res, new_qty in new_data.items():
            cursor.execute("SELECT quantity FROM resources WHERE resource = %s", (res,))
            old_qty = cursor.fetchone()[0]
            if old_qty != new_qty:
                cursor.execute("UPDATE resources SET quantity = %s WHERE resource = %s", (new_qty, res))
                cursor.execute("INSERT INTO resource_updates (resource, old_quantity, new_quantity) VALUES (%s, %s, %s)",
                               (res, old_qty, new_qty))
        conn.commit()
        conn.close()
        st.success("✅ Resources updated successfully!")

    if st.button("📜 Show Recent Updates"):
        conn = get_connection()
        updates = pd.read_sql("SELECT * FROM resource_updates ORDER BY updated_at DESC LIMIT 10", conn)
        conn.close()
        st.dataframe(updates)

    if st.button("🏠 Home"):
        st.session_state.page = "home"

# ---------- Request Resource ----------
def request_resource():
    st.title("📦 Request Resources")
    df = fetch_resources()
    st.dataframe(df)

    st.subheader("🧾 Personal Info")
    name = st.text_input("Name")
    contact = st.text_input("Contact No.")
    street = st.text_input("Street")

    st.subheader("📧 Manager Emails")
    fert_email = st.text_input("Fertilizer, Pesticide, Seeds Manager Email")
    mach_email = st.text_input("Machinery & Labour Manager Email")

    required = {}
    with st.form("request_form"):
        for _, row in df.iterrows():
            req = st.number_input(f"Required {row['resource']}", min_value=0, key=row['resource'])
            required[row['resource']] = req
        submit = st.form_submit_button("Submit Request")

    if submit:
        conn = get_connection()
        cursor = conn.cursor()
        shortages_fert = {}
        shortages_mach = {}
        all_ok = True

        for res, qty in required.items():
            cursor.execute("SELECT quantity FROM resources WHERE resource = %s", (res,))
            available = cursor.fetchone()[0]
            if available < qty:
                all_ok = False
                if res in ["Fertilizer (kg)", "Pesticides (liters)", "Seeds (kg)"]:
                    shortages_fert[res] = qty - available
                else:
                    shortages_mach[res] = qty - available

        contact_info = f"\n\nContact Info:\nName: {name}\n📞 {contact}\n🏡 {street}"
        if shortages_fert and fert_email:
            body = "Dear Manager,\nShortage in the following resources:\n" + \
                   "\n".join([f"{k}: Need {v} more" for k, v in shortages_fert.items()]) + contact_info
            subject = "🚨 Shortage Alert - F/P/S"
            result = send_mail(subject, body, fert_email)
            st.info(result)
            st.session_state.email_history.append(f"{datetime.now()} - Sent to {fert_email}: {subject}")

        if shortages_mach and mach_email:
            body = "Dear Manager,\nShortage in the following resources:\n" + \
                   "\n".join([f"{k}: Need {v} more" for k, v in shortages_mach.items()]) + contact_info
            subject = "🚨 Shortage Alert - M/L"
            result = send_mail(subject, body, mach_email)
            st.info(result)
            st.session_state.email_history.append(f"{datetime.now()} - Sent to {mach_email}: {subject}")

        if all_ok:
            for res, qty in required.items():
                cursor.execute("UPDATE resources SET quantity = quantity - %s WHERE resource = %s", (qty, res))
            st.success("✅ All resources allocated!")
            conn.commit()

        # Save request log
        cursor.execute("INSERT INTO resource_requests (requested_data) VALUES (%s)", (str(required),))
        conn.commit()
        conn.close()

    if st.button("📈 Show Visualization"):
        visualize_bar_chart(df, required)

    if st.button("📜 Previous Requests"):
        conn = get_connection()
        logs = pd.read_sql("SELECT * FROM resource_requests ORDER BY timestamp DESC LIMIT 10", conn)
        conn.close()
        st.dataframe(logs)

    if st.session_state.email_history:
        st.subheader("📨 Sent Emails")
        for mail in st.session_state.email_history:
            st.write(mail)

    if st.button("🏠 Home"):
        st.session_state.page = "home"

# ---------- Visualization ----------
def visualize_bar_chart(available_df, requested):
    st.subheader("📊 Resource Comparison")
    resources = available_df['resource'].tolist()
    available_qty = available_df['quantity'].tolist()
    requested_qty = [requested[res] for res in resources]

    fig, ax = plt.subplots(figsize=(10, 4))
    index = range(len(resources))
    bar_width = 0.35

    ax.bar(index, available_qty, bar_width, label='Available', color='green')
    ax.bar([i + bar_width for i in index], requested_qty, bar_width, label='Requested', color='red')
    ax.set_xticks([i + bar_width / 2 for i in index])
    ax.set_xticklabels(resources, rotation=45)
    ax.set_ylabel("Quantity")
    ax.set_title("Available vs Requested")
    ax.legend()
    st.pyplot(fig)

def ask_bot():
    import streamlit as st
    import google.generativeai as genai
    from graphviz import Digraph
    import textwrap
    import re

    # 🔐 Gemini API key
    GEMINI_API_KEY = "AIzaSyDJ1tewK5Hpt-DrLhT67NLCmj7AcvXnRHc"

    # Configure Gemini
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")
    except Exception as e:
        st.error(f"❌ Failed to configure Gemini: {str(e)}")
        return

    # 🌳 Tree Diagram
    def create_tree_diagram(title, points):
        try:
            dot = Digraph(comment='AgriBot Diagram')
            dot.attr(rankdir='TB', size='12,14')
            dot.attr('node', shape='box', style='filled',
                     fillcolor='#E8F5E9', fontname='Arial',
                     fontsize='14', margin='0.3', width='1.5', height='0.5')
            dot.node('A', "\n".join(textwrap.wrap(title, 18)), fontsize='16',
                     fillcolor='#81C784', penwidth='2', color='#2E7D32')

            for i, point in enumerate(points, start=1):
                node_id = f"N{i}"
                clean_point = re.sub(r'^[-•*]\s*', '', point).strip()
                label = "\n".join(textwrap.wrap(clean_point, 20))
                dot.node(node_id, label, fontsize='13', fillcolor='#F1F8E9')
                dot.edge('A', node_id, arrowsize='0.8', penwidth='1.2')

            return dot
        except Exception as e:
            st.error(f"Diagram creation error: {str(e)}")
            return None

    # 💬 UI Section
    # st.set_page_config(page_title="AgriBot", page_icon="🌿", layout="centered")
    st.markdown("""<h1 style='text-align: center; color: green; font-size: 2.5rem;'>🌿 Beginner's Agriculture Guide</h1>
        <p style='text-align: center; font-size: 1.1rem;'>Simple answers with visual diagrams for new farmers</p>""", unsafe_allow_html=True)
    st.divider()

    st.subheader("💬 Try These Common Questions")
    faqs = [
        "How to start a small vegetable garden?",
        "Natural ways to remove pests?",
        "Best crops for beginners?",
        "How often should I water plants?",
        "Easy composting methods?",
        "When to harvest vegetables?"
    ]

    cols = st.columns(2)
    for i, faq in enumerate(faqs):
        if cols[i % 2].button(faq, use_container_width=True):
            st.session_state.question = faq

    st.subheader("📝 Ask Your Farming Question")
    question = st.text_area("Type your question here:", value=st.session_state.get("question", ""), height=120)

    if st.button("Generate Explanation 🌱", use_container_width=True):
        if not question.strip():
            st.warning("Please enter a question")
        else:
            with st.spinner("Creating explanation..."):
                try:
                    desc_prompt = f"""Provide a beginner-friendly explanation for: '{question}'
                    Format with 4-5 subheadings (##) and 1-2 bullet points each.
                    Keep language simple (max 8 words per point)."""
                    desc_response = model.generate_content(desc_prompt).text

                    tree_prompt = f"""Extract 5 key action steps for: '{question}'
                    - Each must start with '-'
                    - Max 8 words per point"""
                    tree_response = model.generate_content(tree_prompt).text
                    points = [line.strip() for line in tree_response.split('\n') if line.strip().startswith('-')][:5]

                    st.subheader("📋 Step-by-Step Guide")
                    st.markdown(desc_response)

                    st.subheader("🌳 Quick Visual Summary")
                    if points:
                        tree = create_tree_diagram(question, points)
                        if tree:
                            st.graphviz_chart(tree, use_container_width=True)
                except Exception as e:
                    st.error("Couldn't generate answer. Please try again.")
                    st.write("Tip: Keep questions simple for best results")
        
# ---------- Main Navigation ----------
if st.session_state.page == "login":
    login_register()
elif st.session_state.page == "home":
    home()
elif st.session_state.page == "update":
    update_resource()
elif st.session_state.page == "request":
    request_resource()
elif st.session_state.page == "ask_bot":
    st.session_state.page = "ask_bot"
    ask_bot()
elif st.session_state.page == "crop_recommendation":
    st.session_state.page = "crop_recommendation"
    from Crop_Prediction.app import crop_prediction
    crop_prediction()
elif st.session_state.page == "crop_requirements":
    from Crop_Requirement.app import crop_requirement
    crop_requirement()
elif st.session_state.page == "crop_yield":
    from Crop_Yield.app import crop_yield
    crop_yield()