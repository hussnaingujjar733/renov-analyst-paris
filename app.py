import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import random

# --- PAGE CONFIG ---
st.set_page_config(page_title="Renov'Analyst PRO", page_icon="🏢", layout="wide", initial_sidebar_state="expanded")

# --- EXECUTIVE DARK CSS ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    div[data-testid="stMetric"] {
        background-color: #17181D;
        border: 1px solid #2E303A;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        border-left: 4px solid #FF4B4B;
        transition: transform 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        border-color: #FF4B4B;
    }
    div[data-testid="stMetric"] label {
        color: #A0AEC0 !important;
        font-weight: 600;
        font-size: 14px;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF4B4B 0%, #FF6B6B 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
    }
    [data-testid="stSidebar"] {
        border-right: 1px solid #2E303A;
    }
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE MEMORY & SECURITY ---
if 'raw_data' not in st.session_state:
    st.session_state.raw_data = pd.DataFrame()
if 'city_coords' not in st.session_state:
    st.session_state.city_coords = (48.8566, 2.3522)
if 'is_unlocked' not in st.session_state:
    st.session_state.is_unlocked = False

# THE SECRET PASSWORD
SECRET_PASSWORD = "CEO2026"

# --- FUNCTIONS ---
def get_city_center(zipcode):
    try:
        url = f"https://geo.api.gouv.fr/communes?codePostal={zipcode}&fields=centre"
        r = requests.get(url).json()
        if r: return r[0]['centre']['coordinates'][1], r[0]['centre']['coordinates'][0]
    except: pass
    return 48.8566, 2.3522

def geocode_exact_address(address, default_lat, default_lon):
    try:
        url = f"https://api-adresse.data.gouv.fr/search/?q={address}&limit=1"
        res = requests.get(url).json()
        if res and len(res.get('features', [])) > 0:
            coords = res['features'][0]['geometry']['coordinates']
            return coords[1], coords[0] 
    except: pass
    return default_lat + random.uniform(-0.005, 0.005), default_lon + random.uniform(-0.005, 0.005)

def mask_address(address):
    """Jadoogar ki trick: Address ka pehla hissa dikhao, baaki chupa do"""
    parts = str(address).split()
    if len(parts) > 1:
        return f"{parts[0]} {parts[1]} ... [🔒 MASQUÉ]"
    return "[🔒 MASQUÉ]"

def fetch_live_ademe_data(zipcode, limit=50):
    dataset_id = "meg-83tjwtg8dyz4vv7h1dqe" 
    url = f"https://data.ademe.fr/data-fair/api/v1/datasets/{dataset_id}/lines"
    params = {"page": 1, "size": limit, "q": zipcode}
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json().get('results', [])
            clean_data = []
            for item in data:
                addr = item.get('Adresse_brute') or item.get('adresse_ban') or "Inconnu"
                dpe = str(item.get('etiquette_dpe') or item.get('Etiquette_DPE') or "N/A").upper()
                surface = item.get('surface_habitable_logement') or 30
                
                is_critical = dpe in ['E', 'F', 'G']
                cost_est = surface * 1200 if dpe in ['F', 'G'] else (surface * 600 if dpe == 'E' else 0)

                clean_data.append({
                    "Vraie_Adresse": addr, # Asli address hidden column mein
                    "Address": addr,       # Display column
                    "Code Postal": zipcode,
                    "DPE": dpe,
                    "Surface (m²)": float(surface),
                    "Coût Rénov. (€)": cost_est,
                    "Status": "CRITICAL" if dpe in ['F', 'G'] else ("WARNING" if dpe == 'E' else "OK")
                })
            return pd.DataFrame(clean_data)
    except: pass
    return pd.DataFrame()

# --- SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #FF4B4B;'>🏢 Renov'Analyst</h2>", unsafe_allow_html=True)
    
    # SECURITY PANEL
    st.markdown("---")
    pwd_input = st.text_input("🔑 Accès Partenaire", type="password", placeholder="Mot de passe...")
    if pwd_input == SECRET_PASSWORD:
        st.session_state.is_unlocked = True
        st.success("✅ Mode Premium Débloqué")
    elif pwd_input != "":
        st.error("❌ Mot de passe incorrect")
        st.session_state.is_unlocked = False

    st.markdown("---")
    st.markdown("### 🔍 1. Extraction")
    zipcode = st.text_input("Code Postal (ex: 75018)", "75018")
    fetch_limit = st.slider("Biens à scanner (Demo)", 10, 100, 50)
    
    if st.button("Lancer l'Analyse 🚀", use_container_width=True):
        with st.spinner("Analyse du secteur..."):
            df = fetch_live_ademe_data(zipcode, fetch_limit)
            if not df.empty:
                city_lat, city_lon = get_city_center(zipcode)
                st.session_state.city_coords = (city_lat, city_lon)
                
                my_bar = st.progress(0, text="Localisation GPS...")
                lats, lons = [], []
                for i, row in df.iterrows():
                    full_address = f"{row['Vraie_Adresse']} {zipcode}"
                    lat, lon = geocode_exact_address(full_address, city_lat, city_lon)
                    lats.append(lat)
                    lons.append(lon)
                    my_bar.progress((i + 1) / len(df), text="Localisation GPS...")
                
                my_bar.empty()
                df['Latitude'] = lats
                df['Longitude'] = lons
                df['Taille_Bulle'] = df['Coût Rénov. (€)'].apply(lambda x: x if x > 0 else 3000)
                st.session_state.raw_data = df
            else:
                st.error("Aucune donnée trouvée.")

    st.markdown("---")
    st.markdown("### ⚙️ 2. Filtres")
    min_surface = st.number_input("Surface Minimum (m²)", min_value=0, value=15)
    selected_dpes = st.multiselect("Filtrer par DPE", ['A', 'B', 'C', 'D', 'E', 'F', 'G'], default=['F', 'G'])

# --- MAIN DASHBOARD ---
st.title("Tableau de Bord d'Investissement")
st.markdown("Détection des passoires thermiques. **Mode :** " + ("🟢 Premium" if st.session_state.is_unlocked else "🟡 Démo Restreinte"))

if not st.session_state.raw_data.empty:
    
    df_filtered = st.session_state.raw_data.copy()
    df_filtered = df_filtered[df_filtered['Surface (m²)'] >= min_surface]
    if selected_dpes:
        df_filtered = df_filtered[df_filtered['DPE'].isin(selected_dpes)]

    # APPLY SECURITY MASKING IF LOCKED
    if not st.session_state.is_unlocked:
        df_filtered['Address'] = df_filtered['Vraie_Adresse'].apply(mask_address)
    else:
        df_filtered['Address'] = df_filtered['Vraie_Adresse']

    # Metrics
    critical_df = df_filtered[df_filtered['Status'] == "CRITICAL"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Biens Analysés", len(df_filtered))
    col2.metric("Passoires (Urgent)", len(critical_df))
    col3.metric("Marché Rénovation", f"€ {critical_df['Coût Rénov. (€)'].sum():,.0f}")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Map
    st.subheader("🗺️ Cartographie" + (" Exacte" if st.session_state.is_unlocked else " (Adresses Masquées)"))
    if not df_filtered.empty:
        color_map = {"CRITICAL": "#ff4b4b", "WARNING": "#ffa500", "OK": "#00cc66"}
        fig_map = px.scatter_mapbox(
            df_filtered, lat="Latitude", lon="Longitude", color="Status",
            size="Taille_Bulle", color_discrete_map=color_map, hover_name="Address",
            hover_data={"Latitude": False, "Longitude": False, "Taille_Bulle": False, "Vraie_Adresse": False, "DPE": True, "Surface (m²)": True, "Coût Rénov. (€)": True},
            zoom=14, center={"lat": st.session_state.city_coords[0], "lon": st.session_state.city_coords[1]},
            mapbox_style="carto-darkmatter", height=500
        )
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Data Table
    st.subheader("📑 Base de Données des Leads")
    
    col_table, col_btn = st.columns([4, 1])
    with col_table:
        display_cols = ['Address', 'Code Postal', 'DPE', 'Surface (m²)', 'Coût Rénov. (€)', 'Status']
        st.dataframe(df_filtered[display_cols], use_container_width=True, height=250)
        
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.session_state.is_unlocked:
            csv_data = df_filtered[display_cols].to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Exporter CSV", data=csv_data, file_name=f'Leads_{zipcode}.csv', mime='text/csv', type="primary", use_container_width=True)
        else:
            st.button("🔒 Export Bloqué", disabled=True, use_container_width=True)
            st.caption("Entrez le mot de passe pour débloquer.")

else:
    st.info("Veuillez entrer un Code Postal à gauche et lancer l'analyse.")