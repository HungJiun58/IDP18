import streamlit as st
import os
import sqlite3
import hashlib
from datetime import datetime
from streamlit_webrtc import webrtc_streamer

# Ensure the folder exists
if not os.path.exists("captured_images"):
    os.makedirs("captured_images")

# Set up database
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables for users & images
cursor.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS images (username TEXT, image_path TEXT)''')
conn.commit()

# Hash password function
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to load images from the database
def load_images(username):
    cursor.execute("SELECT image_path FROM images WHERE username=?", (username,))
    return [row[0] for row in cursor.fetchall()]

# Function to save images to the database
def save_image(username, image_path):
    cursor.execute("INSERT INTO images (username, image_path) VALUES (?, ?)", (username, image_path))
    conn.commit()

# Function to delete images
def delete_image(username, image_path):
    if os.path.exists(image_path):
        os.remove(image_path)
    cursor.execute("DELETE FROM images WHERE username=? AND image_path=?", (username, image_path))
    conn.commit()

# User authentication
def login_page():
    st.title("🔐 Login / Sign Up")
    menu = st.sidebar.radio("Menu", ["Login", "Sign Up"])

    if menu == "Sign Up":
        st.subheader("Create a New Account")
        new_user = st.text_input("Username")
        new_pass = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            cursor.execute("SELECT * FROM users WHERE username=?", (new_user,))
            if cursor.fetchone():
                st.warning("❌ Username already exists!")
            else:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (new_user, hash_password(new_pass)))
                conn.commit()
                st.success("✅ Account created! Please log in.")

    elif menu == "Login":
        st.subheader("Login to Your Account")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hash_password(password)))
            if cursor.fetchone():
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.captured_images = load_images(username)  # Load previous images BEFORE capturing
                st.session_state.camera_active = False  # Track if camera is open
                st.rerun()
            else:
                st.warning("❌ Incorrect username or password!")

# If not logged in, show login page
if "logged_in" not in st.session_state:
    login_page()
    st.stop()

# ---- MAIN APP ----
st.title(f"📷 Durian Monitor - Welcome, {st.session_state.username}")

# Load previous images IMMEDIATELY after login
if "captured_images" not in st.session_state:
    st.session_state.captured_images = load_images(st.session_state.username)

# Layout: Open Camera & Capture Buttons
st.subheader("🎥 Camera Controls")
col1, col2 = st.columns(2)

with col1:
    if st.button("📷 Open Camera"):
        st.session_state.camera_active = True

with col2:
    if st.button("📸 Capture Image"):
        st.warning("Image capture from WebRTC requires extra handling (work in progress).")

# Show livestream only if camera is opened
if "camera_active" in st.session_state and st.session_state.camera_active:
    webrtc_streamer(key="camera")

# Display captured images
st.subheader("📂 Captured Images History")
if st.session_state.captured_images:
    for img_path in reversed(st.session_state.captured_images):
        col1, col2 = st.columns([2, 3])

        with col1:
            st.image(img_path, caption=os.path.basename(img_path), use_column_width=True)

        with col2:
            st.write(f"Ripeness: (AI Prediction)")
            st.write(f"Condition: (AI Prediction)")
            st.write(f"Quality: (AI Prediction)")
            st.write(f"Location: (To be added)")

            # DELETE BUTTON (FIXED TO WORK PROPERLY)
            if st.button(f"🗑 Delete {os.path.basename(img_path)}", key=img_path):
                delete_image(st.session_state.username, img_path)
                st.session_state.captured_images = load_images(st.session_state.username)  # Refresh images
                st.rerun()

else:
    st.info("No images captured yet.")
