import requests
import pandas as pd
from dotenv import load_dotenv
import os

# 공공데이터포털 서비스 키 (디코딩된 버전으로 사용)
load_dotenv()
SERVICE_KEY = os.getenv("SERVICE_KEY")

# HTTP
BASE_URL = "http://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01"

# 세팅
params = {
    "serviceKey": SERVICE_KEY,
    "pageNo": 2,
    "numOfRows": 20,
    "returnType": "json"
}

try:
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    data = response.json()
    items = data.get("data", [])
except Exception as e:
    print(f"요청 실패: {e}")

# 데이터 파싱
items = data.get("data", [])
df = pd.DataFrame([{
    "공고명": item.get("biz_pbanc_nm"),
    "모집기간": f"{item.get('pbanc_rcpt_bgng_dt')} ~ {item.get('pbanc_rcpt_end_dt')}",
    "대상": item.get("aply_trgt_ctnt"),
    "링크": item.get("detl_pg_url")
} for item in items])

# 터미널 출력
print(df)