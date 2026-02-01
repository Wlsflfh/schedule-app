import streamlit as st
import pandas as pd
import re
import os
from datetime import date
from collections import defaultdict

IMAGE_FILE = "schedule_preview.png"
CURRENT_FILE = "current_name.xlsx"
DATA_FILE = "schedule.xlsx"
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD","heritageclub_75")

st.set_page_config(page_title="근무 스케줄", layout="centered")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
st.image(os.path.join(BASE_DIR, "HERITAGE_CLUB.jpg"), use_column_width=True)
st.title("☕️ HERITAGE CLUB 근무 스케줄")

tab_staff, tab_admin = st.tabs(["👥 직원", "👑 관리자"])

##################################
# 관리자 모드
##################################

with tab_admin:
    with st.expander("📌 관리자 유의사항"):
        st.markdown("""
        1. numbers 로 작성한 근무 스케줄 표를 예쁘게 캡쳐한다. 
        2. 근무 스케줄 numbers 파일을 .xslx 확장자로 추출한다. (파일 -> 다음으로 내보내기 -> Excel 선택)
        3. 엑셀 파일과 이미지를 입력 후 저장 버튼을 누른다.
        - 이미지와 엑셀 파일은 항상 동일하게 유지되어야 직원이 헷갈리지 않음 
        - A1 셀에는 꼭 ‘n월’ 키워드가 포함되어야함 -> (e.g. 헤리티지 2월 🍰)
        - 날짜셀에는 오로지 숫자만 포함되어야함 -> (e.g. 16(설날) → [ERROR])
        - 정확히 해당 월의 근무만 표시해야함 -> (e.g. 2월 스케줄의 마지막 칸에 3월 1일 시간표는 표시 X)
        """)

    # 로그인 상태 저장
    if "admin" not in st.session_state:
        st.session_state.admin = False

    st.markdown("### 👑 관리자")
    pw = st.text_input("관리자 비밀번호", type="password")

    # 로그인 성공 시 상태 고정
    if pw == ADMIN_PASSWORD:
        st.session_state.admin = True

    # 로그인 전
    if not st.session_state.admin:
        if os.path.exists(CURRENT_FILE):
            real_name = open(CURRENT_FILE).read()
            st.info(f"현재 업로드된 파일: {real_name}")
        else:
            st.info("업로드된 파일이 없습니다.")

        if pw:
            st.error("비밀번호가 틀렸습니다")

    # 로그인 후
    if st.session_state.admin:
        st.success("관리자 로그인 완료")

        st.markdown("#### 📄 근무 스케줄 엑셀 업로드 / 교체")
        uploaded = st.file_uploader("xlsx", type=["xlsx"])
            
        if os.path.exists(DATA_FILE) and os.path.exists(CURRENT_FILE):
            if st.button("🗑️ 현재 파일 삭제"):
                os.remove(DATA_FILE)
                os.remove(CURRENT_FILE)
                st.warning("근무 파일이 삭제되었습니다.")
                st.rerun()
            
        st.divider()
        st.markdown("#### 🗓️ 근무 스케줄 이미지 업로드 / 교체")

        img = st.file_uploader("PNG / JPG", type=["png","jpg","jpeg"], key="img")

        if os.path.exists(IMAGE_FILE):
            if st.button("🗑️ 현재 이미지 삭제"):
                os.remove(IMAGE_FILE)
                st.warning("스케줄 이미지가 삭제되었습니다.")
                st.rerun()

        col1, col2, col3 = st.columns([2,3,2])

        with col2:
            save = st.button("💾 저장", use_container_width=True)

        if save:
            if not uploaded and not img:
                st.warning("업로드할 파일이나 이미지를 선택하세요.")
                st.stop()

            if uploaded:
                with open(DATA_FILE,"wb") as f:
                    f.write(uploaded.getbuffer())

                with open(CURRENT_FILE,"w") as f:
                    f.write(uploaded.name)

            if img:
                with open(IMAGE_FILE,"wb") as f:
                    f.write(img.getbuffer())

            st.success("저장 완료! 직원들이 바로 조회 가능합니다.")
            st.rerun()

##################################
# 직원 모드
##################################

with tab_staff:
    st.markdown("### 🗓️ 이번 달 근무 스케줄")

    if not os.path.exists(DATA_FILE):
        st.info("아직 근무 시간표가 나오지 않았습니다.")
        st.stop()
        
    if os.path.exists(IMAGE_FILE):
        st.image(IMAGE_FILE, use_column_width=True)
    
    col1, col2 = st.columns(2)

    with col1:
        if os.path.exists(IMAGE_FILE):
            with open(IMAGE_FILE, "rb") as f:
                st.download_button(
                    "🎞️ 이미지 저장",
                    f,
                    file_name="schedule.png",
                    mime="image/png",
                    use_container_width=True
                )

    with col2:
        with open(DATA_FILE, "rb") as f:
            st.download_button(
                label="📥 엑셀 파일 저장",
                data=f,
                file_name=real_name if 'real_name' in globals() else DATA_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
    uploaded_file = DATA_FILE

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
        st.subheader(f"{base_date.month}월 {target}의 근무")

        total = 0
        found = False
        lines = []

        for d in sorted(schedule.keys()):
            for item in schedule[d]:
                if item["name"] == target:
                    start = int(item["start"])
                    end = int(item["end"])

                    hours = end - start
                    if hours < 0:
                        hours += 12

                    lines.append(f"{d.month}.{d.day} {d.strftime('%a')}  {start}-{end}  ({hours}h)")
                    total += hours
                    found = True

        st.text("\n".join(lines))

        if found:
            st.markdown(f"#### Total hours: {total}h")
        else:
            st.warning("존재하지 않는 이름입니다.")
