import requests
import pandas as pd
import os
from dotenv import load_dotenv
from datetime import datetime

# 공공데이터포털 서비스 키 (디코딩된 버전으로 사용)
load_dotenv()
SERVICE_KEY = os.getenv("SERVICE_KEY")

# API URL 설정
BASE_URL = "http://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01"
all_items = []

# 1. 수집
# 페이지 반복 수집
for page in range(1, 6): # 우선 임시로 1~5페이지로 설정
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": page,
        "numOfRows": 20,
        "returnType": "json"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("data", [])
        # "민간" 주관기관은 제외
        filtered_items = [item for item in items if item.get("jrsd_inst_nm") != "민간"]
        all_items.extend(filtered_items)
    except Exception as e:
        print(f"[ERROR] {page}페이지 요청 실패: {e}")
        continue

# 2. 미리 벡터화 해두기
# # df 생성
# df = pd.DataFrame([{
#     "id": item.get("pbanc_id"),
#     "지원분야": item.get("biz_stle_nm"),
#     "제목": item.get("biz_pbanc_nm"),
#     "모집시작일": item.get('pbanc_rcpt_bgng_dt'),
#     "모집종료일" : item.get('pbanc_rcpt_end_dt'),
#     "지역": item.get("rgn_nm"),
#     "창업업력": item.get("entrprs_age_se_nm"),
#     "주관기관": item.get("jrsd_inst_nm"),
#     "대상": item.get("aply_trgt_ctnt"),
#     "연락처": item.get("rprsnt_telno"),
#     "본문 링크": item.get("detl_pg_url"),
#     "핵심본문내용": item.get("pbanc_cn")
# } for item in all_items])

# 3. SpringBoot에 응답 주기
