"""
Business Automation SaaS — Professional ERP Frontend
Built with Streamlit + custom CSS for a modern ERP look.
"""

import json
import os
import re
from datetime import date, datetime, timedelta
from typing import Any

import extra_streamlit_components as stx
import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DEFAULT_API = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
SESSION_MINUTES = 15  # auto-logout after this many minutes of inactivity
COOKIE_NAME = "erp_session"

st.set_page_config(
    page_title="Business Automation SaaS",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Cookie manager — persists session across browser refresh
# Do NOT cache this — CookieManager uses Streamlit widgets internally,
# caching it triggers the "CachedWidgetWarning" banner on every rerun.
# ---------------------------------------------------------------------------
cookies = stx.CookieManager(key="erp_cookie_mgr")


# ---------------------------------------------------------------------------
# Session defaults
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "token": None,
    "user_profile": None,
    "auth_page": "login",
    "page": "dashboard",
    "api_base_url": DEFAULT_API,
    "session_expires_at": None,
    "_session_restored": False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Session persistence helpers
# ---------------------------------------------------------------------------
def save_session_cookie(token: str, user_profile: dict):
    """Save the auth session to a cookie so it survives page refresh."""
    expires_at = datetime.utcnow() + timedelta(minutes=SESSION_MINUTES)
    st.session_state.session_expires_at = expires_at.isoformat()
    payload = {
        "token": token,
        "user_profile": user_profile,
        "expires_at": expires_at.isoformat(),
    }
    cookies.set(COOKIE_NAME, json.dumps(payload), expires_at=expires_at)


def clear_session_cookie():
    st.session_state.token = None
    st.session_state.user_profile = None
    st.session_state.session_expires_at = None
    try:
        cookies.delete(COOKIE_NAME)
    except Exception:
        pass


def restore_session_from_cookie():
    """Restore session from the cookie on app load (after refresh)."""
    if st.session_state._session_restored:
        return
    st.session_state._session_restored = True

    raw = cookies.get(COOKIE_NAME)
    if not raw:
        return
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        expires_at = datetime.fromisoformat(data.get("expires_at", ""))
        if datetime.utcnow() >= expires_at:
            clear_session_cookie()
            return
        st.session_state.token = data.get("token")
        st.session_state.user_profile = data.get("user_profile")
        st.session_state.session_expires_at = data.get("expires_at")
    except Exception:
        clear_session_cookie()


def check_session_expired() -> bool:
    """Return True if the session has expired (and log out)."""
    exp_str = st.session_state.get("session_expires_at")
    if not exp_str or not st.session_state.token:
        return False
    try:
        expires_at = datetime.fromisoformat(exp_str)
        if datetime.utcnow() >= expires_at:
            clear_session_cookie()
            return True
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _detail(data: Any) -> str:
    return data.get("detail", data) if isinstance(data, dict) else str(data)


def api(method: str, endpoint: str, token: str | None = None, **kw) -> tuple[int, Any]:
    base = st.session_state.get("api_base_url", DEFAULT_API)
    headers = kw.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = requests.request(method, f"{base.rstrip('/')}/{endpoint.lstrip('/')}", headers=headers, timeout=30, **kw)
    if "application/json" in r.headers.get("content-type", ""):
        return r.status_code, r.json()
    return r.status_code, r.text


def tk():
    return st.session_state.token


def nav(page: str):
    st.session_state.page = page


def _md_to_html(msg: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", str(msg))


def show_success(msg: str):
    st.markdown(f'<div class="alert-success">{_md_to_html(msg)}</div>', unsafe_allow_html=True)


def show_error(msg: str):
    st.markdown(f'<div class="alert-error">{_md_to_html(msg)}</div>', unsafe_allow_html=True)


def show_info(msg: str):
    st.markdown(f'<div class="alert-info">{_md_to_html(msg)}</div>', unsafe_allow_html=True)


def show_warning(msg: str):
    st.markdown(f'<div class="alert-warning">{_md_to_html(msg)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# GLOBAL CSS — Professional ERP Theme
# ---------------------------------------------------------------------------
THEME_CSS = """
<style>
/* ---- Reset Streamlit defaults ---- */
#MainMenu, footer, header, .stDeployButton {display:none!important}
.block-container {padding-top:1rem!important; padding-bottom:1rem!important;}

/* ---- Hide Streamlit developer exception/warning boxes ---- */
.stException {display: none !important;}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    min-width: 240px !important;
    max-width: 240px !important;
}
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3,
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown span,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] .stMarkdown label {
    color: #cbd5e1 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
}

/* Sidebar nav buttons */
section[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    text-align: left !important;
    justify-content: flex-start !important;
    background: transparent !important;
    color: #94a3b8 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
    margin-bottom: 2px !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.08) !important;
    color: #e2e8f0 !important;
}

/* ---- Main content area ---- */
.stApp {
    background: #f1f5f9;
}

/* ---- Form labels — dark and readable ---- */
.stTextInput label, .stNumberInput label, .stDateInput label,
.stSelectbox label, .stTextArea label, .stCheckbox label span,
.stMultiSelect label, .stRadio label {
    color: #1e293b !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

/* ---- Alerts — royal blue for success, strong colors for all ---- */
/* Success — royal blue background */
div[role="alert"]:has(.st-success),
div[data-testid="stAlert"] div[data-testid*="Success"],
.stAlert div[data-baseweb="notification"][kind="positive"],
div.stAlert > div:first-child {
    font-weight: 600 !important;
    font-size: 15px !important;
}
/* Broad override — force ALL alert boxes */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    overflow: hidden !important;
}
div[data-testid="stAlert"] > div {
    font-weight: 600 !important;
    font-size: 15px !important;
    padding: 16px 20px !important;
    border-radius: 10px !important;
}
/* Success = Royal Blue */
div[data-testid="stAlert"] > div[data-baseweb="notification"] div[role="alert"],
.element-container .stSuccess > div,
div[data-testid="stAlert"]:has([kind="positive"]) > div,
div[data-testid="stAlert"]:nth-of-type(n) > div {
    font-weight: 600 !important;
    font-size: 15px !important;
}

/* Direct color overrides using attribute selectors */
/* green/success alerts */
div[data-testid="stAlert"] > div[style*="background-color: rgb(221, 243, 228)"],
div[data-testid="stAlert"] > div[style*="rgba(33, 195, 84)"] {
    background: #1e40af !important;
    color: #ffffff !important;
}
/* red/error alerts */
div[data-testid="stAlert"] > div[style*="background-color: rgb(255, 226, 226)"],
div[data-testid="stAlert"] > div[style*="rgba(255, 43, 43)"] {
    background: #dc2626 !important;
    color: #ffffff !important;
}

/* Nuclear option: override via Streamlit's internal classes */
.stException, .stWarning, .stError, .stSuccess, .stInfo {
    border-radius: 10px !important;
}

/* Custom styled alert classes we'll use via markdown */
.alert-success {
    background: linear-gradient(135deg, #1e40af, #3b82f6) !important;
    color: #ffffff !important;
    padding: 16px 20px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(30, 64, 175, 0.3);
}
.alert-error {
    background: linear-gradient(135deg, #dc2626, #ef4444) !important;
    color: #ffffff !important;
    padding: 16px 20px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(220, 38, 38, 0.3);
}
.alert-info {
    background: linear-gradient(135deg, #6366f1, #818cf8) !important;
    color: #ffffff !important;
    padding: 16px 20px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}
.alert-warning {
    background: linear-gradient(135deg, #d97706, #f59e0b) !important;
    color: #ffffff !important;
    padding: 16px 20px;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 600;
    margin: 8px 0;
    box-shadow: 0 2px 8px rgba(217, 119, 6, 0.3);
}

/* ---- KPI Metric Cards ---- */
.kpi-row {display:flex; gap:16px; margin-bottom:20px; flex-wrap:wrap;}
.kpi-card {
    flex:1; min-width:180px;
    background:#ffffff;
    border-radius:12px;
    padding:20px 24px;
    box-shadow:0 1px 3px rgba(0,0,0,0.06);
    border-left:4px solid #6366f1;
}
.kpi-card.green  {border-left-color:#10b981;}
.kpi-card.blue   {border-left-color:#3b82f6;}
.kpi-card.orange {border-left-color:#f59e0b;}
.kpi-card.red    {border-left-color:#ef4444;}
.kpi-card.purple {border-left-color:#8b5cf6;}
.kpi-label {font-size:12px; color:#64748b; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px;}
.kpi-value {font-size:28px; font-weight:700; color:#1e293b;}
.kpi-sub   {font-size:12px; color:#94a3b8; margin-top:2px;}

/* ---- Section Cards ---- */
.section-card {
    background:#ffffff;
    border-radius:12px;
    padding:24px;
    box-shadow:0 1px 3px rgba(0,0,0,0.06);
    margin-bottom:16px;
}
.section-title {
    font-size:18px;
    font-weight:600;
    color:#1e293b;
    margin-bottom:16px;
    padding-bottom:12px;
    border-bottom:1px solid #e2e8f0;
}

/* ---- Page header ---- */
.page-header {
    font-size:24px; font-weight:700; color:#1e293b;
    margin-bottom:4px;
}
.page-subtitle {
    font-size:14px; color:#64748b; margin-bottom:20px;
}

/* ---- Breadcrumb ---- */
.breadcrumb {
    font-size:12px; color:#94a3b8; margin-bottom:16px;
}
.breadcrumb a {color:#6366f1; text-decoration:none;}

/* ---- Auth pages — compact centered card ---- */
.auth-wrapper {
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding-top: 40px;
    min-height: 100vh;
}
.auth-card {
    width: 400px;
    max-width: 400px;
    background: #ffffff;
    border-radius: 12px;
    padding: 36px 32px 28px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.12);
}
/* Force the main block container narrow on auth pages */
.auth-page .block-container {
    max-width: 480px !important;
    padding-left: 40px !important;
    padding-right: 40px !important;
}
/* Compact inputs on auth page */
.auth-card .stTextInput > div > div > input {
    padding: 10px 14px !important;
    font-size: 14px !important;
    border-radius: 6px !important;
    border: 1px solid #d1d5db !important;
    background: #ffffff !important;
    color: #1e293b !important;
}
.auth-card .stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}
.auth-card .stTextInput label {
    color: #374151 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
.auth-card .stCheckbox label span {
    color: #374151 !important;
    font-size: 13px !important;
}
.auth-title {
    text-align: center; font-size: 20px; font-weight: 700;
    color: #1e293b; margin-bottom: 4px;
}
.auth-subtitle {
    text-align: center; font-size: 13px; color: #6b7280; margin-bottom: 20px;
}
.avatar-circle {
    width: 72px; height: 72px; margin: 0 auto 16px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
}
.avatar-circle svg {width: 36px; height: 36px; fill: #ffffff;}
.brand-label {
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    color: #6366f1;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 24px;
}

/* Auth form button — teal/green like reference */
.auth-card .stFormSubmitButton > button {
    width: 100%;
    background: #2dd4a8 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}
.auth-card .stFormSubmitButton > button:hover {
    background: #22c997 !important;
    box-shadow: 0 4px 12px rgba(45, 212, 168, 0.4) !important;
}
.auth-toggle {text-align: center; margin-top: 14px;}
.auth-toggle a {color: #6366f1; font-weight: 600; text-decoration: none; font-size: 13px;}

/* ---- Status badges ---- */
.badge {
    display:inline-block; padding:3px 10px; border-radius:20px;
    font-size:11px; font-weight:600; text-transform:uppercase;
}
.badge-green  {background:#d1fae5; color:#065f46;}
.badge-blue   {background:#dbeafe; color:#1e40af;}
.badge-orange {background:#fef3c7; color:#92400e;}
.badge-red    {background:#fee2e2; color:#991b1b;}
.badge-gray   {background:#f1f5f9; color:#475569;}

/* ---- Data tables ---- */
.stDataFrame {border-radius:8px!important; overflow:hidden!important;}

/* ---- Tabs inside content ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px;
    background: #ffffff;
    border-radius: 8px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 8px 20px;
    font-weight: 500;
}

/* Hide sidebar on auth pages */
.auth-hide-sidebar section[data-testid="stSidebar"] {display:none!important;}

/* ---- Welcome banner ---- */
.welcome-banner {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    border-radius: 16px;
    padding: 28px 32px;
    color: white;
    margin-bottom: 20px;
}
.welcome-banner h2 {margin:0 0 4px 0; font-size:22px; font-weight:700;}
.welcome-banner p  {margin:0; opacity:0.85; font-size:14px;}
</style>
"""

AUTH_HIDE_SIDEBAR_CSS = """
<style>section[data-testid="stSidebar"]{display:none!important;}</style>
"""


def hide_cached_widget_warning():
    """Hide the CachedWidgetWarning banner emitted by extra_streamlit_components."""
    import streamlit.components.v1 as components
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;
            const hide = () => {
                doc.querySelectorAll('[data-testid="stAlert"], .stAlert, div[role="alert"]').forEach(el => {
                    const txt = (el.innerText || '').toLowerCase();
                    if (txt.includes('cachedwidgetwarning') ||
                        txt.includes('cache_resource') ||
                        txt.includes('cache_data') ||
                        txt.includes('cached function')) {
                        el.style.display = 'none';
                        // Also try to hide parent container
                        let p = el.closest('.element-container, [data-testid="stElementContainer"]');
                        if (p) p.style.display = 'none';
                    }
                });
            };
            hide();
            // Watch for dynamically added warnings
            const observer = new MutationObserver(hide);
            observer.observe(doc.body, {childList: true, subtree: true});
            // Also run periodically for the first few seconds
            let count = 0;
            const interval = setInterval(() => {
                hide();
                if (++count > 20) clearInterval(interval);
            }, 200);
        })();
        </script>
        """,
        height=0,
    )

AVATAR_SVG = '<svg viewBox="0 0 24 24"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v1.2c0 .7.5 1.2 1.2 1.2h16.8c.7 0 1.2-.5 1.2-1.2v-1.2c0-3.2-6.4-4.8-9.6-4.8z"/></svg>'


# ===================================================================
# AUTH PAGES
# ===================================================================

def page_login():
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    st.markdown(AUTH_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
    # Force narrow centered layout
    st.markdown('<style>.block-container{max-width:460px!important;margin:0 auto!important;padding-top:30px!important;}</style>', unsafe_allow_html=True)

    st.markdown(f'<div class="avatar-circle">{AVATAR_SVG}</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-label">ERP System</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Welcome to <strong>ERP Admin</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Sign in to manage your business</div>', unsafe_allow_html=True)

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="email@domain.com")
        password = st.text_input("Password", type="password", placeholder="********")
        st.markdown('<p style="margin:0 0 12px 0;"><a href="#" style="color:#6366f1;font-size:12px;text-decoration:none;">Forgot password?</a></p>', unsafe_allow_html=True)
        submitted = st.form_submit_button("SUBMIT")

    if submitted:
        if not email or not password:
            st.error("Please enter email and password.")
        else:
            try:
                sc, data = api("POST", "/auth/login", data={"username": email, "password": password})
                if sc == 200:
                    token = data["access_token"]
                    st.session_state.token = token
                    sc2, me = api("GET", "/auth/me", token=token)
                    if sc2 == 200:
                        st.session_state.user_profile = me
                    st.session_state.page = "dashboard"
                    # Persist session to cookie
                    save_session_cookie(token, st.session_state.user_profile or {})
                    st.rerun()
                else:
                    st.error(_detail(data))
            except requests.RequestException as e:
                st.error(f"Connection error: {e}")

    st.markdown('<div class="auth-toggle"><span style="color:#64748b;font-size:13px;">Don\'t have login? </span><a href="#" style="color:#6366f1;font-weight:600;text-decoration:none;font-size:13px;">Register</a></div>', unsafe_allow_html=True)

    if st.button("Create a new business account", use_container_width=True, type="tertiary"):
        st.session_state.auth_page = "register"
        st.rerun()


def page_register():
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    st.markdown(AUTH_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)
    st.markdown('<style>.block-container{max-width:460px!important;margin:0 auto!important;padding-top:30px!important;}</style>', unsafe_allow_html=True)

    st.markdown(f'<div class="avatar-circle">{AVATAR_SVG}</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-label">ERP System</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-title">Create Account</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Register your business to get started</div>', unsafe_allow_html=True)

    with st.form("register_form"):
        biz_name = st.text_input("Business Name", placeholder="My Company Ltd.")
        slug = re.sub(r"[^a-z0-9]+", "-", biz_name.lower()).strip("-") if biz_name else ""
        biz_slug = st.text_input("Business Slug", value=slug, placeholder="my-company-ltd")
        admin_name = st.text_input("Full Name", placeholder="John Doe")
        admin_email = st.text_input("Email", placeholder="john@company.com")
        admin_pw = st.text_input("Password", type="password", placeholder="Min 8 characters")
        submitted = st.form_submit_button("CREATE ACCOUNT")

    if submitted:
        clean = re.sub(r"[^a-z0-9]+", "-", biz_slug.lower()).strip("-")
        try:
            sc, data = api("POST", "/auth/register-tenant", json={
                "business_name": biz_name, "business_slug": clean,
                "admin_name": admin_name, "admin_email": admin_email, "admin_password": admin_pw,
            })
            if sc == 201:
                st.success("Account created! You can now sign in.")
                st.session_state.auth_page = "login"
            else:
                st.error(_detail(data))
        except requests.RequestException as e:
            st.error(str(e))

    st.markdown('<div class="auth-toggle"><span style="color:#64748b;font-size:13px;">Already have an account? </span><a href="#" style="color:#6366f1;font-weight:600;text-decoration:none;font-size:13px;">Sign in</a></div>', unsafe_allow_html=True)

    if st.button("Sign in to your account", use_container_width=True, type="tertiary"):
        st.session_state.auth_page = "login"
        st.rerun()


# ===================================================================
# SIDEBAR NAVIGATION
# ===================================================================

def render_sidebar():
    user = st.session_state.user_profile or {}
    tenant = user.get("tenant", {}).get("name", "Business")

    with st.sidebar:
        # Brand
        st.markdown(f"""
        <div style="padding:8px 0 16px 0; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:16px;">
            <div style="font-size:20px; font-weight:800; color:#ffffff; letter-spacing:-0.5px;">💼 {tenant}</div>
            <div style="font-size:11px; color:#64748b; margin-top:2px;">ERP Solution</div>
        </div>
        """, unsafe_allow_html=True)

        role = user.get("role", "").lower()
        section_hdr = '<p style="font-size:10px;font-weight:700;color:#475569;letter-spacing:1px;margin:12px 0 6px 4px;">'

        # MAIN section
        st.markdown(section_hdr + 'MAIN</p>', unsafe_allow_html=True)
        if st.button("📊  Dashboard", key="nav_dash"):
            nav("dashboard"); st.rerun()

        # HR
        st.markdown(section_hdr.replace("12px", "16px") + 'HR</p>', unsafe_allow_html=True)
        if st.button("👥  Employees", key="nav_emp"):
            nav("employees"); st.rerun()
        if st.button("💰  Salary Structures", key="nav_sal"):
            nav("salary"); st.rerun()
        if st.button("📋  Payroll", key="nav_pay"):
            nav("payroll"); st.rerun()
        if st.button("🕐  Attendance", key="nav_att"):
            nav("attendance"); st.rerun()
        if st.button("🌴  Leave Requests", key="nav_lv"):
            nav("leaves"); st.rerun()

        # BILLING
        st.markdown(section_hdr.replace("12px", "16px") + 'BILLING</p>', unsafe_allow_html=True)
        if st.button("🏢  Customers", key="nav_cust"):
            nav("customers"); st.rerun()
        if st.button("🧾  Invoices", key="nav_inv"):
            nav("invoices"); st.rerun()

        # SALES & CRM
        st.markdown(section_hdr.replace("12px", "16px") + 'SALES & CRM</p>', unsafe_allow_html=True)
        if st.button("🎯  Leads", key="nav_lead"):
            nav("leads"); st.rerun()
        if st.button("💡  Opportunities", key="nav_opp"):
            nav("opportunities"); st.rerun()
        if st.button("📝  Quotations", key="nav_qt"):
            nav("quotations"); st.rerun()
        if st.button("📦  Sales Orders", key="nav_so"):
            nav("sales_orders"); st.rerun()

        # INVENTORY
        st.markdown(section_hdr.replace("12px", "16px") + 'INVENTORY</p>', unsafe_allow_html=True)
        if st.button("🏬  Warehouses", key="nav_wh"):
            nav("warehouses"); st.rerun()
        if st.button("📦  Items", key="nav_it"):
            nav("items"); st.rerun()
        if st.button("🔄  Stock Movements", key="nav_sm"):
            nav("stock_movements"); st.rerun()

        # PROCUREMENT
        st.markdown(section_hdr.replace("12px", "16px") + 'PROCUREMENT</p>', unsafe_allow_html=True)
        if st.button("🏭  Vendors", key="nav_ven"):
            nav("vendors"); st.rerun()
        if st.button("📝  Purchase Req.", key="nav_pr"):
            nav("prs"); st.rerun()
        if st.button("🛒  Purchase Orders", key="nav_po"):
            nav("pos"); st.rerun()
        if st.button("📥  GRN (Receipts)", key="nav_grn"):
            nav("grns"); st.rerun()

        # ACCOUNTING
        st.markdown(section_hdr.replace("12px", "16px") + 'ACCOUNTING</p>', unsafe_allow_html=True)
        if st.button("📒  Chart of Accounts", key="nav_coa"):
            nav("accounts"); st.rerun()
        if st.button("📖  Journal Entries", key="nav_je"):
            nav("journals"); st.rerun()
        if st.button("🏗️  Fixed Assets", key="nav_fa"):
            nav("fixed_assets"); st.rerun()
        if st.button("🏦  Bank & Reconcile", key="nav_bank"):
            nav("bank"); st.rerun()
        if st.button("📑  Financial Reports", key="nav_fr"):
            nav("fin_reports"); st.rerun()

        # FINANCE (expense tracking)
        st.markdown(section_hdr.replace("12px", "16px") + 'EXPENSE TRACKING</p>', unsafe_allow_html=True)
        if st.button("📂  Expense Categories", key="nav_cat"):
            nav("exp_categories"); st.rerun()
        if st.button("💳  Expenses", key="nav_exp"):
            nav("expenses"); st.rerun()
        if st.button("📈  Reports", key="nav_rep"):
            nav("reports"); st.rerun()

        st.divider()

        # DMS
        st.markdown(section_hdr.replace("12px", "16px") + 'DMS</p>', unsafe_allow_html=True)
        if st.button("📁  Documents", key="nav_docs"):
            nav("documents"); st.rerun()

        # OTHERS — admin only for user management & audit
        st.markdown(section_hdr.replace("12px", "8px") + 'OTHERS</p>', unsafe_allow_html=True)
        if role == "admin":
            if st.button("👤  User Management", key="nav_users"):
                nav("users"); st.rerun()
            if st.button("🔍  Audit Log", key="nav_audit"):
                nav("audit"); st.rerun()
        if st.button("⚙️  Settings", key="nav_set"):
            nav("settings"); st.rerun()

        # User info at bottom
        st.markdown(f"""
        <div style="position:fixed; bottom:16px; left:16px; width:208px;
                    background:rgba(255,255,255,0.05); border-radius:10px; padding:10px 12px;
                    display:flex; align-items:center; gap:10px;">
            <div style="width:36px;height:36px;border-radius:50%;background:#6366f1;
                        display:flex;align-items:center;justify-content:center;
                        font-size:14px;font-weight:700;color:white;">
                {user.get('full_name', 'U')[0].upper()}
            </div>
            <div>
                <div style="color:#e2e8f0;font-size:13px;font-weight:600;">{user.get('full_name', 'User')}</div>
                <div style="color:#64748b;font-size:11px;">{user.get('role', 'admin').title()}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ===================================================================
# DASHBOARD PAGE
# ===================================================================

def page_dashboard():
    user = st.session_state.user_profile or {}
    name = user.get("full_name", "User").split()[0]

    # Welcome banner
    st.markdown(f"""
    <div class="welcome-banner">
        <h2>Good Morning, {name}!</h2>
        <p>Here's your business overview for today, {date.today().strftime('%B %d, %Y')}.</p>
    </div>
    """, unsafe_allow_html=True)

    def _safe_get(endpoint, params=None):
        try:
            sc, d = api("GET", endpoint, token=tk(), params=params)
            return d if sc == 200 else None
        except Exception:
            return None

    emps = _safe_get("/employees/") or []
    custs = _safe_get("/customers/") or []
    invs = _safe_get("/invoices/") or []
    history = _safe_get("/payroll/history") or []
    report = _safe_get("/expenses/report", {"year": date.today().year}) or {}
    low_stock = _safe_get("/items/low-stock") or []
    pending_prs = _safe_get("/prs/", {"status_filter": "pending"}) or []
    pending_leaves = _safe_get("/leaves/", {"status_filter": "pending"}) or []
    opps = _safe_get("/opportunities/") or []
    today = date.today()
    pnl = _safe_get("/financial-reports/profit-and-loss",
                    {"period_start": f"{today.year}-01-01", "period_end": str(today)}) or {}

    exp_total = report.get("total", 0)
    net_profit = pnl.get("net_profit", 0) if pnl else 0
    pipeline = sum((o.get("expected_amount", 0) * o.get("probability", 0) / 100) for o in opps)

    # Top-row KPI cards — 5 business metrics
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card blue">
            <div class="kpi-label">Employees</div>
            <div class="kpi-value">{len(emps)}</div>
            <div class="kpi-sub">Active workforce</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-label">Customers</div>
            <div class="kpi-value">{len(custs)}</div>
            <div class="kpi-sub">Registered clients</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-label">Invoices</div>
            <div class="kpi-value">{len(invs)}</div>
            <div class="kpi-sub">Total created</div>
        </div>
        <div class="kpi-card orange">
            <div class="kpi-label">Payroll Slips</div>
            <div class="kpi-value">{len(history)}</div>
            <div class="kpi-sub">Processed</div>
        </div>
        <div class="kpi-card red">
            <div class="kpi-label">Expenses {today.year}</div>
            <div class="kpi-value">{exp_total:,.0f}</div>
            <div class="kpi-sub">Year to date</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Second row — financial + operational KPIs
    np_color = "green" if net_profit >= 0 else "red"
    low_color = "red" if low_stock else "green"
    st.markdown(f"""
    <div class="kpi-row">
        <div class="kpi-card {np_color}">
            <div class="kpi-label">Net Profit YTD</div>
            <div class="kpi-value">{net_profit:,.0f}</div>
            <div class="kpi-sub">Income – Expenses</div>
        </div>
        <div class="kpi-card blue">
            <div class="kpi-label">Weighted Pipeline</div>
            <div class="kpi-value">{pipeline:,.0f}</div>
            <div class="kpi-sub">{len(opps)} opportunities</div>
        </div>
        <div class="kpi-card {low_color}">
            <div class="kpi-label">Low Stock Items</div>
            <div class="kpi-value">{len(low_stock)}</div>
            <div class="kpi-sub">Need reorder</div>
        </div>
        <div class="kpi-card orange">
            <div class="kpi-label">Pending PRs</div>
            <div class="kpi-value">{len(pending_prs)}</div>
            <div class="kpi-sub">Awaiting approval</div>
        </div>
        <div class="kpi-card purple">
            <div class="kpi-label">Pending Leaves</div>
            <div class="kpi-value">{len(pending_leaves)}</div>
            <div class="kpi-sub">Awaiting approval</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Content sections
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="section-card"><div class="section-title">Quick Actions</div>', unsafe_allow_html=True)
        if st.button("➕ Add Employee", use_container_width=True):
            nav("employees"); st.rerun()
        if st.button("🧾 Create Invoice", use_container_width=True):
            nav("invoices"); st.rerun()
        if st.button("📦 New PO", use_container_width=True):
            nav("pos"); st.rerun()
        if st.button("📖 Post Journal", use_container_width=True):
            nav("journals"); st.rerun()
        if st.button("💳 Record Expense", use_container_width=True):
            nav("expenses"); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card"><div class="section-title">Recent Invoices</div>', unsafe_allow_html=True)
        if invs:
            for inv in invs[:5]:
                cname = inv.get("customer", {}).get("name", "—")
                st.markdown(f"**{inv['invoice_number']}** — {cname} — **{inv['total']:,.2f}** `{inv['status']}`")
        else:
            show_info("No invoices yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="section-card"><div class="section-title">Low Stock Alert</div>', unsafe_allow_html=True)
        if low_stock:
            for i in low_stock[:5]:
                st.markdown(f"⚠️ **{i['sku']}** — {i['name']} — stock: **{i['current_stock']}** (reorder: {i['reorder_level']})")
        else:
            show_success("All items healthy.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Third row — approvals panel
    col4, col5 = st.columns(2)
    with col4:
        st.markdown('<div class="section-card"><div class="section-title">Pending PR Approvals</div>', unsafe_allow_html=True)
        if pending_prs:
            for p in pending_prs[:5]:
                st.markdown(f"📝 **{p['pr_number']}** — {p.get('department') or '—'} — {len(p.get('items', []))} items")
            if st.button("→ Manage PRs", key="dash_go_prs", use_container_width=True):
                nav("prs"); st.rerun()
        else:
            show_info("No pending PRs.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="section-card"><div class="section-title">Pending Leave Requests</div>', unsafe_allow_html=True)
        if pending_leaves:
            for l in pending_leaves[:5]:
                emp = l.get("employee", {}).get("full_name", "—") if l.get("employee") else "—"
                st.markdown(f"🌴 **{emp}** — {l['leave_type']} — {l['start_date']} → {l['end_date']} ({l['days']}d)")
            if st.button("→ Manage Leaves", key="dash_go_leaves", use_container_width=True):
                nav("leaves"); st.rerun()
        else:
            show_info("No pending leave requests.")
        st.markdown('</div>', unsafe_allow_html=True)


# ===================================================================
# EMPLOYEES PAGE
# ===================================================================

def page_employees():
    st.markdown('<div class="breadcrumb">Home / Payroll / <strong>Employees</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Employees</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage your workforce — add, edit, and view employee records.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Employee List", "➕ Add Employee"])

    with list_tab:
        try:
            sc, emps = api("GET", "/employees/", token=tk())
            if sc == 200 and emps:
                rows = [{"ID": e["id"], "Code": e["employee_code"], "Name": e["full_name"],
                         "Email": e.get("email") or "—", "Department": e.get("department") or "—",
                         "Designation": e.get("designation") or "—", "Active": "Yes" if e["is_active"] else "No"} for e in emps]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No employees found. Add your first employee!")
            else:
                show_warning(_detail(emps))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("emp_form"):
            c1, c2 = st.columns(2)
            code = c1.text_input("Employee Code *", placeholder="EMP-001")
            name = c2.text_input("Full Name *", placeholder="John Doe")
            email = c1.text_input("Email", placeholder="john@company.com")
            dept = c2.text_input("Department", placeholder="Engineering")
            desig = c1.text_input("Designation", placeholder="Senior Developer")
            jdate = c2.date_input("Joining Date")
            active = st.checkbox("Active", value=True)
            sub = st.form_submit_button("Save Employee", use_container_width=True)
        if sub:
            payload = {"employee_code": code, "full_name": name, "email": email or None,
                       "department": dept or None, "designation": desig or None,
                       "joining_date": str(jdate), "is_active": active}
            try:
                sc, d = api("POST", "/employees/", token=tk(), json=payload)
                if sc == 201:
                    show_success("Employee created successfully!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# SALARY STRUCTURES PAGE
# ===================================================================

def page_salary():
    st.markdown('<div class="breadcrumb">Home / Payroll / <strong>Salary Structures</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Salary Structures</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Define compensation packages for each employee.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Structure List", "➕ Assign Structure"])

    with list_tab:
        try:
            sc, sals = api("GET", "/salary-structures/", token=tk())
            if sc == 200 and sals:
                rows = [{"ID": s["id"], "Employee ID": s["employee_id"],
                         "Basic": f'{s["basic"]:,.2f}', "HRA": f'{s["hra"]:,.2f}',
                         "Allowances": f'{s["allowances"]:,.2f}', "Deductions": f'{s["deductions"]:,.2f}',
                         "Tax %": s["tax_percent"], "Effective": s["effective_from"]} for s in sals]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No salary structures defined yet.")
            else:
                show_warning(_detail(sals))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("sal_form"):
            emp_id = st.number_input("Employee ID *", min_value=1, step=1)
            c1, c2, c3 = st.columns(3)
            basic = c1.number_input("Basic *", min_value=0.0, step=1000.0)
            hra = c2.number_input("HRA", min_value=0.0, step=1000.0)
            allow = c3.number_input("Allowances", min_value=0.0, step=1000.0)
            ded = c1.number_input("Deductions", min_value=0.0, step=500.0)
            tax = c2.number_input("Tax %", min_value=0.0, max_value=100.0, step=1.0)
            eff = c3.date_input("Effective From")
            sub = st.form_submit_button("Save Structure", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/salary-structures/", token=tk(), json={
                    "employee_id": int(emp_id), "basic": basic, "hra": hra,
                    "allowances": allow, "deductions": ded, "tax_percent": tax,
                    "effective_from": str(eff)})
                if sc == 201:
                    show_success("Salary structure saved!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PAYROLL PAGE
# ===================================================================

def page_payroll():
    st.markdown('<div class="breadcrumb">Home / Payroll / <strong>Process Payroll</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Payroll Processing</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Run monthly payroll and download payslips.</div>', unsafe_allow_html=True)

    run_tab, hist_tab = st.tabs(["🚀 Process", "📜 History"])

    with run_tab:
        with st.form("payroll_form"):
            c1, c2 = st.columns(2)
            month = c1.number_input("Month", min_value=1, max_value=12, step=1, value=date.today().month)
            year = c2.number_input("Year", min_value=2024, max_value=2100, value=date.today().year)
            sub = st.form_submit_button("Process Payroll", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/payroll/process", token=tk(), json={"month": int(month), "year": int(year)})
                if sc == 200:
                    show_success(f"Processed **{d.get('processed_count', 0)}** record(s)")
                    skipped = d.get("skipped") or []
                    if skipped:
                        items = "".join(
                            f"<li><strong>{s.get('employee_name', 'Unknown')}</strong> (ID: {s.get('employee_id')}) — {s.get('reason', '')}</li>"
                            for s in skipped
                        )
                        st.markdown(
                            f'<div class="alert-warning">Skipped {len(skipped)} employee(s):'
                            f'<ul style="margin:8px 0 0 20px;padding:0;">{items}</ul></div>',
                            unsafe_allow_html=True,
                        )
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))

    with hist_tab:
        try:
            sc, history = api("GET", "/payroll/history", token=tk())
            if sc == 200 and history:
                rows = [{"ID": r["id"], "Employee": r.get("employee", {}).get("full_name", "—"),
                         "Month/Year": f'{r["month"]:02d}/{r["year"]}',
                         "Gross": f'{r["gross_salary"]:,.2f}', "Deductions": f'{r["deductions"]:,.2f}',
                         "Net": f'{r["net_salary"]:,.2f}', "Status": r["status"]} for r in history]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                st.markdown("**Download Payslip:**")
                # Show download buttons for recent records (up to 5)
                recent = history[:5]
                cols = st.columns(len(recent))
                base = st.session_state.get("api_base_url", DEFAULT_API)
                for idx, r in enumerate(recent):
                    with cols[idx]:
                        try:
                            pdf_resp = requests.get(
                                f"{base.rstrip('/')}/payroll/{r['id']}/payslip",
                                headers={"Authorization": f"Bearer {tk()}"},
                                timeout=30,
                            )
                            if pdf_resp.status_code == 200:
                                emp_name = r.get("employee", {}).get("full_name", "Employee").replace(" ", "_")
                                filename = f"payslip_{emp_name}_{r['month']:02d}_{r['year']}.pdf"
                                st.download_button(
                                    label=f"📄 {r.get('employee', {}).get('full_name', '—')} — {r['month']:02d}/{r['year']}",
                                    data=pdf_resp.content,
                                    file_name=filename,
                                    mime="application/pdf",
                                    key=f"dl_pay_{r['id']}",
                                    use_container_width=True,
                                )
                            else:
                                st.caption(f"⚠️ #{r['id']} unavailable")
                        except Exception:
                            st.caption(f"⚠️ #{r['id']} error")
            elif sc == 200:
                show_info("No payroll history. Process payroll first.")
            else:
                show_warning(_detail(history))
        except requests.RequestException as e:
            show_error(str(e))


# ===================================================================
# CUSTOMERS PAGE
# ===================================================================

def page_customers():
    st.markdown('<div class="breadcrumb">Home / Billing / <strong>Customers</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Customers</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage your clients and billing contacts.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Customer List", "➕ Add Customer"])

    with list_tab:
        try:
            sc, custs = api("GET", "/customers/", token=tk())
            if sc == 200 and custs:
                rows = [{"ID": c["id"], "Name": c["name"], "Email": c.get("email") or "—",
                         "Phone": c.get("phone") or "—", "GSTIN": c.get("gstin") or "—",
                         "Active": "Yes" if c["is_active"] else "No"} for c in custs]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No customers found. Add your first customer!")
            else:
                show_warning(_detail(custs))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("cust_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Customer Name *", placeholder="Acme Corp")
            email = c2.text_input("Email", placeholder="billing@acme.com")
            phone = c1.text_input("Phone", placeholder="+91-9999999999")
            gstin = c2.text_input("GSTIN", placeholder="29ABCDE1234F1Z5")
            addr = st.text_area("Billing Address", height=80)
            sub = st.form_submit_button("Save Customer", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/customers/", token=tk(), json={
                    "name": name, "email": email or None, "phone": phone or None,
                    "gstin": gstin or None, "billing_address": addr or None})
                if sc == 201:
                    show_success("Customer created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# INVOICES PAGE
# ===================================================================

def page_invoices():
    st.markdown('<div class="breadcrumb">Home / Billing / <strong>Invoices</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Invoices</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Create, manage, and export invoices with GST.</div>', unsafe_allow_html=True)

    list_tab, create_tab = st.tabs(["📋 Invoice List", "➕ Create Invoice"])
    base = st.session_state.get("api_base_url", DEFAULT_API)

    with list_tab:
        try:
            sc, invs = api("GET", "/invoices/", token=tk())
            if sc == 200 and invs:
                rows = [{"ID": i["id"], "#": i["invoice_number"],
                         "Customer": i.get("customer", {}).get("name", "—"),
                         "Date": i["invoice_date"], "Subtotal": f'{i["subtotal"]:,.2f}',
                         "Tax": f'{i["tax_amount"]:,.2f}', "Total": f'{i["total"]:,.2f}',
                         "Status": i["status"].upper()} for i in invs]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                st.markdown("**Download Invoices:**")
                for inv in invs[:5]:
                    dc1, dc2, dc3 = st.columns([2, 1, 1])
                    with dc1:
                        st.markdown(f"**#{inv['invoice_number']}** — {inv.get('customer', {}).get('name', '—')}")
                    with dc2:
                        try:
                            pdf_r = requests.get(
                                f"{base.rstrip('/')}/invoices/{inv['id']}/pdf",
                                headers={"Authorization": f"Bearer {tk()}"}, timeout=30,
                            )
                            if pdf_r.status_code == 200:
                                st.download_button(
                                    "📄 PDF", data=pdf_r.content,
                                    file_name=f"invoice_{inv['invoice_number']}.pdf",
                                    mime="application/pdf",
                                    key=f"dl_inv_pdf_{inv['id']}",
                                    use_container_width=True,
                                )
                        except Exception:
                            pass
                    with dc3:
                        try:
                            csv_r = requests.get(
                                f"{base.rstrip('/')}/invoices/{inv['id']}/excel",
                                headers={"Authorization": f"Bearer {tk()}"}, timeout=30,
                            )
                            if csv_r.status_code == 200:
                                st.download_button(
                                    "📊 CSV", data=csv_r.content,
                                    file_name=f"invoice_{inv['invoice_number']}.csv",
                                    mime="text/csv",
                                    key=f"dl_inv_csv_{inv['id']}",
                                    use_container_width=True,
                                )
                        except Exception:
                            pass
            elif sc == 200:
                show_info("No invoices yet. Create your first invoice!")
            else:
                show_warning(_detail(invs))
        except requests.RequestException as e:
            show_error(str(e))

    with create_tab:
        with st.form("inv_form"):
            c1, c2, c3 = st.columns(3)
            cust_id = c1.number_input("Customer ID *", min_value=1, step=1)
            inv_num = c2.text_input("Invoice Number *", placeholder="INV-001")
            inv_date = c3.date_input("Invoice Date")
            c1b, c2b, c3b = st.columns(3)
            due = c1b.date_input("Due Date")
            discount = c2b.number_input("Discount", min_value=0.0, step=100.0)
            status = c3b.selectbox("Status", ["draft", "sent", "paid", "cancelled"])
            notes = st.text_input("Notes")

            st.markdown("---")
            st.markdown("**Line Items** (fill at least 1)")
            items = []
            for i in range(1, 6):
                with st.expander(f"Item {i}", expanded=(i == 1)):
                    ic1, ic2, ic3, ic4 = st.columns(4)
                    desc = ic1.text_input("Description", key=f"d{i}")
                    qty = ic2.number_input("Qty", min_value=0.0, value=1.0, step=1.0, key=f"q{i}")
                    price = ic3.number_input("Unit Price", min_value=0.0, step=100.0, key=f"p{i}")
                    tax = ic4.number_input("Tax %", min_value=0.0, max_value=100.0, step=0.5, key=f"t{i}")
                    if desc and price > 0:
                        items.append({"description": desc, "quantity": qty, "unit_price": price, "tax_rate": tax})

            sub = st.form_submit_button("Create Invoice", use_container_width=True)

        if sub:
            if not items:
                show_error("Add at least one item with description and price.")
            else:
                try:
                    sc, d = api("POST", "/invoices/", token=tk(), json={
                        "customer_id": int(cust_id), "invoice_number": inv_num,
                        "invoice_date": str(inv_date), "due_date": str(due),
                        "discount": discount, "notes": notes or None, "status": status,
                        "items": items})
                    if sc == 201:
                        show_success(f"Invoice **{d.get('invoice_number')}** created — Total: **{d.get('total', 0):,.2f}**")
                    else:
                        show_error(_detail(d))
                except requests.RequestException as e:
                    show_error(str(e))


# ===================================================================
# EXPENSE CATEGORIES PAGE
# ===================================================================

def page_exp_categories():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Expense Categories</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Expense Categories</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Organize your expenses by category.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Categories", "➕ Add Category"])

    with list_tab:
        try:
            sc, cats = api("GET", "/expenses/categories/", token=tk())
            if sc == 200 and cats:
                rows = [{"ID": c["id"], "Name": c["name"], "Description": c.get("description") or "—"} for c in cats]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No categories. Create one to start tracking expenses.")
            else:
                show_warning(_detail(cats))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("cat_form"):
            name = st.text_input("Category Name *", placeholder="Travel, Office Supplies, Utilities...")
            desc = st.text_input("Description", placeholder="Optional description")
            sub = st.form_submit_button("Save Category", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/expenses/categories/", token=tk(), json={"name": name, "description": desc or None})
                if sc == 201:
                    show_success("Category created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# EXPENSES PAGE
# ===================================================================

def page_expenses():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Expenses</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Expenses</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Record and manage business expenses.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Expense List", "➕ Add Expense"])

    with list_tab:
        try:
            sc, exps = api("GET", "/expenses/", token=tk())
            if sc == 200 and exps:
                rows = [{"ID": e["id"], "Title": e["title"],
                         "Category": e.get("category", {}).get("name", "—"),
                         "Amount": f'{e["amount"]:,.2f}', "Date": e["expense_date"],
                         "Receipt": e.get("receipt_filename") or "—"} for e in exps]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No expenses recorded yet.")
            else:
                show_warning(_detail(exps))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("exp_form"):
            c1, c2 = st.columns(2)
            title = c1.text_input("Title *", placeholder="Flight to Mumbai")
            cat_id = c2.number_input("Category ID *", min_value=1, step=1)
            amount = c1.number_input("Amount *", min_value=0.01, step=100.0)
            exp_date = c2.date_input("Date")
            desc = st.text_input("Description", placeholder="Optional details")
            sub = st.form_submit_button("Save Expense", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/expenses/", token=tk(), json={
                    "category_id": int(cat_id), "title": title, "description": desc or None,
                    "amount": amount, "expense_date": str(exp_date)})
                if sc == 201:
                    show_success("Expense recorded!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# REPORTS PAGE
# ===================================================================

def page_reports():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Reports</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">View expense summaries and business analytics.</div>', unsafe_allow_html=True)

    with st.form("report_form"):
        c1, c2 = st.columns(2)
        rmonth = c1.number_input("Month (0 = all)", min_value=0, max_value=12, value=0)
        ryear = c2.number_input("Year (0 = all)", min_value=0, max_value=2100, value=date.today().year)
        sub = st.form_submit_button("Generate Report", use_container_width=True)

    if sub:
        params = {}
        if rmonth > 0:
            params["month"] = int(rmonth)
        if ryear > 0:
            params["year"] = int(ryear)
        try:
            sc, rpt = api("GET", "/expenses/report", token=tk(), params=params)
            if sc == 200:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"""
                    <div class="kpi-card purple" style="margin-bottom:16px;">
                        <div class="kpi-label">Total Expenses</div>
                        <div class="kpi-value">{rpt.get('total', 0):,.2f}</div>
                        <div class="kpi-sub">Period: {rpt.get('period', 'N/A')}</div>
                    </div>
                    """, unsafe_allow_html=True)

                by_cat = rpt.get("by_category", [])
                if by_cat:
                    st.markdown('<div class="section-card"><div class="section-title">Breakdown by Category</div>', unsafe_allow_html=True)
                    rows = [{"Category": c["category_name"], "Total": f'{c["total_amount"]:,.2f}',
                             "# Expenses": c["expense_count"]} for c in by_cat]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Simple bar chart
                    import pandas as pd
                    df = pd.DataFrame(by_cat)
                    if not df.empty:
                        st.bar_chart(df.set_index("category_name")["total_amount"])
                else:
                    show_info("No expenses found for this period.")
            else:
                show_error(_detail(rpt))
        except requests.RequestException as e:
            show_error(str(e))


# ===================================================================
# SETTINGS PAGE
# ===================================================================

def page_settings():
    st.markdown('<div class="breadcrumb">Home / <strong>Settings</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Application configuration and account settings.</div>', unsafe_allow_html=True)

    user = st.session_state.user_profile or {}

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-card"><div class="section-title">API Configuration</div>', unsafe_allow_html=True)
        new_url = st.text_input("API Base URL", value=st.session_state.api_base_url)
        if new_url != st.session_state.api_base_url:
            st.session_state.api_base_url = new_url
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="section-card"><div class="section-title">User Profile</div>', unsafe_allow_html=True)
        st.markdown(f"**Name:** {user.get('full_name', '—')}")
        st.markdown(f"**Email:** {user.get('email', '—')}")
        st.markdown(f"**Role:** {user.get('role', '—').title()}")
        st.markdown(f"**Tenant:** {user.get('tenant', {}).get('name', '—')}")
        st.markdown(f"**Tenant Slug:** {user.get('tenant', {}).get('slug', '—')}")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    if st.button("🚪 Logout", type="primary", use_container_width=True):
        clear_session_cookie()
        st.session_state.auth_page = "login"
        st.session_state.page = "dashboard"
        st.rerun()


# ===================================================================
# PHASE A — HR: ATTENDANCE
# ===================================================================

def page_attendance():
    st.markdown('<div class="breadcrumb">Home / HR / <strong>Attendance</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Attendance</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Record and track daily employee attendance.</div>', unsafe_allow_html=True)

    list_tab, add_tab, sum_tab = st.tabs(["📋 Records", "➕ Mark Attendance", "📊 Summary"])

    with list_tab:
        try:
            sc, data = api("GET", "/attendance/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": r["id"], "Employee": r.get("employee", {}).get("full_name", "—"),
                         "Date": r["date"], "Status": r["status"].upper(),
                         "Check-in": r.get("check_in") or "—",
                         "Check-out": r.get("check_out") or "—",
                         "Notes": r.get("notes") or "—"} for r in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No attendance records yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("att_form"):
            c1, c2 = st.columns(2)
            emp_id = c1.number_input("Employee ID *", min_value=1, step=1)
            att_date = c2.date_input("Date")
            c1b, c2b = st.columns(2)
            check_in = c1b.time_input("Check-in")
            check_out = c2b.time_input("Check-out")
            status_v = st.selectbox("Status", ["present", "absent", "half_day", "leave"])
            notes = st.text_input("Notes")
            sub = st.form_submit_button("Save Attendance", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/attendance/", token=tk(), json={
                    "employee_id": int(emp_id), "date": str(att_date),
                    "check_in": check_in.strftime("%H:%M:%S") if check_in else None,
                    "check_out": check_out.strftime("%H:%M:%S") if check_out else None,
                    "status": status_v, "notes": notes or None,
                })
                if sc == 201:
                    show_success("Attendance recorded!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))

    with sum_tab:
        with st.form("sum_form"):
            c1, c2 = st.columns(2)
            m = c1.number_input("Month (0 = all)", min_value=0, max_value=12, value=date.today().month)
            y = c2.number_input("Year (0 = all)", min_value=0, max_value=2100, value=date.today().year)
            gen = st.form_submit_button("Generate Summary", use_container_width=True)
        if gen:
            params = {}
            if m > 0: params["month"] = int(m)
            if y > 0: params["year"] = int(y)
            try:
                sc, data = api("GET", "/attendance/summary", token=tk(), params=params)
                if sc == 200 and data:
                    rows = [{"Employee": r["employee_name"], "Present": r["present"],
                             "Absent": r["absent"], "Half Day": r["half_day"],
                             "Leave": r["leave"], "Total Days": r["total_days"]} for r in data]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    show_info("No data for this period.")
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE A — HR: LEAVE REQUESTS
# ===================================================================

def page_leaves():
    st.markdown('<div class="breadcrumb">Home / HR / <strong>Leave Requests</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Leave Requests</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Apply, approve, or reject employee leave.</div>', unsafe_allow_html=True)

    user = st.session_state.user_profile or {}
    is_manager = user.get("role", "").lower() in ("admin", "manager")

    list_tab, add_tab = st.tabs(["📋 Requests", "➕ Apply for Leave"])

    with list_tab:
        try:
            sc, data = api("GET", "/leaves/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": r["id"], "Employee": r.get("employee", {}).get("full_name", "—"),
                         "Type": r["leave_type"].upper(),
                         "From": r["start_date"], "To": r["end_date"], "Days": r["days"],
                         "Status": r["status"].upper(), "Reason": r.get("reason") or "—"} for r in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                if is_manager:
                    st.markdown("### Approve / Reject Pending Requests")
                    pending = [r for r in data if r["status"] == "pending"]
                    if not pending:
                        show_info("No pending requests.")
                    else:
                        for r in pending:
                            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
                            c1.markdown(
                                f"**{r.get('employee', {}).get('full_name', '—')}** — "
                                f"{r['leave_type']} — {r['start_date']} → {r['end_date']} ({r['days']}d)"
                            )
                            if c2.button("✅ Approve", key=f"app_{r['id']}", use_container_width=True):
                                sc2, _ = api("PUT", f"/leaves/{r['id']}/approve", token=tk())
                                if sc2 == 200:
                                    show_success("Approved")
                                    st.rerun()
                            if c3.button("❌ Reject", key=f"rej_{r['id']}", use_container_width=True):
                                sc2, _ = api("PUT", f"/leaves/{r['id']}/reject", token=tk(),
                                             json={"approver_comment": "Rejected by manager"})
                                if sc2 == 200:
                                    show_success("Rejected")
                                    st.rerun()
            elif sc == 200:
                show_info("No leave requests yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("leave_form"):
            c1, c2 = st.columns(2)
            emp_id = c1.number_input("Employee ID *", min_value=1, step=1)
            leave_type = c2.selectbox("Leave Type", ["casual", "sick", "earned", "unpaid"])
            c1b, c2b = st.columns(2)
            start = c1b.date_input("Start Date")
            end = c2b.date_input("End Date")
            reason = st.text_area("Reason", height=80)
            sub = st.form_submit_button("Submit Request", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/leaves/", token=tk(), json={
                    "employee_id": int(emp_id), "leave_type": leave_type,
                    "start_date": str(start), "end_date": str(end), "reason": reason or None,
                })
                if sc == 201:
                    show_success("Leave request submitted!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE A — CRM: LEADS
# ===================================================================

def page_leads():
    st.markdown('<div class="breadcrumb">Home / Sales & CRM / <strong>Leads</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Leads</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Track potential customers from first contact to qualification.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Lead List", "➕ Add Lead"])

    with list_tab:
        try:
            sc, data = api("GET", "/leads/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": r["id"], "Name": r["name"], "Company": r.get("company") or "—",
                         "Email": r.get("email") or "—", "Phone": r.get("phone") or "—",
                         "Source": r.get("source") or "—", "Status": r["status"].upper()} for r in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No leads yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("lead_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Name *")
            company = c2.text_input("Company")
            email = c1.text_input("Email")
            phone = c2.text_input("Phone")
            c1b, c2b = st.columns(2)
            source = c1b.selectbox("Source", ["", "website", "referral", "cold_call", "event", "social_media"])
            status_v = c2b.selectbox("Status", ["new", "contacted", "qualified", "lost"])
            notes = st.text_area("Notes", height=80)
            sub = st.form_submit_button("Save Lead", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/leads/", token=tk(), json={
                    "name": name, "company": company or None,
                    "email": email or None, "phone": phone or None,
                    "source": source or None, "status": status_v,
                    "notes": notes or None,
                })
                if sc == 201:
                    show_success("Lead created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE A — CRM: OPPORTUNITIES
# ===================================================================

def page_opportunities():
    st.markdown('<div class="breadcrumb">Home / Sales & CRM / <strong>Opportunities</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Opportunities</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Track deals through the sales pipeline.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Opportunity List", "➕ Add Opportunity"])

    with list_tab:
        try:
            sc, data = api("GET", "/opportunities/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": r["id"], "Title": r["title"],
                         "Customer": r.get("customer", {}).get("name", "—") if r.get("customer") else "—",
                         "Amount": f'{r["expected_amount"]:,.2f}',
                         "Probability": f'{r["probability"]}%',
                         "Stage": r["stage"].upper(),
                         "Close Date": r.get("expected_close_date") or "—"} for r in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                total_pipeline = sum(r["expected_amount"] * r["probability"] / 100 for r in data)
                st.markdown(f"""
                <div class="kpi-card blue" style="margin-top:16px;">
                    <div class="kpi-label">Weighted Pipeline Value</div>
                    <div class="kpi-value">{total_pipeline:,.2f}</div>
                    <div class="kpi-sub">{len(data)} opportunities</div>
                </div>
                """, unsafe_allow_html=True)
            elif sc == 200:
                show_info("No opportunities yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("opp_form"):
            title = st.text_input("Title *", placeholder="Acme Corp - Annual Contract")
            c1, c2 = st.columns(2)
            lead_id = c1.number_input("Lead ID (optional)", min_value=0, step=1)
            cust_id = c2.number_input("Customer ID (optional)", min_value=0, step=1)
            c1b, c2b, c3b = st.columns(3)
            amount = c1b.number_input("Expected Amount", min_value=0.0, step=1000.0)
            prob = c2b.number_input("Probability %", min_value=0, max_value=100, value=50)
            close_date = c3b.date_input("Expected Close Date")
            stage = st.selectbox("Stage",
                ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"])
            notes = st.text_area("Notes", height=80)
            sub = st.form_submit_button("Save Opportunity", use_container_width=True)
        if sub:
            try:
                payload = {
                    "title": title,
                    "expected_amount": amount,
                    "probability": int(prob),
                    "stage": stage,
                    "expected_close_date": str(close_date),
                    "notes": notes or None,
                }
                if lead_id > 0: payload["lead_id"] = int(lead_id)
                if cust_id > 0: payload["customer_id"] = int(cust_id)
                sc, d = api("POST", "/opportunities/", token=tk(), json=payload)
                if sc == 201:
                    show_success("Opportunity created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE A — CRM: QUOTATIONS
# ===================================================================

def page_quotations():
    st.markdown('<div class="breadcrumb">Home / Sales & CRM / <strong>Quotations</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Quotations</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Send price quotes to customers.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Quotation List", "➕ Create Quotation"])

    with list_tab:
        try:
            sc, data = api("GET", "/quotations/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": q["id"], "#": q["quote_number"],
                         "Customer": q.get("customer", {}).get("name", "—"),
                         "Date": q["quote_date"], "Valid Until": q.get("valid_until") or "—",
                         "Subtotal": f'{q["subtotal"]:,.2f}', "Tax": f'{q["tax_amount"]:,.2f}',
                         "Total": f'{q["total"]:,.2f}', "Status": q["status"].upper()} for q in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No quotations yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("quote_form"):
            c1, c2, c3 = st.columns(3)
            cust_id = c1.number_input("Customer ID *", min_value=1, step=1)
            quote_num = c2.text_input("Quote Number *", placeholder="QT-001")
            quote_date = c3.date_input("Quote Date")
            c1b, c2b = st.columns(2)
            valid = c1b.date_input("Valid Until")
            q_status = c2b.selectbox("Status", ["draft", "sent", "accepted", "rejected", "expired"])
            notes = st.text_input("Notes")

            st.markdown("**Line Items**")
            items = []
            for i in range(1, 6):
                with st.expander(f"Item {i}", expanded=(i == 1)):
                    ic1, ic2, ic3, ic4 = st.columns(4)
                    desc = ic1.text_input("Description", key=f"qd{i}")
                    qty = ic2.number_input("Qty", min_value=0.0, value=1.0, step=1.0, key=f"qq{i}")
                    price = ic3.number_input("Unit Price", min_value=0.0, step=100.0, key=f"qp{i}")
                    tax = ic4.number_input("Tax %", min_value=0.0, max_value=100.0, step=0.5, key=f"qt{i}")
                    if desc and price > 0:
                        items.append({"description": desc, "quantity": qty, "unit_price": price, "tax_rate": tax})
            sub = st.form_submit_button("Create Quotation", use_container_width=True)

        if sub:
            if not items:
                show_error("Add at least one item.")
            else:
                try:
                    sc, d = api("POST", "/quotations/", token=tk(), json={
                        "customer_id": int(cust_id), "quote_number": quote_num,
                        "quote_date": str(quote_date), "valid_until": str(valid),
                        "notes": notes or None, "status": q_status, "items": items,
                    })
                    if sc == 201:
                        show_success(f"Quotation **{d.get('quote_number')}** created — Total: **{d.get('total', 0):,.2f}**")
                    else:
                        show_error(_detail(d))
                except requests.RequestException as e:
                    show_error(str(e))


# ===================================================================
# PHASE A — CRM: SALES ORDERS
# ===================================================================

def page_sales_orders():
    st.markdown('<div class="breadcrumb">Home / Sales & CRM / <strong>Sales Orders</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Sales Orders</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Confirmed orders ready for fulfilment.</div>', unsafe_allow_html=True)

    list_tab, add_tab = st.tabs(["📋 Order List", "➕ Create Sales Order"])

    with list_tab:
        try:
            sc, data = api("GET", "/sales-orders/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": o["id"], "#": o["order_number"],
                         "Customer": o.get("customer", {}).get("name", "—"),
                         "Order Date": o["order_date"], "Delivery": o.get("delivery_date") or "—",
                         "Total": f'{o["total"]:,.2f}', "Status": o["status"].upper()} for o in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No sales orders yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("so_form"):
            c1, c2, c3 = st.columns(3)
            cust_id = c1.number_input("Customer ID *", min_value=1, step=1)
            order_num = c2.text_input("Order Number *", placeholder="SO-001")
            order_date = c3.date_input("Order Date")
            c1b, c2b, c3b = st.columns(3)
            quote_id = c1b.number_input("Quotation ID (optional)", min_value=0, step=1)
            delivery = c2b.date_input("Delivery Date")
            o_status = c3b.selectbox("Status", ["draft", "confirmed", "in_production", "delivered", "invoiced", "cancelled"])
            notes = st.text_input("Notes")

            st.markdown("**Line Items**")
            items = []
            for i in range(1, 6):
                with st.expander(f"Item {i}", expanded=(i == 1)):
                    ic1, ic2, ic3, ic4 = st.columns(4)
                    desc = ic1.text_input("Description", key=f"sod{i}")
                    qty = ic2.number_input("Qty", min_value=0.0, value=1.0, step=1.0, key=f"soq{i}")
                    price = ic3.number_input("Unit Price", min_value=0.0, step=100.0, key=f"sop{i}")
                    tax = ic4.number_input("Tax %", min_value=0.0, max_value=100.0, step=0.5, key=f"sot{i}")
                    if desc and price > 0:
                        items.append({"description": desc, "quantity": qty, "unit_price": price, "tax_rate": tax})
            sub = st.form_submit_button("Create Sales Order", use_container_width=True)

        if sub:
            if not items:
                show_error("Add at least one item.")
            else:
                payload = {
                    "customer_id": int(cust_id), "order_number": order_num,
                    "order_date": str(order_date), "delivery_date": str(delivery),
                    "notes": notes or None, "status": o_status, "items": items,
                }
                if quote_id > 0: payload["quotation_id"] = int(quote_id)
                try:
                    sc, d = api("POST", "/sales-orders/", token=tk(), json=payload)
                    if sc == 201:
                        show_success(f"Sales Order **{d.get('order_number')}** created — Total: **{d.get('total', 0):,.2f}**")
                    else:
                        show_error(_detail(d))
                except requests.RequestException as e:
                    show_error(str(e))


# ===================================================================
# USERS MANAGEMENT (Admin only)
# ===================================================================

def page_users():
    st.markdown('<div class="breadcrumb">Home / <strong>User Management</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">User Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Create users with different roles (Admin / Manager / User / Auditor).</div>', unsafe_allow_html=True)

    user = st.session_state.user_profile or {}
    if user.get("role", "").lower() != "admin":
        show_warning("Only admins can manage users.")
        return

    list_tab, add_tab = st.tabs(["👥 Users", "➕ Add User"])

    with list_tab:
        try:
            sc, data = api("GET", "/auth/users", token=tk())
            if sc == 200 and data:
                rows = [{"ID": u["id"], "Name": u["full_name"], "Email": u["email"],
                         "Role": u["role"].upper(), "Active": "Yes" if u["is_active"] else "No"} for u in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with add_tab:
        with st.form("user_form"):
            c1, c2 = st.columns(2)
            full_name = c1.text_input("Full Name *")
            email = c2.text_input("Email *")
            c1b, c2b = st.columns(2)
            password = c1b.text_input("Password *", type="password", help="Min 8 characters")
            role = c2b.selectbox("Role *", ["user", "manager", "admin", "auditor"])
            sub = st.form_submit_button("Create User", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/auth/users", token=tk(), json={
                    "full_name": full_name, "email": email,
                    "password": password, "role": role,
                })
                if sc == 201:
                    show_success(f"User **{d.get('full_name')}** created with role **{d.get('role').upper()}**")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE B — INVENTORY: WAREHOUSES
# ===================================================================

def page_warehouses():
    st.markdown('<div class="breadcrumb">Home / Inventory / <strong>Warehouses</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Warehouses</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage storage locations for your inventory.</div>', unsafe_allow_html=True)

    lt, at = st.tabs(["📋 Warehouses", "➕ Add Warehouse"])
    with lt:
        try:
            sc, data = api("GET", "/warehouses/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": w["id"], "Code": w["code"], "Name": w["name"],
                         "Address": w.get("address") or "—",
                         "Active": "Yes" if w["is_active"] else "No"} for w in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No warehouses yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("wh_form"):
            c1, c2 = st.columns(2)
            code = c1.text_input("Warehouse Code *", placeholder="WH-01")
            name = c2.text_input("Warehouse Name *", placeholder="Main Storage")
            address = st.text_area("Address", height=80)
            sub = st.form_submit_button("Save Warehouse", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/warehouses/", token=tk(), json={
                    "code": code, "name": name, "address": address or None})
                if sc == 201:
                    show_success("Warehouse created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE B — INVENTORY: ITEMS
# ===================================================================

def page_items():
    st.markdown('<div class="breadcrumb">Home / Inventory / <strong>Items</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Items / Products</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Master catalog of items, stock levels, and reorder thresholds.</div>', unsafe_allow_html=True)

    lt, at, low = st.tabs(["📋 Item List", "➕ Add Item", "⚠️ Low Stock"])
    with lt:
        try:
            sc, data = api("GET", "/items/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": i["id"], "SKU": i["sku"], "Name": i["name"], "Unit": i["unit"],
                         "Purchase": f'{i["purchase_price"]:,.2f}', "Sale": f'{i["sale_price"]:,.2f}',
                         "Stock": i["current_stock"], "Reorder At": i["reorder_level"],
                         "Active": "Yes" if i["is_active"] else "No"} for i in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No items yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("item_form"):
            c1, c2 = st.columns(2)
            sku = c1.text_input("SKU *")
            name = c2.text_input("Name *")
            c1b, c2b, c3b = st.columns(3)
            unit = c1b.selectbox("Unit", ["unit", "kg", "ltr", "box", "pack", "dozen", "meter"])
            purchase = c2b.number_input("Purchase Price", min_value=0.0, step=10.0)
            sale = c3b.number_input("Sale Price", min_value=0.0, step=10.0)
            reorder = st.number_input("Reorder Level", min_value=0, step=1)
            desc = st.text_area("Description", height=60)
            sub = st.form_submit_button("Save Item", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/items/", token=tk(), json={
                    "sku": sku, "name": name, "unit": unit,
                    "purchase_price": purchase, "sale_price": sale,
                    "reorder_level": int(reorder), "description": desc or None})
                if sc == 201:
                    show_success("Item created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))

    with low:
        try:
            sc, data = api("GET", "/items/low-stock", token=tk())
            if sc == 200 and data:
                rows = [{"SKU": i["sku"], "Name": i["name"],
                         "Current Stock": i["current_stock"], "Reorder At": i["reorder_level"]}
                        for i in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
                show_warning(f"⚠️ {len(data)} item(s) at or below reorder level — time to reorder.")
            elif sc == 200:
                show_success("✅ All items are above reorder level.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))


# ===================================================================
# PHASE B — INVENTORY: STOCK MOVEMENTS
# ===================================================================

def page_stock_movements():
    st.markdown('<div class="breadcrumb">Home / Inventory / <strong>Stock Movements</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Stock Movements</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Track stock in / out / transfer / adjustments.</div>', unsafe_allow_html=True)

    lt, at = st.tabs(["📋 Movements", "➕ Record Movement"])
    with lt:
        try:
            sc, data = api("GET", "/stock-movements/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": m["id"], "Date": m["movement_date"],
                         "Item": m.get("item", {}).get("name", "—") if m.get("item") else "—",
                         "Warehouse": m.get("warehouse", {}).get("name", "—") if m.get("warehouse") else "—",
                         "Type": m["movement_type"].upper(), "Qty": m["quantity"],
                         "Reference": m.get("reference") or "—"} for m in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No stock movements yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("sm_form"):
            c1, c2 = st.columns(2)
            item_id = c1.number_input("Item ID *", min_value=1, step=1)
            wh_id = c2.number_input("Warehouse ID *", min_value=1, step=1)
            c1b, c2b, c3b = st.columns(3)
            mtype = c1b.selectbox("Type", ["in", "out", "adjustment"])
            qty = c2b.number_input("Quantity", min_value=1, step=1)
            mdate = c3b.date_input("Date")
            ref = st.text_input("Reference (optional)")
            notes = st.text_input("Notes")
            sub = st.form_submit_button("Save Movement", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/stock-movements/", token=tk(), json={
                    "item_id": int(item_id), "warehouse_id": int(wh_id),
                    "movement_type": mtype, "quantity": int(qty),
                    "reference": ref or None, "notes": notes or None,
                    "movement_date": str(mdate)})
                if sc == 201:
                    show_success("Stock movement recorded!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE B — PROCUREMENT: VENDORS
# ===================================================================

def page_vendors():
    st.markdown('<div class="breadcrumb">Home / Procurement / <strong>Vendors</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Vendors</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage suppliers for procurement.</div>', unsafe_allow_html=True)

    lt, at = st.tabs(["📋 Vendor List", "➕ Add Vendor"])
    with lt:
        try:
            sc, data = api("GET", "/vendors/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": v["id"], "Code": v["code"], "Name": v["name"],
                         "Email": v.get("email") or "—", "Phone": v.get("phone") or "—",
                         "GSTIN": v.get("gstin") or "—",
                         "Active": "Yes" if v["is_active"] else "No"} for v in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No vendors yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("ven_form"):
            c1, c2 = st.columns(2)
            code = c1.text_input("Vendor Code *", placeholder="V-001")
            name = c2.text_input("Vendor Name *")
            c1b, c2b = st.columns(2)
            email = c1b.text_input("Email")
            phone = c2b.text_input("Phone")
            gstin = st.text_input("GSTIN")
            address = st.text_area("Address", height=80)
            sub = st.form_submit_button("Save Vendor", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/vendors/", token=tk(), json={
                    "code": code, "name": name,
                    "email": email or None, "phone": phone or None,
                    "gstin": gstin or None, "address": address or None})
                if sc == 201:
                    show_success("Vendor created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE B — PROCUREMENT: PURCHASE REQUISITIONS
# ===================================================================

def page_prs():
    st.markdown('<div class="breadcrumb">Home / Procurement / <strong>Purchase Requisitions</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Purchase Requisitions</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Request items for purchase → approved → converted to PO.</div>', unsafe_allow_html=True)

    user = st.session_state.user_profile or {}
    is_mgr = user.get("role", "").lower() in ("admin", "manager")

    lt, at = st.tabs(["📋 PR List", "➕ Create PR"])
    with lt:
        try:
            sc, data = api("GET", "/prs/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": p["id"], "PR#": p["pr_number"], "Date": p["pr_date"],
                         "Department": p.get("department") or "—",
                         "Items": len(p.get("items", [])),
                         "Status": p["status"].upper()} for p in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                if is_mgr:
                    st.markdown("### Approve / Reject Pending PRs")
                    pending = [p for p in data if p["status"] == "pending"]
                    if not pending:
                        show_info("No pending PRs.")
                    else:
                        for p in pending:
                            c1, c2, c3 = st.columns([3, 1, 1])
                            c1.markdown(f"**{p['pr_number']}** — {p.get('department') or '—'} — {len(p.get('items', []))} items")
                            if c2.button("✅ Approve", key=f"pra_{p['id']}", use_container_width=True):
                                sc2, _ = api("PUT", f"/prs/{p['id']}/approve", token=tk())
                                if sc2 == 200:
                                    show_success("PR approved"); st.rerun()
                            if c3.button("❌ Reject", key=f"prr_{p['id']}", use_container_width=True):
                                sc2, _ = api("PUT", f"/prs/{p['id']}/reject", token=tk(), json={"approver_comment":"Not approved"})
                                if sc2 == 200:
                                    show_success("PR rejected"); st.rerun()
            elif sc == 200:
                show_info("No PRs yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("pr_form"):
            c1, c2 = st.columns(2)
            pr_num = c1.text_input("PR Number *", placeholder="PR-001")
            pr_date = c2.date_input("PR Date")
            dept = st.text_input("Department")
            reason = st.text_area("Reason / Justification", height=60)

            st.markdown("**Items**")
            items = []
            for i in range(1, 6):
                with st.expander(f"Item {i}", expanded=(i == 1)):
                    ic1, ic2, ic3, ic4 = st.columns(4)
                    iid = ic1.number_input("Item ID (optional)", min_value=0, step=1, key=f"pri_id{i}")
                    desc = ic2.text_input("Description", key=f"pri_d{i}")
                    qty = ic3.number_input("Qty", min_value=1, step=1, key=f"pri_q{i}")
                    price = ic4.number_input("Est. Price", min_value=0.0, step=10.0, key=f"pri_p{i}")
                    if desc:
                        row = {"description": desc, "quantity": int(qty), "estimated_price": price}
                        if iid > 0: row["item_id"] = int(iid)
                        items.append(row)
            sub = st.form_submit_button("Create PR", use_container_width=True)

        if sub:
            if not items:
                show_error("Add at least one item.")
            else:
                try:
                    sc, d = api("POST", "/prs/", token=tk(), json={
                        "pr_number": pr_num, "pr_date": str(pr_date),
                        "department": dept or None, "reason": reason or None,
                        "items": items})
                    if sc == 201:
                        show_success(f"PR **{d.get('pr_number')}** created — status: **{d.get('status').upper()}**")
                    else:
                        show_error(_detail(d))
                except requests.RequestException as e:
                    show_error(str(e))


# ===================================================================
# PHASE B — PROCUREMENT: PURCHASE ORDERS
# ===================================================================

def page_pos():
    st.markdown('<div class="breadcrumb">Home / Procurement / <strong>Purchase Orders</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Purchase Orders</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Place and track PO → approval → GRN receipt.</div>', unsafe_allow_html=True)

    user = st.session_state.user_profile or {}
    is_mgr = user.get("role", "").lower() in ("admin", "manager")

    lt, at = st.tabs(["📋 PO List", "➕ Create PO"])
    with lt:
        try:
            sc, data = api("GET", "/pos/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": p["id"], "PO#": p["po_number"],
                         "Vendor": p.get("vendor", {}).get("name", "—"),
                         "Date": p["po_date"], "Delivery": p.get("expected_delivery") or "—",
                         "Total": f'{p["total"]:,.2f}', "Status": p["status"].upper()} for p in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                if is_mgr:
                    st.markdown("### Approve / Reject Pending POs")
                    pending = [p for p in data if p["status"] in ("draft", "pending_approval")]
                    if not pending:
                        show_info("No POs awaiting approval.")
                    else:
                        for p in pending:
                            c1, c2, c3 = st.columns([3, 1, 1])
                            c1.markdown(f"**{p['po_number']}** — {p.get('vendor', {}).get('name', '—')} — {p['total']:,.2f}")
                            if c2.button("✅ Approve", key=f"poa_{p['id']}", use_container_width=True):
                                sc2, _ = api("PUT", f"/pos/{p['id']}/approve", token=tk())
                                if sc2 == 200:
                                    show_success("PO approved"); st.rerun()
                            if c3.button("❌ Reject", key=f"por_{p['id']}", use_container_width=True):
                                sc2, _ = api("PUT", f"/pos/{p['id']}/reject", token=tk(), json={"approver_comment":"Not approved"})
                                if sc2 == 200:
                                    show_success("PO rejected"); st.rerun()
            elif sc == 200:
                show_info("No POs yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("po_form"):
            c1, c2, c3 = st.columns(3)
            vendor_id = c1.number_input("Vendor ID *", min_value=1, step=1)
            po_num = c2.text_input("PO Number *", placeholder="PO-001")
            po_date = c3.date_input("PO Date")
            c1b, c2b, c3b = st.columns(3)
            pr_id = c1b.number_input("PR ID (optional, must be approved)", min_value=0, step=1)
            delivery = c2b.date_input("Expected Delivery")
            po_status = c3b.selectbox("Status", ["draft", "pending_approval"])
            notes = st.text_input("Notes")

            st.markdown("**Items**")
            items = []
            for i in range(1, 6):
                with st.expander(f"Item {i}", expanded=(i == 1)):
                    ic1, ic2, ic3, ic4, ic5 = st.columns(5)
                    iid = ic1.number_input("Item ID", min_value=0, step=1, key=f"poi_id{i}")
                    desc = ic2.text_input("Description", key=f"poi_d{i}")
                    qty = ic3.number_input("Qty", min_value=1, step=1, key=f"poi_q{i}")
                    price = ic4.number_input("Unit Price", min_value=0.0, step=10.0, key=f"poi_p{i}")
                    tax = ic5.number_input("Tax %", min_value=0.0, max_value=100.0, step=0.5, key=f"poi_t{i}")
                    if desc and price > 0:
                        row = {"description": desc, "quantity": int(qty), "unit_price": price, "tax_rate": tax}
                        if iid > 0: row["item_id"] = int(iid)
                        items.append(row)
            sub = st.form_submit_button("Create PO", use_container_width=True)

        if sub:
            if not items:
                show_error("Add at least one item.")
            else:
                payload = {
                    "vendor_id": int(vendor_id), "po_number": po_num,
                    "po_date": str(po_date), "expected_delivery": str(delivery),
                    "status": po_status, "notes": notes or None, "items": items,
                }
                if pr_id > 0: payload["pr_id"] = int(pr_id)
                try:
                    sc, d = api("POST", "/pos/", token=tk(), json=payload)
                    if sc == 201:
                        show_success(f"PO **{d.get('po_number')}** created — Total: **{d.get('total', 0):,.2f}**")
                    else:
                        show_error(_detail(d))
                except requests.RequestException as e:
                    show_error(str(e))


# ===================================================================
# PHASE B — PROCUREMENT: GRN (Goods Receipt Note)
# ===================================================================

def page_grns():
    st.markdown('<div class="breadcrumb">Home / Procurement / <strong>GRN</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Goods Receipt Notes</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Record delivery of approved POs and update stock.</div>', unsafe_allow_html=True)

    lt, at = st.tabs(["📋 GRN List", "➕ Create GRN"])
    with lt:
        try:
            sc, data = api("GET", "/grns/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": g["id"], "GRN#": g["grn_number"], "Date": g["grn_date"],
                         "PO ID": g["po_id"],
                         "Warehouse": g.get("warehouse", {}).get("name", "—") if g.get("warehouse") else "—",
                         "Items": len(g.get("items", [])),
                         "Status": g["status"].upper()} for g in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No GRNs yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("grn_form"):
            c1, c2, c3 = st.columns(3)
            po_id = c1.number_input("PO ID * (must be approved)", min_value=1, step=1)
            grn_num = c2.text_input("GRN Number *", placeholder="GRN-001")
            grn_date = c3.date_input("GRN Date")
            c1b, c2b = st.columns(2)
            wh_id = c1b.number_input("Warehouse ID (optional, for stock)", min_value=0, step=1)
            g_status = c2b.selectbox("Status", ["received", "partial", "rejected"])
            notes = st.text_input("Notes")

            st.markdown("**Received Items**")
            items = []
            for i in range(1, 6):
                with st.expander(f"Item {i}", expanded=(i == 1)):
                    ic1, ic2, ic3, ic4, ic5 = st.columns(5)
                    poi_id = ic1.number_input("PO Item ID", min_value=0, step=1, key=f"gi_poi{i}")
                    iid = ic2.number_input("Item ID", min_value=0, step=1, key=f"gi_i{i}")
                    desc = ic3.text_input("Description", key=f"gi_d{i}")
                    rcv = ic4.number_input("Received Qty", min_value=0, step=1, key=f"gi_r{i}")
                    rej = ic5.number_input("Rejected Qty", min_value=0, step=1, key=f"gi_x{i}")
                    if desc and rcv > 0:
                        row = {"description": desc, "received_quantity": int(rcv),
                               "rejected_quantity": int(rej)}
                        if poi_id > 0: row["po_item_id"] = int(poi_id)
                        if iid > 0: row["item_id"] = int(iid)
                        items.append(row)
            sub = st.form_submit_button("Create GRN", use_container_width=True)

        if sub:
            if not items:
                show_error("Add at least one received item.")
            else:
                payload = {
                    "po_id": int(po_id), "grn_number": grn_num,
                    "grn_date": str(grn_date), "status": g_status,
                    "notes": notes or None, "items": items,
                }
                if wh_id > 0: payload["warehouse_id"] = int(wh_id)
                try:
                    sc, d = api("POST", "/grns/", token=tk(), json=payload)
                    if sc == 201:
                        show_success(f"GRN **{d.get('grn_number')}** created — stock updated.")
                    else:
                        show_error(_detail(d))
                except requests.RequestException as e:
                    show_error(str(e))


# ===================================================================
# PHASE C — FINANCE: CHART OF ACCOUNTS
# ===================================================================

def page_accounts():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Chart of Accounts</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Chart of Accounts</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Ledger accounts by type: asset, liability, equity, income, expense.</div>', unsafe_allow_html=True)

    lt, at = st.tabs(["📋 Accounts", "➕ Add Account"])
    with lt:
        try:
            sc, data = api("GET", "/accounts/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": a["id"], "Code": a["code"], "Name": a["name"],
                         "Type": a["account_type"].upper(),
                         "Active": "Yes" if a["is_active"] else "No"} for a in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No accounts yet. Click 'Seed Default COA' to bootstrap.")
                if st.button("🌱 Seed Default Chart of Accounts"):
                    sc2, d2 = api("POST", "/accounts/seed-default", token=tk())
                    if sc2 == 200:
                        show_success(f"Created {len(d2)} default accounts")
                        st.rerun()
                    else:
                        show_error(_detail(d2))
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("acc_form"):
            c1, c2 = st.columns(2)
            code = c1.text_input("Account Code *", placeholder="5600")
            name = c2.text_input("Account Name *")
            c1b, c2b = st.columns(2)
            atype = c1b.selectbox("Type *", ["asset", "liability", "equity", "income", "expense"])
            parent = c2b.number_input("Parent Account ID (optional)", min_value=0, step=1)
            desc = st.text_area("Description", height=60)
            sub = st.form_submit_button("Save Account", use_container_width=True)
        if sub:
            payload = {"code": code, "name": name, "account_type": atype,
                       "description": desc or None}
            if parent > 0: payload["parent_id"] = int(parent)
            try:
                sc, d = api("POST", "/accounts/", token=tk(), json=payload)
                if sc == 201:
                    show_success("Account created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE C — FINANCE: JOURNAL ENTRIES
# ===================================================================

def page_journals():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Journal Entries</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Journal Entries</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Double-entry journal postings — debits must equal credits.</div>', unsafe_allow_html=True)

    lt, at = st.tabs(["📋 Entries", "➕ New Entry"])

    # fetch accounts for dropdowns
    accounts = []
    try:
        sc, accounts = api("GET", "/accounts/", token=tk())
        if sc != 200:
            accounts = []
    except Exception:
        accounts = []

    with lt:
        try:
            sc, data = api("GET", "/journals/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": e["id"], "#": e["entry_number"], "Date": e["entry_date"],
                         "Ref": e.get("reference") or "—",
                         "Description": (e.get("description") or "")[:50],
                         "Debit": f'{e["total_debit"]:,.2f}',
                         "Credit": f'{e["total_credit"]:,.2f}',
                         "Status": e["status"].upper()} for e in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                # Reverse buttons for posted entries
                st.markdown("### Reverse an Entry")
                posted = [e for e in data if e["status"] == "posted"]
                if posted:
                    opts = {f"#{e['entry_number']} — {e.get('description') or ''}": e["id"] for e in posted}
                    sel = st.selectbox("Select entry to reverse", list(opts.keys()))
                    if st.button("↩️ Create Reversing Entry"):
                        sc2, d2 = api("PUT", f"/journals/{opts[sel]}/reverse", token=tk())
                        if sc2 == 200:
                            show_success(f"Reversed — new entry #{d2.get('entry_number')}")
                            st.rerun()
                        else:
                            show_error(_detail(d2))
            elif sc == 200:
                show_info("No journal entries yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        if not accounts:
            show_warning("Create Chart of Accounts first.")
            return

        acc_options = {f'{a["code"]} — {a["name"]} ({a["account_type"]})': a["id"] for a in accounts}
        acc_labels = [""] + list(acc_options.keys())

        with st.form("je_form"):
            c1, c2, c3 = st.columns(3)
            num = c1.text_input("Entry Number *", placeholder="JE-001")
            edate = c2.date_input("Entry Date")
            ref = c3.text_input("Reference")
            desc = st.text_input("Description")
            st_val = st.selectbox("Status", ["posted", "draft"])

            st.markdown("**Journal Lines** (debits must equal credits)")
            lines = []
            for i in range(1, 7):
                with st.expander(f"Line {i}", expanded=(i <= 2)):
                    lc1, lc2, lc3, lc4 = st.columns(4)
                    acc_label = lc1.selectbox(f"Account {i}", acc_labels, key=f"jel_a{i}")
                    debit = lc2.number_input("Debit", min_value=0.0, step=100.0, key=f"jel_d{i}")
                    credit = lc3.number_input("Credit", min_value=0.0, step=100.0, key=f"jel_c{i}")
                    narr = lc4.text_input("Narration", key=f"jel_n{i}")
                    if acc_label and (debit > 0 or credit > 0):
                        lines.append({
                            "account_id": acc_options[acc_label],
                            "debit": debit, "credit": credit,
                            "narration": narr or None,
                        })
            sub = st.form_submit_button("Post Journal Entry", use_container_width=True)

        if sub:
            total_d = sum(l["debit"] for l in lines)
            total_c = sum(l["credit"] for l in lines)
            if len(lines) < 2:
                show_error("Need at least 2 lines.")
            elif abs(total_d - total_c) > 0.01:
                show_error(f"Entry not balanced: debit {total_d:,.2f} ≠ credit {total_c:,.2f}")
            else:
                try:
                    sc, d = api("POST", "/journals/", token=tk(), json={
                        "entry_number": num, "entry_date": str(edate),
                        "reference": ref or None, "description": desc or None,
                        "status": st_val, "lines": lines,
                    })
                    if sc == 201:
                        show_success(f"Entry **{num}** posted — Dr {total_d:,.2f} = Cr {total_c:,.2f}")
                    else:
                        show_error(_detail(d))
                except requests.RequestException as e:
                    show_error(str(e))


# ===================================================================
# PHASE C — FINANCE: FIXED ASSETS
# ===================================================================

def page_fixed_assets():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Fixed Assets</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Fixed Assets Register</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage long-term assets and run straight-line depreciation.</div>', unsafe_allow_html=True)

    lt, at = st.tabs(["📋 Assets", "➕ Add Asset"])
    with lt:
        try:
            sc, data = api("GET", "/fixed-assets/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": a["id"], "Code": a["asset_code"], "Name": a["name"],
                         "Category": a.get("category") or "—",
                         "Cost": f'{a["purchase_cost"]:,.2f}',
                         "Accum. Depr.": f'{a["accumulated_depreciation"]:,.2f}',
                         "NBV": f'{a["net_book_value"]:,.2f}',
                         "Annual": f'{a["annual_depreciation"]:,.2f}',
                         "Status": a["status"].upper()} for a in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                st.markdown("### Run Annual Depreciation")
                opts = {f'{a["asset_code"]} — {a["name"]}': a["id"] for a in data if a["status"] == "active"}
                if opts:
                    sel = st.selectbox("Select asset", list(opts.keys()))
                    if st.button("🗓️ Apply 1 Year Depreciation"):
                        sc2, d2 = api("POST", f"/fixed-assets/{opts[sel]}/depreciate", token=tk())
                        if sc2 == 200:
                            show_success(f"Depreciation applied. New NBV: {d2['net_book_value']:,.2f}")
                            st.rerun()
                        else:
                            show_error(_detail(d2))
            elif sc == 200:
                show_info("No assets yet.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with at:
        with st.form("fa_form"):
            c1, c2 = st.columns(2)
            code = c1.text_input("Asset Code *", placeholder="FA-001")
            name = c2.text_input("Asset Name *")
            c1b, c2b = st.columns(2)
            cat = c1b.selectbox("Category", ["", "building", "vehicle", "equipment", "furniture", "computer"])
            pdate = c2b.date_input("Purchase Date")
            c1c, c2c, c3c = st.columns(3)
            cost = c1c.number_input("Purchase Cost *", min_value=0.01, step=1000.0)
            salvage = c2c.number_input("Salvage Value", min_value=0.0, step=100.0)
            years = c3c.number_input("Useful Life (years)", min_value=1, max_value=50, value=5)
            notes = st.text_area("Notes", height=60)
            sub = st.form_submit_button("Save Asset", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/fixed-assets/", token=tk(), json={
                    "asset_code": code, "name": name, "category": cat or None,
                    "purchase_date": str(pdate), "purchase_cost": cost,
                    "salvage_value": salvage, "useful_life_years": int(years),
                    "notes": notes or None,
                })
                if sc == 201:
                    show_success(f"Asset created. Annual depreciation: {d['annual_depreciation']:,.2f}")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE C — FINANCE: BANK & RECONCILIATION
# ===================================================================

def page_bank():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Bank Accounts</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Bank & Reconciliation</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Manage bank accounts, record transactions, and reconcile.</div>', unsafe_allow_html=True)

    acc_tab, txn_tab, rec_tab = st.tabs(["🏦 Accounts", "💸 Transactions", "✅ Reconcile"])

    # -- Accounts --
    with acc_tab:
        try:
            sc, data = api("GET", "/bank/accounts/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": a["id"], "Bank": a["bank_name"], "Account": a["account_number"],
                         "Name": a["account_name"], "IFSC": a.get("ifsc_code") or "—",
                         "Opening": f'{a["opening_balance"]:,.2f}',
                         "Current": f'{a["current_balance"]:,.2f}'} for a in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No bank accounts yet.")
        except requests.RequestException as e:
            show_error(str(e))

        st.markdown("### Add Bank Account")
        with st.form("bank_acc_form"):
            c1, c2 = st.columns(2)
            bank = c1.text_input("Bank Name *")
            acc_num = c2.text_input("Account Number *")
            c1b, c2b = st.columns(2)
            acc_name = c1b.text_input("Account Holder Name *")
            ifsc = c2b.text_input("IFSC")
            opening = st.number_input("Opening Balance", value=0.0, step=1000.0)
            sub = st.form_submit_button("Save Bank Account", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/bank/accounts/", token=tk(), json={
                    "bank_name": bank, "account_number": acc_num,
                    "account_name": acc_name, "ifsc_code": ifsc or None,
                    "opening_balance": opening,
                })
                if sc == 201:
                    show_success("Bank account created!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))

    # -- Transactions --
    with txn_tab:
        try:
            sc, data = api("GET", "/bank/transactions/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": t["id"], "Date": t["txn_date"], "Account ID": t["bank_account_id"],
                         "Description": t["description"], "Ref": t.get("reference") or "—",
                         "Deposit": f'{t["deposit"]:,.2f}' if t["deposit"] else "—",
                         "Withdrawal": f'{t["withdrawal"]:,.2f}' if t["withdrawal"] else "—",
                         "Reconciled": "✅" if t["reconciled"] else "❌"} for t in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            elif sc == 200:
                show_info("No transactions yet.")
        except requests.RequestException as e:
            show_error(str(e))

        st.markdown("### Record Transaction")
        with st.form("bank_txn_form"):
            c1, c2, c3 = st.columns(3)
            acc_id = c1.number_input("Bank Account ID *", min_value=1, step=1)
            txn_date = c2.date_input("Date")
            ref = c3.text_input("Reference")
            desc = st.text_input("Description *")
            c1b, c2b = st.columns(2)
            deposit = c1b.number_input("Deposit", min_value=0.0, step=100.0)
            wd = c2b.number_input("Withdrawal", min_value=0.0, step=100.0)
            sub = st.form_submit_button("Save Transaction", use_container_width=True)
        if sub:
            try:
                sc, d = api("POST", "/bank/transactions/", token=tk(), json={
                    "bank_account_id": int(acc_id), "txn_date": str(txn_date),
                    "description": desc, "reference": ref or None,
                    "deposit": deposit, "withdrawal": wd,
                })
                if sc == 201:
                    show_success("Transaction recorded!")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))

    # -- Reconciliation --
    with rec_tab:
        try:
            sc, data = api("GET", "/bank/transactions/", token=tk(), params={"reconciled": "false"})
            if sc == 200 and data:
                show_warning(f"{len(data)} transaction(s) awaiting reconciliation")
                for t in data[:20]:
                    c1, c2 = st.columns([4, 1])
                    amt = t["deposit"] or -t["withdrawal"]
                    c1.markdown(f"**{t['txn_date']}** — {t['description']} — **{amt:,.2f}**")
                    if c2.button("✅ Reconcile", key=f"rec_{t['id']}"):
                        sc2, _ = api("PUT", f"/bank/transactions/{t['id']}/reconcile", token=tk())
                        if sc2 == 200:
                            show_success("Reconciled"); st.rerun()
            elif sc == 200:
                show_success("✅ All transactions reconciled")
        except requests.RequestException as e:
            show_error(str(e))


# ===================================================================
# PHASE C — FINANCIAL REPORTS
# ===================================================================

def page_financial_reports():
    st.markdown('<div class="breadcrumb">Home / Finance / <strong>Financial Reports</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Financial Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Trial Balance, Profit & Loss, Balance Sheet.</div>', unsafe_allow_html=True)

    tb_tab, pnl_tab, bs_tab = st.tabs(["⚖️ Trial Balance", "📊 P&L", "📘 Balance Sheet"])

    with tb_tab:
        as_of = st.date_input("As of date", value=date.today(), key="tb_date")
        if st.button("Generate Trial Balance", use_container_width=True):
            try:
                sc, d = api("GET", "/financial-reports/trial-balance", token=tk(),
                            params={"as_of": str(as_of)})
                if sc == 200:
                    rows = [{"Code": r["code"], "Account": r["name"],
                             "Type": r["account_type"].upper(),
                             "Debit": f'{r["debit"]:,.2f}' if r["debit"] else "",
                             "Credit": f'{r["credit"]:,.2f}' if r["credit"] else ""}
                            for r in d["rows"]]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                    c1, c2 = st.columns(2)
                    c1.markdown(f"**Total Debit:** {d['total_debit']:,.2f}")
                    c2.markdown(f"**Total Credit:** {d['total_credit']:,.2f}")
                    if abs(d["total_debit"] - d["total_credit"]) < 0.01:
                        show_success("✅ Trial Balance is balanced")
                    else:
                        show_error(f"⚠️ Imbalance: {d['total_debit'] - d['total_credit']:,.2f}")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))

    with pnl_tab:
        c1, c2 = st.columns(2)
        start = c1.date_input("From", value=date(date.today().year, 1, 1), key="pnl_start")
        end = c2.date_input("To", value=date.today(), key="pnl_end")
        if st.button("Generate P&L", use_container_width=True):
            try:
                sc, d = api("GET", "/financial-reports/profit-and-loss", token=tk(),
                            params={"period_start": str(start), "period_end": str(end)})
                if sc == 200:
                    st.markdown("#### Income")
                    if d["income"]:
                        st.dataframe(
                            [{"Code": i["code"], "Account": i["name"], "Amount": f'{i["amount"]:,.2f}'}
                             for i in d["income"]], use_container_width=True, hide_index=True)
                    st.markdown(f"**Total Income: {d['total_income']:,.2f}**")
                    st.markdown("#### Expenses")
                    if d["expenses"]:
                        st.dataframe(
                            [{"Code": e["code"], "Account": e["name"], "Amount": f'{e["amount"]:,.2f}'}
                             for e in d["expenses"]], use_container_width=True, hide_index=True)
                    st.markdown(f"**Total Expenses: {d['total_expenses']:,.2f}**")
                    net = d["net_profit"]
                    cls = "alert-success" if net >= 0 else "alert-error"
                    st.markdown(
                        f'<div class="{cls}" style="font-size:20px;text-align:center;">'
                        f'Net Profit: {net:,.2f}</div>', unsafe_allow_html=True)
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))

    with bs_tab:
        as_of_bs = st.date_input("As of date", value=date.today(), key="bs_date")
        if st.button("Generate Balance Sheet", use_container_width=True):
            try:
                sc, d = api("GET", "/financial-reports/balance-sheet", token=tk(),
                            params={"as_of": str(as_of_bs)})
                if sc == 200:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### Assets")
                        if d["assets"]:
                            st.dataframe(
                                [{"Code": a["code"], "Name": a["name"], "Amount": f'{a["amount"]:,.2f}'}
                                 for a in d["assets"]], use_container_width=True, hide_index=True)
                        st.markdown(f"**Total Assets: {d['total_assets']:,.2f}**")
                    with c2:
                        st.markdown("#### Liabilities")
                        if d["liabilities"]:
                            st.dataframe(
                                [{"Code": l["code"], "Name": l["name"], "Amount": f'{l["amount"]:,.2f}'}
                                 for l in d["liabilities"]], use_container_width=True, hide_index=True)
                        st.markdown(f"**Total Liabilities: {d['total_liabilities']:,.2f}**")
                        st.markdown("#### Equity")
                        if d["equity"]:
                            st.dataframe(
                                [{"Code": e["code"], "Name": e["name"], "Amount": f'{e["amount"]:,.2f}'}
                                 for e in d["equity"]], use_container_width=True, hide_index=True)
                        st.markdown(f"**Retained Earnings: {d['retained_earnings']:,.2f}**")
                        st.markdown(f"**Total Equity: {d['total_equity']:,.2f}**")
                    # Check: assets = liabilities + equity
                    diff = d["total_assets"] - (d["total_liabilities"] + d["total_equity"])
                    if abs(diff) < 0.01:
                        show_success("✅ Balance Sheet balances")
                    else:
                        show_error(f"⚠️ Imbalance: {diff:,.2f}")
                else:
                    show_error(_detail(d))
            except requests.RequestException as e:
                show_error(str(e))


# ===================================================================
# PHASE D — DMS (Document Management)
# ===================================================================

def page_documents():
    st.markdown('<div class="breadcrumb">Home / DMS / <strong>Documents</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Document Management</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Upload, version, and download business documents.</div>', unsafe_allow_html=True)

    lt, up_tab = st.tabs(["📋 Documents", "📤 Upload New"])
    base = st.session_state.get("api_base_url", DEFAULT_API)

    with lt:
        try:
            sc, data = api("GET", "/documents/", token=tk())
            if sc == 200 and data:
                rows = [{"ID": d["id"], "Title": d["title"],
                         "Category": d.get("category") or "—",
                         "Tags": d.get("tags") or "—",
                         "Current Version": f'v{d["current_version"]}',
                         "Versions": len(d.get("versions", [])),
                         "Created": (d.get("created_at") or "").split("T")[0]} for d in data]
                st.dataframe(rows, use_container_width=True, hide_index=True)

                st.markdown("### Download / Upload New Version")
                opts = {f'#{d["id"]} — {d["title"]} (v{d["current_version"]})': d for d in data}
                sel_label = st.selectbox("Select document", list(opts.keys()))
                doc = opts[sel_label]

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Versions:**")
                    for v in doc.get("versions", []):
                        try:
                            resp = requests.get(
                                f"{base.rstrip('/')}/documents/{doc['id']}/versions/{v['version_number']}/download",
                                headers={"Authorization": f"Bearer {tk()}"}, timeout=30,
                            )
                            if resp.status_code == 200:
                                st.download_button(
                                    f"⬇️ v{v['version_number']} — {v['filename']} ({v['file_size']:,} bytes)",
                                    data=resp.content, file_name=v["filename"],
                                    mime=v.get("mime_type") or "application/octet-stream",
                                    key=f"dl_doc_{doc['id']}_v{v['version_number']}",
                                    use_container_width=True,
                                )
                        except Exception:
                            pass

                with c2:
                    st.markdown("**Upload new version:**")
                    new_file = st.file_uploader("File", key=f"nv_{doc['id']}")
                    notes = st.text_input("Change notes", key=f"nv_notes_{doc['id']}")
                    if st.button("📤 Upload new version", key=f"nv_btn_{doc['id']}", use_container_width=True):
                        if not new_file:
                            show_error("Please choose a file.")
                        else:
                            try:
                                files = {"file": (new_file.name, new_file.getvalue(), new_file.type or "application/octet-stream")}
                                resp = requests.post(
                                    f"{base.rstrip('/')}/documents/{doc['id']}/versions",
                                    headers={"Authorization": f"Bearer {tk()}"},
                                    files=files, data={"change_notes": notes or ""}, timeout=60,
                                )
                                if resp.status_code == 200:
                                    show_success(f"v{resp.json().get('current_version')} uploaded")
                                    st.rerun()
                                else:
                                    show_error(resp.text[:200])
                            except Exception as e:
                                show_error(str(e))
            elif sc == 200:
                show_info("No documents yet. Upload your first document.")
            else:
                show_warning(_detail(data))
        except requests.RequestException as e:
            show_error(str(e))

    with up_tab:
        with st.form("doc_upload_form"):
            title = st.text_input("Title *")
            c1, c2 = st.columns(2)
            category = c1.selectbox("Category",
                ["", "contract", "invoice_scan", "compliance", "policy", "report", "other"])
            tags = c2.text_input("Tags (comma-separated)")
            description = st.text_area("Description", height=60)
            upfile = st.file_uploader("File *")
            change_notes = st.text_input("Initial version notes")
            sub = st.form_submit_button("Upload Document", use_container_width=True)
        if sub:
            if not upfile or not title:
                show_error("Title and file are required.")
            else:
                try:
                    files = {"file": (upfile.name, upfile.getvalue(), upfile.type or "application/octet-stream")}
                    data_form = {
                        "title": title,
                        "description": description or "",
                        "category": category or "",
                        "tags": tags or "",
                        "change_notes": change_notes or "",
                    }
                    resp = requests.post(
                        f"{base.rstrip('/')}/documents/",
                        headers={"Authorization": f"Bearer {tk()}"},
                        files=files, data=data_form, timeout=60,
                    )
                    if resp.status_code == 201:
                        show_success(f"Document '{title}' uploaded as v1")
                    else:
                        show_error(resp.text[:200])
                except Exception as e:
                    show_error(str(e))


# ===================================================================
# PHASE D — AUDIT LOG
# ===================================================================

def page_audit():
    st.markdown('<div class="breadcrumb">Home / Security / <strong>Audit Log</strong></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-header">Audit Log</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">Who did what, and when. Tracks logins, creates, updates, approvals, deletions.</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    days = c1.number_input("Last N days", min_value=1, max_value=365, value=30)
    action = c2.selectbox("Action", ["", "LOGIN", "CREATE", "UPDATE", "DELETE", "APPROVE", "REJECT", "VERSION"])
    res_type = c3.text_input("Resource type", placeholder="e.g. invoice, user")
    limit = c4.number_input("Limit", min_value=10, max_value=1000, value=200)
    if st.button("🔍 Refresh", use_container_width=True):
        st.rerun()

    try:
        params = {"days": int(days), "limit": int(limit)}
        if action: params["action"] = action
        if res_type: params["resource_type"] = res_type
        sc, data = api("GET", "/audit-logs/", token=tk(), params=params)
        if sc == 200 and data:
            rows = [{"Time": (r.get("created_at") or "").replace("T", " ").split(".")[0],
                     "User": r.get("user_email") or f'#{r.get("user_id")}',
                     "Action": r["action"], "Resource": r["resource_type"],
                     "ID": r.get("resource_id") or "—",
                     "IP": r.get("ip_address") or "—",
                     "Description": r.get("description") or ""} for r in data]
            st.dataframe(rows, use_container_width=True, hide_index=True)
            show_info(f"Showing {len(data)} audit log entries")
        elif sc == 200:
            show_info("No audit log entries match the filters.")
        else:
            show_warning(_detail(data))
    except requests.RequestException as e:
        show_error(str(e))


# ===================================================================
# MAIN ROUTER
# ===================================================================

PAGES = {
    "dashboard": page_dashboard,
    "employees": page_employees,
    "salary": page_salary,
    "payroll": page_payroll,
    "attendance": page_attendance,
    "leaves": page_leaves,
    "customers": page_customers,
    "invoices": page_invoices,
    "leads": page_leads,
    "opportunities": page_opportunities,
    "quotations": page_quotations,
    "sales_orders": page_sales_orders,
    "warehouses": page_warehouses,
    "items": page_items,
    "stock_movements": page_stock_movements,
    "vendors": page_vendors,
    "prs": page_prs,
    "pos": page_pos,
    "grns": page_grns,
    "accounts": page_accounts,
    "journals": page_journals,
    "fixed_assets": page_fixed_assets,
    "bank": page_bank,
    "fin_reports": page_financial_reports,
    "documents": page_documents,
    "audit": page_audit,
    "exp_categories": page_exp_categories,
    "expenses": page_expenses,
    "reports": page_reports,
    "users": page_users,
    "settings": page_settings,
}

# Inject global CSS
st.markdown(THEME_CSS, unsafe_allow_html=True)

# Hide the CachedWidgetWarning banner from extra_streamlit_components
hide_cached_widget_warning()

# Restore session from cookie on page load (survives refresh)
restore_session_from_cookie()

# Auto-logout if session expired
if check_session_expired():
    st.warning("⏰ Your session has expired. Please log in again.")
    st.session_state.auth_page = "login"

if not st.session_state.token:
    if st.session_state.auth_page == "register":
        page_register()
    else:
        page_login()
else:
    render_sidebar()
    page_fn = PAGES.get(st.session_state.page, page_dashboard)
    page_fn()

    # Show session expiry countdown in footer
    exp_str = st.session_state.get("session_expires_at")
    if exp_str:
        try:
            exp = datetime.fromisoformat(exp_str)
            remaining = exp - datetime.utcnow()
            mins = max(0, int(remaining.total_seconds() // 60))
            secs = max(0, int(remaining.total_seconds() % 60))
            st.sidebar.markdown(
                f'<div style="color:#64748b;font-size:11px;text-align:center;margin-top:8px;">'
                f'Session expires in {mins}m {secs}s</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            pass
