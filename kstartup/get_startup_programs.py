import os
from dotenv import load_dotenv
import re
import requests
from datetime import datetime

# 0. 세팅
load_dotenv()
SERVICE_KEY = os.getenv("SERVICE_KEY") # 공공데이터포털 서비스 키 (디코딩된 버전으로 사용)

# API URL 설정
BASE_URL = "http://apis.data.go.kr/B552735/kisedKstartupService01/getAnnouncementInformation01"
SPRING_ENDPOINT = "http://localhost:8080/api/admin/startup-supports/batch" # 메인 서버 엔트포이트

all_items = []


# 1. 수집
# 페이지 반복 수집
for page in range(1, 10): # 페이지 범위 설정
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
        filtered_items = [item for item in items if item.get("sprv_inst") != "민간"]
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
# - 날짜: YYYY.MM.DD
def _date_yyyymmdd_to_dot(d: str | None) -> str | None:
    if not d:
        return None
    d = d.strip()
    if not re.fullmatch(r"\d{8}", d):
        return None
    return datetime.strptime(d, "%Y%m%d").strftime("%Y.%m.%d")

def _pick_contact(item: dict) -> str | None:
    # rprsnt_telno(대표전화) → prch_cnpl_no(담당부서 전화) 우선
    return (item.get("rprsnt_telno") or item.get("prch_cnpl_no"))

def _build_agency(item: dict) -> str | None:
    org = item.get("pbanc_ntrp_nm")          # 주관기관
    dept = item.get("biz_prch_dprt_nm")      # 담당부서
    if org and dept:
        return f"{org} / {dept}"
    return org or dept

def _build_apply_method(item: dict) -> str | None:
    parts = []
    if item.get("aply_mthd_onli_rcpt_istc"):
        parts.append(f"온라인: {item['aply_mthd_onli_rcpt_istc']}")
    if item.get("biz_aply_url"):
        parts.append(f"신청URL: {item['biz_aply_url']}")
    if item.get("aply_mthd_eml_rcpt_istc"):
        parts.append(f"이메일: {item['aply_mthd_eml_rcpt_istc']}")
    if item.get("aply_mthd_vst_rcpt_istc"):
        parts.append("방문 접수")
    if item.get("aply_mthd_pssr_rcpt_istc"):
        parts.append("우편 접수")
    if item.get("aply_mthd_fax_rcpt_istc"):
        parts.append("팩스 접수")
    if item.get("aply_mthd_etc_istc"):
        parts.append(f"기타: {item['aply_mthd_etc_istc']}")
    return " | ".join(parts) if parts else None

def _clean(s: str | None) -> str | None:
    if not s:
        return None
    return re.sub(r"\s+", " ", str(s)).strip()

def to_create_startup_response(item: dict) -> dict:
    return {
        "title": _clean(item.get("biz_pbanc_nm")),
        "supportArea": _clean(item.get("supt_biz_clsfc")),
        "region": _clean(item.get("supt_regin")),  # 서버에서 Region 매핑 예정(Mapper 사용)
        "businessDuration": _clean(item.get("biz_enyy")),  # 서버에서 BusinessDuration 매핑 예정(Mapper 사용)
        "agency": _clean(_build_agency(item)),
        "targetAge": _clean(item.get("biz_trgt_age")),
        "target": _clean(item.get("aply_trgt_ctnt")),
        "contact": _clean(_pick_contact(item)),
        "link": _clean(item.get("detl_pg_url")),
        "startDate": _date_yyyymmdd_to_dot(item.get("pbanc_rcpt_bgng_dt")),
        "endDate": _date_yyyymmdd_to_dot(item.get("pbanc_rcpt_end_dt")),
        "applyMethod": _clean(_build_apply_method(item)),
        "supportDetails": _clean(item.get("pbanc_ctnt")),
        "requiredDocuments": _clean(item.get("prfn_matr")), # 추가 API 필요
        "evaluationMethod": None,  # 추가 API 필요
    }

# 변환 실행
payload = [to_create_startup_response(it) for it in all_items ]

print(f"\n[INFO] 전송 대상 건수(민간 제외): {len(payload)}")
for i, row in enumerate(payload[:3], 1):
    print(f"\n[DTO 샘플 {i}]")
    for k, v in row.items():
        print(f" - {k}: {v}")

# 전송
try:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    resp = requests.post(SPRING_ENDPOINT, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    print("\n[SUCCESS] Spring 응답 코드:", resp.status_code)
    print(resp.text[:800])
except Exception as e:
    print("\n[ERROR] Spring 전송 실패:", e)
