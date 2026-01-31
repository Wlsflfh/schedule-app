import streamlit as st
import pandas as pd
import re
from datetime import date
from collections import defaultdict

st.set_page_config(page_title="근무 스케줄", layout="centered")
st.title("📅 근무 스케줄 조회")

uploaded_file = st.file_uploader("엑셀 파일 업로드 (HERITAGE_FEB.xlsx)", type=["xlsx"])

if uploaded_file:

    # 1. Load excel
    df = pd.read_excel(uploaded_file, header=None)

    # 2-1. Extract month
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

    # 2-2. Extract schedule
    schedule = defaultdict(list)
    pattern = re.compile(r"([가-힣]+)\s*(\d+)\s*-\s*(마감|\d+)")

    active_dates = {}

    for row in range(len(df)):
        # 날짜 감지
        for col in df.columns:
            v = str(df[col][row]).strip()
            if v.isdigit():
                active_dates[col] = base_date.replace(day=int(v))

        # 근무 파싱
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

    # 이름 목록 자동 생성
    names = sorted({item["name"] for v in schedule.values() for item in v})

    st.divider()

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
