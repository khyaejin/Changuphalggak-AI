import base64
import os
import re
import asyncio
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
import httpx
from dotenv import load_dotenv
from api.dto.startup_dto import CreateStartupResponseDTO

load_dotenv()
SERVICE_KEY = os.getenv("SERVICE_KEY")
BASE_URL = os.getenv("BASE_URL")

# ---------- 유틸 ----------

def _date_yyyymmdd_to_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    d = d.strip()
    if not re.fullmatch(r"\d{8}", d):
        return None
    return datetime.strptime(d, "%Y%m%d").date()

def _pick_contact(item: Dict[str, Any]) -> Optional[str]:
    return item.get("rprsnt_telno") or item.get("prch_cnpl_no")

def _build_agency(item: Dict[str, Any]) -> Optional[str]:
    org = item.get("pbanc_ntrp_nm")
    dept = item.get("biz_prch_dprt_nm")
    if org and dept:
        return f"{org} / {dept}"
    return org or dept

def _decode_base64_if_needed(value: str) -> str:
    try:
        # Base64인지 확인 후 디코딩
        decoded = base64.b64decode(value).decode("utf-8")
        return decoded
    except Exception:
        # 디코딩 실패하면 원본 반환
        return value

def _build_apply_method(item: Dict[str, Any]) -> Optional[str]:
    parts = []
    if item.get("aply_mthd_onli_rcpt_istc"):
        parts.append(f"온라인: {item['aply_mthd_onli_rcpt_istc']}")
    if item.get("biz_aply_url"):
        parts.append(f"신청URL: {item['biz_aply_url']}")
    if item.get("aply_mthd_eml_rcpt_istc"):
        email_value = _decode_base64_if_needed(item["aply_mthd_eml_rcpt_istc"])
        parts.append(f"이메일: {email_value}")
    if item.get("aply_mthd_vst_rcpt_istc"):
        parts.append("방문 접수")
    if item.get("aply_mthd_pssr_rcpt_istc"):
        parts.append("우편 접수")
    if item.get("aply_mthd_fax_rcpt_istc"):
        parts.append("팩스 접수")
    if item.get("aply_mthd_etc_istc"):
        parts.append(f"기타: {item['aply_mthd_etc_istc']}")
    return " | ".join(parts) if parts else None

def _clean(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    return re.sub(r"\s+", " ", str(s)).strip()

# dto 변환
def to_create_startup_response(item: Dict[str, Any]) -> CreateStartupResponseDTO:
    body = item.get("pbanc_ctnt")
    return CreateStartupResponseDTO(
        # 기본 필드
        title=_clean(item.get("biz_pbanc_nm")),
        support_area=_clean(item.get("supt_biz_clsfc")),
        region=_clean(item.get("supt_regin")),
        business_duration=_clean(item.get("biz_enyy")),
        agency=_clean(_build_agency(item)),
        target_age=_normalize_target_age(_clean(item.get("biz_trgt_age"))),
        target=_clean(item.get("aply_trgt_ctnt")),
        contact=_clean(_pick_contact(item)),
        link=_clean(item.get("detl_pg_url")),
        start_date=_date_yyyymmdd_to_date(item.get("pbanc_rcpt_bgng_dt")),
        end_date=_date_yyyymmdd_to_date(item.get("pbanc_rcpt_end_dt")),
        apply_method=_clean(_build_apply_method(item)),
        support_details=_clean(item.get("pbanc_ctnt")),

        # 추가 필드
        external_ref=str(item.get("pbanc_sn")) if item.get("pbanc_sn") is not None else None,
        guidance_url=_clean(item.get("biz_gdnc_url")),
        is_recruiting=True if item.get("rcrt_prgs_yn") == "Y" else False,
    )

# 연령 축약
def _normalize_target_age(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    # 토큰 분리
    tokens = [t.strip() for t in value.split(",") if t.strip()]
    # 모든 연령 범위 패턴 파싱
    age_ranges = []
    for t in tokens:
        # '만 XX세 미만'
        m = re.match(r"만\s*(\d+)\s*세\s*미만", t)
        if m:
            age_ranges.append((0, int(m.group(1)) - 1))
            continue
        # '만 XX세 이상 ~ 만 YY세 이하'
        m = re.match(r"만\s*(\d+)\s*세\s*이상\s*~\s*만\s*(\d+)\s*세\s*이하", t)
        if m:
            age_ranges.append((int(m.group(1)), int(m.group(2))))
            continue
        # '만 XX세 이상'
        m = re.match(r"만\s*(\d+)\s*세\s*이상", t)
        if m:
            age_ranges.append((int(m.group(1)), 200))  # 200세는 사실상 무제한 상한
            continue
    # 범위가 없으면 원본 반환
    if not age_ranges:
        return value
    # 범위 병합
    age_ranges.sort()
    merged = [age_ranges[0]]
    for start, end in age_ranges[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    # 전체 커버 체크
    if merged[0][0] <= 0 and merged[-1][1] >= 200:
        return "제한 없음"
    # 하나의 구간으로 축약 가능하면 간단히
    if len(merged) == 1:
        s, e = merged[0]
        if s <= 0:
            return f"만 {e}세 이하"
        elif e >= 200:
            return f"만 {s}세 이상"
        else:
            return f"만 {s}세 이상 ~ 만 {e}세 이하"
    # 그 외는 원본 반환
    return value

# ---------- 내부 메서드 ----------
async def _safe_fetch_json(client: httpx.AsyncClient, params: Dict[str, Any]) -> Dict[str, Any]:
    try:
        r = await client.get(BASE_URL, params=params, timeout=10.0)
        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "application/json" not in ctype.lower():
            # HTML/빈 응답 등 → 빈 데이터로 처리
            return {}
        return r.json()
    except Exception as e:
        # 네트워크/JSON 파싱/HTTP 오류 → 빈 데이터로 처리
        print(f"[ERROR] page={params.get('pageNo')} 요청 실패: {e}")
        return {}

async def _fetch_page_items(client: httpx.AsyncClient, page_no: int, num_rows: int) -> List[Dict[str, Any]]:
    params = {
        "serviceKey": SERVICE_KEY,
        "pageNo": page_no,
        "numOfRows": num_rows,
        "returnType": "json",
    }
    data = await _safe_fetch_json(client, params)
    return data.get("data", []) or []

def _filter_and_dedupe(items: List[Dict[str, Any]], seen: set[str]) -> List[Dict[str, Any]]:
    out = []
    for it in items:
        sprv = (it.get("sprv_inst") or "").strip()
        if "민간" in sprv:
            continue
        ext = it.get("pbanc_sn")
        key = f"{ext}" if ext is not None else None
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        out.append(it)
    return out

# ---------- 공개 함수 ----------
async def fetch_startup_supports_async(
        *,
        num_rows: int = 10,
        batch_concurrency: int = 5,
        max_empty_batches: int = 2,
        sleep_between_batches: float = 0.05,
        hard_max_pages: int = 500,  # 안전 상한
) -> List[CreateStartupResponseDTO]:

    all_items: List[Dict[str, Any]] = []
    seen: set[str] = set()
    empty_batches = 0

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(headers={"Accept": "application/json"}, limits=limits) as client:
        # 1) 첫 페이지로 총 페이지 수 추정
        first = await _safe_fetch_json(client, {
            "serviceKey": SERVICE_KEY, "pageNo": 1, "numOfRows": num_rows, "returnType": "json"
        })
        first_items = (first.get("data") or [])
        all_items.extend(_filter_and_dedupe(first_items, seen))

        total_pages: Optional[int] = None
        try:
            # 보통 totalCount/numOfRows 로 계산 가능 (없으면 예외)
            total_count = int(first.get("totalCount") or first.get("total_count") or 0)
            if total_count > 0 and num_rows > 0:
                total_pages = max(1, (total_count + num_rows - 1) // num_rows)
        except Exception:
            total_pages = None

        # 2) 나머지 페이지 수집 (배치)
        page = 2
        while True:
            if total_pages is not None and page > total_pages:
                break
            if page > hard_max_pages:
                print(f"[INFO] hard_max_pages({hard_max_pages}) 도달로 종료")
                break

            pages = list(range(page, page + batch_concurrency))
            # total_pages가 있으면 넘어가지 않도록 컷
            if total_pages is not None:
                pages = [p for p in pages if p <= total_pages]
                if not pages:
                    break

            tasks = [asyncio.create_task(_fetch_page_items(client, p, num_rows)) for p in pages]
            results = await asyncio.gather(*tasks)

            batch_count = 0
            for items in results:
                filt = _filter_and_dedupe(items, seen)
                all_items.extend(filt)
                batch_count += len(filt)

            if batch_count == 0:
                empty_batches += 1
                if empty_batches >= max_empty_batches:
                    break
            else:
                empty_batches = 0

            page += batch_concurrency
            if sleep_between_batches:
                await asyncio.sleep(sleep_between_batches)

    # DTO 변환
    dtos: List[CreateStartupResponseDTO] = []
    for it in all_items:
        try:
            dtos.append(to_create_startup_response(it))
        except Exception as e:
            print(f"[WARN] DTO 변환 실패 (pbanc_sn={it.get('pbanc_sn')}): {e}")
    return dtos
