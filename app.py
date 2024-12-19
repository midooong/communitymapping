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

# 폰트 파일 경로 설정
FONT_PATH = os.path.join(os.getcwd(), "NanumGothic.ttf")

# 폰트 파일 존재 확인
if not os.path.exists(FONT_PATH):
    st.error("⚠️ 폰트 파일을 찾을 수 없습니다. 경로를 확인하세요.")
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

# 데이터 로드 함수
@st.cache_data(ttl=60)
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.rename(columns={
            "Kiosk Max Height": "kiosk_max_height",
            "Place Name": "place_name",
            "Foreign Language Support": "foreign_language_support"
        }, inplace=True)
    return df

# 외국어 정렬 함수
def normalize_languages(value):
    if isinstance(value, str):
        languages = value.split(", ")
        return ", ".join(sorted(languages))
    return value

# 데이터 로드
df = load_data()

# 페이지 나누기
st.sidebar.title("😊 키오스크 커뮤니티 매핑")
page = st.sidebar.selectbox("📑 탭 선택", ["📝 키오스크 데이터 입력", "📊 키오스크 데이터 분석"])

if page == "📝 키오스크 데이터 입력":
    # 데이터 입력 페이지
    st.title("📝 키오스크 데이터 수집하기")

    # 이미지 불러오기
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

    # 데이터 입력 섹션
    name = st.text_input("학번+이름 (예: 10000 홍길동):")
    categories = ["음식점", "공공기관", "상점", "기타"]
    selected_category = st.selectbox("분류를 선택하세요:", categories)
    latitude = st.number_input("현재 위도(latitude):", value=37.4973, format="%.4f")
    longitude = st.number_input("현재 경도(longitude):", value=126.9092, format="%.4f")
    place_name = st.text_input("장소 이름:")
    kiosk_height = st.number_input("키오스크 최대 높이(cm):", min_value=0)
    language_options = ["영어", "일본어", "중국어", "스페인어", "기타"]
    selected_languages = st.multiselect("외국어 지원 여부를 선택하세요:", language_options)

    if st.button("🚀 제출"):
        if selected_category and name and place_name and latitude and longitude:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            foreign_language_support = normalize_languages(", ".join(selected_languages)) if selected_languages else "없음"
            sheet.append_row([timestamp, selected_category, latitude, longitude, place_name, kiosk_height, foreign_language_support, name])
            st.success("🎉 데이터가 성공적으로 저장되었습니다!")
            st.experimental_rerun()  # 페이지 새로고침
        else:
            st.error("⚠️ 모든 필드를 입력해주세요.")

    st.header("🗺️ 함께 만든 키오스크 지도")
    if not df.empty:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
        df = df.dropna(subset=['latitude', 'longitude'])

        m = folium.Map(location=[37.4973, 126.9100], zoom_start=17)
        category_colors = {
            "음식점": "red",
            "공공기관": "blue",
            "상점": "orange",
            "기타": "green"
        }
        for _, row in df.iterrows():
            category = row.get("category", "기타")
            color = category_colors.get(category, "gray")
            popup_html = f"""
            <b>분류:</b> {category}<br>
            <b>장소:</b> {row['place_name']}<br>
            <b>최대 높이:</b> {row['kiosk_max_height']}cm<br>
            <b>외국어 지원:</b> {row['foreign_language_support']}<br>
            <b>기록자:</b> {row['name']}
            """
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color=color)
            ).add_to(m)
        st_folium(m, width=700, height=500)

elif page == "📊 키오스크 데이터 분석":
    # 데이터 분석 페이지
    st.title("📊 함께 수집한 키오스크 데이터 분석")
    st.markdown("""
    **이 페이지에서는 수집된 키오스크 데이터를 분석할 수 있습니다.**  
    아래에서 수집된 데이터 요약 통계를 확인하세요.
    """)

    if not df.empty:
        df["foreign_language_support"] = df["foreign_language_support"].apply(normalize_languages)

        st.subheader("📋 전체 데이터 요약")
        total_data_count = len(df)
        st.write(f"🗂️ 총 데이터 개수: **{total_data_count}개**")

        # 키오스크 최대 높이 분포
        st.subheader("📏 키오스크 최대 높이 분포")
        df["kiosk_max_height"] = pd.to_numeric(df["kiosk_max_height"], errors="coerce")
        heights = df["kiosk_max_height"].dropna()
        bins = np.arange(120, 210, 10)

        fig, ax = plt.subplots()
        counts, edges, patches = ax.hist(heights, bins=bins, color="skyblue", edgecolor="black")
        ax.set_title("키오스크 최대 높이 분포 (10cm 단위)")
        ax.set_xlabel("키오스크 높이 (cm)")
        ax.set_ylabel("빈도수")
        ax.set_xticks(bins)
        st.pyplot(fig)

        height_summary = pd.DataFrame({
            "범위 (cm)": [f"{int(bins[i])} - {int(bins[i+1])}" for i in range(len(bins) - 1)],
            "키오스크 수": counts.astype(int)
        })
        st.table(height_summary)

        # 분류별 키오스크 수
        st.subheader("📂 분류별 키오스크 수")
        category_counts = df["category"].value_counts()
        fig, ax = plt.subplots()
        category_counts.plot(kind="bar", color=["red", "blue", "yellow", "green"], ax=ax)
        ax.set_title("분류별 키오스크 수")
        ax.set_xlabel("분류")
        ax.set_ylabel("키오스크 수")
        st.pyplot(fig)
        st.table(category_counts.reset_index().rename(columns={"index": "분류", "category": "개수"}))

        # 외국어 지원 여부
        st.subheader("🌐 외국어 지원 여부")
        language_counts = df["foreign_language_support"].value_counts()
        fig, ax = plt.subplots()
        ax.pie(language_counts, labels=language_counts.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("외국어 지원 여부 비율")
        st.pyplot(fig)
        st.table(language_counts.reset_index().rename(columns={"index": "외국어 지원", "foreign_language_support": "개수"}))

        # CSV 다운로드 버튼 추가
        st.subheader("📥 데이터 다운로드")
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="CSV 다운로드",
            data=csv,
            file_name="kiosk_data.csv",
            mime="text/csv"
        )
    else:
        st.info("📭 분석할 데이터가 없습니다.")
