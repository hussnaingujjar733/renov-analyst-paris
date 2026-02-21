## 📌 Project Overview
**Renov'Analyst PRO** is an end-to-end Real Estate SaaS platform that transforms raw government data into actionable business intelligence. Built to solve the ongoing energy-crisis challenge in the French real estate market, this tool identifies properties affected by the new DPE (Diagnostic de Performance Énergétique) regulations.

It uses a real-time data pipeline integrating French Government APIs (ADEME, Geo API) to extract, geocode, and evaluate energy-inefficient properties (DPE F & G) across Paris and the Île-de-France region. 

## ✨ Key Features
* **📡 Real-Time Data Extraction:** Connects directly to the live ADEME database to fetch the latest property energy audits.
* **🌍 Geospatial Mapping:** Converts raw addresses into GPS coordinates using the official French Geo API and visualizes them on an interactive 3D map (Plotly Mapbox).
* **💶 Automated Cost Estimation:** Uses custom business logic to calculate estimated renovation costs based on surface area and DPE ratings.
* **🔐 Vault Security System:** Features a "Demo Mode" with a password-protected gateway. Addresses and CSV export functionalities are masked until unlocked by an authorized user (Agency Client).

## 🛠️ Tech Stack
* **Language:** Python
* **Frontend & Framework:** Streamlit
* **Data Manipulation:** Pandas
* **Data Visualization:** Plotly Express
* **API Requests & Parsing:** Requests, JSON
