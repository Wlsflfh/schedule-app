import streamlit as st
import pandas as pd
import re
import os
from datetime import date
from collections import defaultdict

DATA_FILE = "schedule.xlsx"

ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD","heritageclub_75")

st.set_page_config(page_title="근무 스케줄", layout="centered")

mode = st.sidebar.radio("모드 선택", ["직원", "관리자"])

####################################
# 관리자
####################################

if mode == "관리자":

    pw = st.text_input("관리자 비밀번호", type="password")

    if pw != ADMIN_PASSWORD:
        st.warning("비밀번호 입력")
        st.stop()

    st.success("관리자 로그인 완료")

    uploaded = st.file_uploader("근무 엑셀 업로드", type=["xlsx"])

    if uploaded:
        with open(DATA_FILE,"wb") as f:
            f.write(uploaded.getbuffer())

        st.success("저장 완료!")

####################################
# 직원
####################################

else:

    st.title("[HERITAGE CLUB] 근무 스케줄 조회")

    if not os.path.exists(DATA_FILE):
        st.info("아직 근무 시간표가 나오지 않았습니다.")
        st.stop()

    df = pd.read_excel(DATA_FILE, header=None)

    header = str(df.iloc[0,0])
    m = re.search(r'(\d{1,2})\s*월?', header)

    month = int(m.group(1))
    year = date.today().year

    base_date = date(year, month, 1)

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
                    end = 23
                else:
                    end = int(end)

                schedule[active_dates[col]].append({
                    "name": name,
                    "start": start,
                    "end": end
                })

    names = sorted({i["name"] for v in schedule.values() for i in v})

    target = st.selectbox("Select name", names)

    total = 0

    for d in sorted(schedule.keys()):
        for item in schedule[d]:
            if item["name"] == target:
                hours = item["end"] - item["start"]
                if hours < 0:
                    hours += 12

                st.write(f"{d.month}.{d.day} {item['start']}-{item['end']} ({hours}h)")
                total += hours

    st.success(f"Total hours: {total}h")
