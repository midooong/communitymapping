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

# 폰트 설정 및 기타 초기화는 동일 (생략)

# 데이터 분석 페이지
if page == "📊 키오스크 데이터 분석":
    st.title("📊 함께 수집한 키오스크 데이터 분석")

    if not df.empty:
        st.subheader("📋 전체 데이터 요약")
        total_data_count = len(df)
        st.write(f"🗂️ 총 데이터 개수: **{total_data_count}개**")

        # 외국어 지원 데이터 정리
        st.subheader("🌐 외국어 지원 여부")
        if "foreign_language_support" in df.columns:
            def normalize_languages(value):
                languages = value.split(", ")
                return ", ".join(sorted(languages))  # 정렬하여 동일하게 처리

            df["foreign_language_support"] = df["foreign_language_support"].apply(normalize_languages)
        
        # 외국어 지원 통계 생성
        language_counts = df["foreign_language_support"].value_counts()

        # 파이 차트 생성
        fig, ax = plt.subplots()
        ax.pie(language_counts, labels=language_counts.index, autopct="%1.1f%%", startangle=90)
        ax.set_title("외국어 지원 여부 비율")
        st.pyplot(fig)

        # 외국어 지원 데이터 표
        language_summary = language_counts.reset_index()
        language_summary.columns = ["외국어 지원", "개수"]
        st.table(language_summary)

        # 기타 데이터 분석은 동일 (생략)
    else:
        st.info("📭 분석할 데이터가 없습니다.")
