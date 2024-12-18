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

# 페이지 나누기
st.sidebar.title("키오스크 커뮤니티 매핑")
page = st.sidebar.selectbox("탭 선택", ["키오스크 데이터 입력", "키오스크 데이터 분석"])

if page == "키오스크 데이터 입력":
    st.title("키오스크 데이터 수집하기")
    image = Image.open("kiosk.jpg")
    st.image(image.resize((500, 400)))

    name = st.text_input("학번+이름 (예: 10000 홍길동):")
    categories = ["음식점", "공공기관", "상점", "기타"]
    selected_category = st.selectbox("분류를 선택하세요:", categories)
    latitude = st.number_input("현재 위도(latitude):", value=37.4973, format="%.4f")
    longitude = st.number_input("현재 경도(longitude):", value=126.9092, format="%.4f")
    place_name = st.text_input("장소 이름:")
    kiosk_height = st.number_input("키오스크 최대 높이(cm):", min_value=0)
    language_options = ["영어", "일본어", "중국어", "스페인어", "기타"]
    selected_languages = st.multiselect("외국어 지원 여부를 선택하세요:", language_options)

    if st.button("제출"):
        if selected_category and name and place_name and latitude and longitude:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            foreign_language_support = ", ".join(selected_languages) if selected_languages else "없음"
            sheet.append_row([timestamp, selected_category, latitude, longitude, place_name, kiosk_height, foreign_language_support, name])
            st.success("데이터가 성공적으로 저장되었습니다!")
        else:
            st.error("모든 필드를 입력해주세요.")

elif page == "키오스크 데이터 분석":
    st.title("키오스크 데이터 분석")
    if not df.empty:
        df["kiosk_max_height"] = pd.to_numeric(df["kiosk_max_height"], errors="coerce")
        heights = df["kiosk_max_height"].dropna()
        bins = np.arange(120, 210, 10)

        # 키오스크 최대 높이 분포
        with st.expander("📊 키오스크 최대 높이 분포"):
            st.subheader("키오스크 최대 높이 분포")
            fig, ax = plt.subplots()
            counts, edges, patches = ax.hist(heights, bins=bins, color="skyblue", edgecolor="black")
            ax.set_title("키오스크 최대 높이 분포")
            ax.set_xlabel("높이 (cm)")
            ax.set_ylabel("빈도수")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            st.pyplot(fig)

            # 통계 데이터 생성
            height_summary = pd.DataFrame({
                "범위 (cm)": [f"{int(bins[i])} - {int(bins[i+1])}" for i in range(len(bins) - 1)],
                "키오스크 수": counts.astype(int)
            })
            st.table(height_summary)

        # 분류별 키오스크 수
        with st.expander("📊 분류별 키오스크 수"):
            st.subheader("분류별 키오스크 수")
            category_counts = df["category"].value_counts()
            fig, ax = plt.subplots()
            category_counts.plot(kind="bar", color=["red", "blue", "yellow", "green"], ax=ax)
            ax.set_title("분류별 키오스크 수")
            ax.set_xlabel("분류")
            ax.set_ylabel("키오스크 수")
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            st.pyplot(fig)
            st.table(category_counts.reset_index().rename(columns={"index": "분류", "category": "개수"}))

        # 외국어 지원 여부
        with st.expander("📊 외국어 지원 여부"):
            st.subheader("외국어 지원 여부")
            language_counts = df["foreign_language_support"].value_counts()
            fig, ax = plt.subplots()
            ax.pie(language_counts, labels=language_counts.index, autopct="%1.1f%%", startangle=90)
            ax.set_title("외국어 지원 여부 비율")
            st.pyplot(fig)
            st.table(language_counts.reset_index().rename(columns={"index": "외국어 지원", "foreign_language_support": "개수"}))
    else:
        st.info("분석할 데이터가 없습니다.")
