# ======================================
# INSTALL PACKAGES
# ======================================
import os,sys,subprocess,time,socket

print("Installing packages...")
subprocess.check_call([sys.executable,"-m","pip","install","-q","streamlit","pyngrok","pyjwt","watchdog"])

from pyngrok import ngrok

# ======================================
# DARK THEME
# ======================================
os.makedirs(".streamlit",exist_ok=True)

with open(".streamlit/config.toml","w") as f:
    f.write("""
[theme]
base="dark"
primaryColor="#648282"
backgroundColor="#BF0F3B"
secondaryBackgroundColor="#648282"
textColor="#050505"
""")

# ======================================
# STREAMLIT APP
# ======================================
app_code='''
import streamlit as st
import hashlib
import jwt
import datetime
import time
import re

SECRET_KEY="super_secret"
ALGO="HS256"

# ---------------- PASSWORD HASH ----------------
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ---------------- JWT ----------------
def create_token(data):
    payload=data.copy()
    payload["exp"]=datetime.datetime.utcnow()+datetime.timedelta(minutes=30)
    return jwt.encode(payload,SECRET_KEY,algorithm=ALGO)

def verify_token(token):
    try:
        return jwt.decode(token,SECRET_KEY,algorithms=[ALGO])
    except:
        return None

# ---------------- VALIDATION ----------------
def valid_email(e):
    return re.match(r"^[^@]+@[^@]+\\.[^@]+$",e)

# ---------------- SESSION ----------------
if "jwt" not in st.session_state:
    st.session_state.jwt=None
if "page" not in st.session_state:
    st.session_state.page="login"
if "users" not in st.session_state:
    st.session_state.users={}
if "reset_email" not in st.session_state:
    st.session_state.reset_email=None

# ---------------- STYLE ----------------
st.set_page_config(layout="wide")

st.markdown("""
<style>
.fade{animation:fadeIn 1s ease-in;}
@keyframes fadeIn{from{opacity:0;}to{opacity:1;}}
.big-title{text-align:center;font-size:42px;font-weight:bold;color:#6C63FF;}
.card{padding:30px;border-radius:15px;background:#1c1f26;box-shadow:0 0 25px rgba(0,0,0,0.4);}
.stButton>button{background:#6C63FF;color:white;border-radius:10px;height:3em;font-weight:bold;}
</style>
""",unsafe_allow_html=True)

# ---------------- TOKEN ACCESS PAGE ----------------
query_params = st.query_params
if "token_access" in query_params:
    st.title("JWT TOKEN ACCESS PANEL")
    if st.session_state.jwt:
        st.code(st.session_state.jwt)
    else:
        st.warning("No active session token")
    st.stop()

# ---------------- LOGIN ----------------
def login():
    st.markdown('<div class="big-title"> LOG IN PAGE </div>',unsafe_allow_html=True)
    col1,col2,col3=st.columns([1,2,1])
    with col2:
        st.markdown('<div class="card">',unsafe_allow_html=True)
        with st.form("login"):
            email=st.text_input("Email")
            pwd=st.text_input("Password",type="password")
            submit=st.form_submit_button("Login")

            if submit:
                if email in st.session_state.users:
                    if st.session_state.users[email]["password"]==hash_password(pwd):
                        st.session_state.jwt=create_token({"sub":email})
                        st.rerun()
                st.error("Invalid credentials")

        if st.button("Create Account"):
            st.session_state.page="signup"
            st.rerun()

        if st.button("Forgot Password"):
            st.session_state.page="forgot"
            st.rerun()
        st.markdown('</div>',unsafe_allow_html=True)

# ---------------- SIGNUP ----------------
def signup():
    st.markdown('<div class="big-title">Create Secure Account</div>',unsafe_allow_html=True)
    questions=["Your pet name?","Your birth city?","Favourite teacher?"]

    with st.form("signup"):
        username=st.text_input("Username")
        email=st.text_input("Email")
        pwd=st.text_input("Password",type="password")
        cpwd=st.text_input("Confirm Password",type="password")
        q=st.selectbox("Security Question",questions)
        ans=st.text_input("Security Answer")
        submit=st.form_submit_button("Sign Up")

        if submit:
            if email and valid_email(email) and pwd==cpwd:
                st.session_state.users[email]={
                    "username":username,
                    "password":hash_password(pwd),
                    "question":q,
                    "answer":hash_password(ans.lower())
                }
                st.success("Account created!")
                time.sleep(1)
                st.session_state.page="login"
                st.rerun()
            else:
                st.error("Invalid signup details")

    if st.button("Back"):
        st.session_state.page="login"
        st.rerun()

# ---------------- FORGOT PASSWORD ----------------
def forgot():
    st.markdown('<div class="big-title">Password Recovery</div>',unsafe_allow_html=True)

    if not st.session_state.reset_email:
        email=st.text_input("Enter your email")
        if st.button("Next"):
            if email in st.session_state.users:
                st.session_state.reset_email=email
                st.rerun()
            else:
                st.error("Email not found")
    else:
        user=st.session_state.users[st.session_state.reset_email]
        st.info("Security Question:")
        st.write(user["question"])

        ans=st.text_input("Answer")
        newpwd=st.text_input("New Password",type="password")

        if st.button("Reset Password"):
            if user["answer"]==hash_password(ans.lower()):
                user["password"]=hash_password(newpwd)
                st.success("Password Updated!")
                time.sleep(1)
                st.session_state.reset_email=None
                st.session_state.page="login"
                st.rerun()
            else:
                st.error("Wrong Answer")

# ---------------- DASHBOARD ----------------
def dashboard():
    if not verify_token(st.session_state.jwt):
        st.session_state.jwt=None
        st.rerun()

    st.sidebar.title("Menu")
    if st.sidebar.button("Logout"):
        st.session_state.jwt=None
        st.session_state.page="login"
        st.rerun()

    st.title("Welcome Secure User")
    st.write("Login successful.")

# ---------------- ROUTER ----------------
if st.session_state.jwt:
    dashboard()
else:
    if st.session_state.page=="signup":
        signup()
    elif st.session_state.page=="forgot":
        forgot()
    else:
        login()
'''

with open("app.py","w") as f:
    f.write(app_code)

# ======================================
# WAIT STREAMLIT
# ======================================
def wait_streamlit(port=8501):
    start=time.time()
    while time.time()-start<30:
        s=socket.socket()
        if s.connect_ex(("localhost",port))==0:
            return True
        time.sleep(1)
    return False

# ======================================
# NGROK RUNNER
# ======================================
print("Get token from:")
print("https://dashboard.ngrok.com/get-started/your-authtoken")

token=input("Enter Ngrok Token: ")

if token:
    ngrok.set_auth_token(token)
    os.system("pkill ngrok")
    os.system("pkill streamlit")

    proc=subprocess.Popen(["streamlit","run","app.py","--server.port","8501"],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL)

    if wait_streamlit():
        url=ngrok.connect(8501).public_url

        print("\\nAPP URL:")
        print(url)

        print("\\nJWT ACCESS LINK (ADMIN ONLY):")
        print(url+"?token_access=1")

        while proc.poll() is None:
            time.sleep(1)
