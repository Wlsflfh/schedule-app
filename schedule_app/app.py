import streamlit as st
import pandas as pd
import re
import os
from datetime import date
from collections import defaultdict

DATA_FILE = "schedule.xlsx"
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD","heritageclub_75")

st.set_page_config(page_title="근무 스케줄", layout="centered")
st.title("☕️ HERITAGE CLUB 근무 스케줄 조회")

tab_staff, tab_admin = st.tabs(["👥 직원", "👑 관리자"])

##################################
# 관리자
##################################

with tab_admin:

    st.header("👑 관리자")

    pw = st.text_input("관리자 비밀번호", type="password")

    if pw == ADMIN_PASSWORD:
        st.success("관리자 로그인 완료")

        if os.path.exists(DATA_FILE):
            st.info(f"현재 업로드된 파일: {DATA_FILE}")

        uploaded = st.file_uploader("근무 엑셀 업로드 / 교체", type=["xlsx"])

        if uploaded:
            with open(DATA_FILE,"wb") as f:
                f.write(uploaded.getbuffer())

            st.success("저장 완료! 직원들이 바로 조회 가능합니다.")
            st.rerun()

    elif pw:
        st.error("비밀번호가 틀렸습니다")

##################################
# 직원 (기존 코드 그대로)
##################################

with tab_staff:

    if not os.path.exists(DATA_FILE):
        st.info("아직 근무 시간표가 나오지 않았습니다.")
        st.stop()

    uploaded_file = DATA_FILE

    # =========================
    # ↓↓↓ 여기부터 네 코드 그대로 ↓↓↓
    # =========================

    df = pd.read_excel(uploaded_file, header=None)

    header = str(df.iloc[0,0])
    m = re.search(r'(\d{1,2})\s*월?', header)

    if not m:
        st.error("월 정보를 찾지 못했습니다")
        st.stop()

    month = int(m.group(1))
    year = date.today().year

    def month_date(month):
        return date(year, month, 1)

    base_date = month_date(month)

    schedule = defaultdict(list)
    pattern = re.compile(r"([가-힣]+)\s*(\d+)\s*-\s*(마감|\d+)")

    active_dates = {}

    for row in range(len(df)):
        for col in df.columns:
            v = str(df[col][row]).strip()
            if v.isdigit():
                active_dates[col] = base_date.replace(day=int(v))

        for col in df.columns:
            cell = str(df[col][row])
            m = pattern.search(cell)

            if m and col in active_dates:
                name = m.group(1)
                start = int(m.group(2))
                end = m.group(3)

                if end == "마감":
                    end = 11
                else:
                    end = int(end)

                schedule[active_dates[col]].append({
                    "name": name,
                    "start": start,
                    "end": end
                })

    names = sorted({item["name"] for v in schedule.values() for item in v})

    target = st.selectbox("이름 선택", names)

    if target:
        st.subheader(f"{base_date.strftime('%b')}. {target}의 근무")

        total = 0
        found = False

        for d in sorted(schedule.keys()):
            for item in schedule[d]:
                if item["name"] == target:
                    start = int(item["start"])
                    end = int(item["end"])

                    hours = end - start
                    if hours < 0:
                        hours += 12

                    st.write(f"{d.month}.{d.day} {d.strftime('%a')}  {start}-{end}  ({hours}h)")
                    total += hours
                    found = True

        if found:
            st.success(f"총 근무시간: {total}h")
        else:
            st.warning("존재하지 않는 이름입니다.")
