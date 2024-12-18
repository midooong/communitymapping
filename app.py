import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from streamlit_folium import st_folium
import folium
from datetime import datetime
import toml
from PIL import Image
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.ticker import MaxNLocator

# 폰트 파일 경로 설정
FONT_PATH = os.path.join(os.getcwd(), "NanumGothic.ttf")
if not os.path.exists(FONT_PATH):
    st.error("폰트 파일을 찾을 수 없습니다.")
else:
    fm.fontManager.addfont(FONT_PATH)
    plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False

# .toml 파일 읽기
config = toml.load("secrets.toml")
SERVICE_ACCOUNT_INFO = {
    "type": config["connections.gsheets"]["type"],
    "project_id": config["connections.gsheets"]["project_id"],
    "private_key_id": config["connections.gsheets"]["private_key_id"],
    "private_key": config["connections.gsheets"]["private_key"].replace("\\n", "\n"),
    "client_email": config["connections.gsheets"]["client_email"],
    "client_id": config["connections.gsheets"]["client_id"],
    "auth_uri": config["connections.gsheets"]["auth_uri"],
    "token_uri": config["connections.gsheets"]["token_uri"],
    "auth_provider_x509_cert_url": config["connections.gsheets"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": config["connections.gsheets"]["client_x509_cert_url"],
}

# Google Sheets API 인증
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPE)
gc = gspread.authorize(credentials)

# Google Sheets 연결
SPREADSHEET_URL = config["connections.gsheets"]["spreadsheet"]
sheet = gc.open_by_url(SPREADSHEET_URL).sheet1

# 데이터 읽기
data = sheet.get_all_records()
df = pd.DataFrame(data)

# 열 이름 변환
if not df.empty:
    df.rename(columns={
        "Kiosk Max Height": "kiosk_max_height",
        "Place Name": "place_name",
        "Foreign Language Support": "foreign_language_support"
    }, inplace=True)

# 메인 페이지
st.title("🗺️ 키오스크 커뮤니티 매핑 프로젝트")

# 이미지 및 프로젝트 설명
image = Image.open("kiosk.jpg")
resized_image = image.resize((500, 400))
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(resized_image, use_container_width=False)

with st.expander("📖 커뮤니티 매핑 프로젝트란?"):
    st.markdown("""
    ### 커뮤니티 매핑이란?
    커뮤니티 매핑(Community Mapping)은 집단지성을 기반으로 참여형 지도를 제작하는 것입니다.  
    이 프로젝트에서는 키오스크에 대한 정보를 수집하여 문제점을 분석합니다.
    """)

# 지도 표시
st.header("🗺️ 키오스크 지도")
if not df.empty:
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df = df.dropna(subset=['latitude', 'longitude'])

    m = folium.Map(location=[37.4973, 126.9100], zoom_start=17)
    category_colors = {"🍔 음식점": "red", "🏛️ 공공기관": "blue", "🛍️ 상점": "green", "✨ 기타": "purple"}
    for _, row in df.iterrows():
        popup_html = f"""
        <b>분류:</b> {row['category']}<br>
        <b>장소:</b> {row['place_name']}<br>
        <b>최대 높이:</b> {row['kiosk_max_height']}cm<br>
        <b>외국어 지원:</b> {row['foreign_language_support']}<br>
        <b>기록자:</b> {row['name']}
        """
        folium.Marker(
            location=[row['latitude'], row['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            icon=folium.Icon(color=category_colors.get(row['category'], "gray"))
        ).add_to(m)
    st_folium(m, width=700, height=500)
else:
    st.info("📭 등록된 키오스크 정보가 없습니다.")

# 데이터 입력
st.header("📝 데이터 입력")
name = st.text_input("✍️ 학번+이름 (예: 10000 홍길동):")
categories = ["🍔 음식점", "🏛️ 공공기관", "🛍️ 상점", "✨ 기타"]
selected_category = st.selectbox("🏷️ 분류를 선택하세요:", categories)
latitude = st.number_input("📍 현재 위도(latitude):", value=37.4973, format="%.4f")
longitude = st.number_input("📍 현재 경도(longitude):", value=126.9092, format="%.4f")
place_name = st.text_input("🏢 장소 이름:")
kiosk_height = st.number_input("📏 키오스크 최대 높이(cm):", min_value=0)
language_options = ["🇬🇧 영어", "🇯🇵 일본어", "🇨🇳 중국어", "🇪🇸 스페인어", "🌐 기타"]
selected_languages = st.multiselect("💬 외국어 지원 여부를 선택하세요:", language_options)

if st.button("🚀 제출하기"):
    if selected_category and name and place_name and latitude and longitude:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        foreign_language_support = ", ".join(selected_languages) if selected_languages else "없음"
        sheet.append_row([timestamp, selected_category, latitude, longitude, place_name, kiosk_height, foreign_language_support, name])
        st.success("🎉 데이터가 성공적으로 저장되었습니다!")
    else:
        st.error("⚠️ 모든 필드를 입력해주세요.")
