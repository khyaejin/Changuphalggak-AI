"""
k-startup open api 통신 및 데이터 가공 로직
"""

import base64
import os
import re
import asyncio
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import httpx
from dotenv import load_dotenv
from api.dto.startup_dto import CreateStartupResponseDTO

from api.services.vectorize_hook import vectorize_and_upsert_from_dtos

load_dotenv()
SERVICE_KEY = os.getenv("SERVICE_KEY")
BASE_URL = os.getenv("BASE_URL")

# ---------- 로거 ----------
logger = logging.getLogger("startup_service")

# ---------- 유틸 메서드들 ----------
# 문자열 → date 객체
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
        # 만 XX세 미만
        m = re.match(r"만\s*(\d+)\s*세\s*미만", t)
        if m:
            age_ranges.append((0, int(m.group(1)) - 1))
            continue
        # 만 XX세 이상 ~ 만 YY세 이하
        m = re.match(r"만\s*(\d+)\s*세\s*이상\s*~\s*만\s*(\d+)\s*세\s*이하", t)
        if m:
            age_ranges.append((int(m.group(1)), int(m.group(2))))
            continue
        # 만 XX세 이상
        m = re.match(r"만\s*(\d+)\s*세\s*이상", t)
        if m:
            age_ranges.append((int(m.group(1)), 200))
            continue
    # 범위가 없으면 원본 사용
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
    # 하나의 구간으로 축약 가능하면 간단히 하기
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
        log_params = {k: v for k, v in params.items() if k != "serviceKey"}
        # 요청 관련 정보 찍기
        logger.debug("[HTTP] GET 요청 보냄 → URL=%s, 요청 params=%s", BASE_URL, log_params)
        r = await client.get(BASE_URL, params=params, timeout=10.0)
        # 응답 관련 정보 찍기
        logger.debug("[HTTP] 응답 받음 → page=%s, status=%s, bytes=%s",
                     params.get("pageNo"), r.status_code, len(r.content))

        r.raise_for_status()
        ctype = r.headers.get("content-type", "")
        if "application/json" not in ctype.lower():
            # HTML/빈 응답 등 있는 경우 → 빈 데이터로 처리
            logger.warning("[HTTP] Non-JSON content-type=%s (page=%s)", ctype, params.get("pageNo"))
            return {}
        return r.json()
    except Exception as e:
        # 네트워크/JSON 파싱/HTTP 오류 → 빈 데이터로 처리
        logger.error("[ERROR] page=%s 요청 실패(네트워크, JSON 파싱, HTTP 오류: %s", params.get("pageNo"), e)
        return {}

async def _fetch_page_items(client: httpx.AsyncClient, page_no: int, num_rows: int) -> List[Dict[str, Any]]:
    params = {
        "serviceKey": SERVICE_KEY,
        "page": page_no, # pageNo -> page
        "perPage": num_rows, # numOfRows -> perPage
        "returnType": "json",
    }
    data = await _safe_fetch_json(client, params)
    items = data.get("data", []) or []
    logger.debug("[PAGE] page=%s raw_items=%s", page_no, len(items))
    return items

def _filter_and_dedupe(items, seen):
    out = []
    removed_private = 0
    removed_dup = 0
    for it in items:
        sprv = (it.get("sprv_inst") or "").strip()
        if "민간" in sprv: # 추후 필요하면 필터링 더 추가
            removed_private += 1
            continue
        ext = it.get("pbanc_sn")
        key = f"{ext}" if ext is not None else None
        if key and key in seen:
            removed_dup += 1
            continue
        if key:
            seen.add(key)
        out.append(it)
    logger.debug("[FILTER] in=%s -> out=%s (민간:%s, dup:%s)",
                 len(items), len(out), removed_private, removed_dup)
    return out

# ---------- 공개 함수 ----------
async def fetch_startup_supports_async(
        *,
        after_external_ref: str | None = None,
        num_rows: int = 10, # 한 번에 10개로
        batch_concurrency: int = 5,
        max_empty_batches: int = 2,
        sleep_between_batches: float = 0.05,
        hard_max_pages: int = 50, # 상한선 -> 추후 배포시 500으로 변경 예정
) -> List[CreateStartupResponseDTO]:
    logger.info("[START] after_external_ref=%s num_rows=%s batch_concurrency=%s",
                after_external_ref, num_rows, batch_concurrency)

    all_items: List[Dict[str, Any]] = []
    seen: set[str] = set()
    empty_batches = 0
    pages_scanned = 0

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=50)
    async with httpx.AsyncClient(headers={"Accept": "application/json"}, limits=limits) as client:

        # 1) after_external_ref가 있는 경우: 마커까지 순차로 수집 ---
        if after_external_ref:
            page = 1
            found_marker = False

            while True:
                # 안전 상한/빈 페이지 종료
                if page > hard_max_pages:
                    logger.info("[STOP] hard_max_pages(%s) 도달", hard_max_pages)
                    break

                items = await _fetch_page_items(client, page, num_rows)
                pages_scanned += 1
                filt = _filter_and_dedupe(items, seen)

                # 응답(items)이 빈 경우 -> 끝 간주
                if not items:
                    empty_batches += 1
                    logger.debug("[LOOP-A] empty batch count=%s", empty_batches)
                    if empty_batches >= max_empty_batches:
                        logger.info("[STOP] max_empty_batches(%s) 도달", max_empty_batches)
                        break
                else:
                    empty_batches = 0  # 응답은 있었음(필터로 비었더라도 계속 진행)

                # 최신부터 과거로 조회로 조회함
                for it in filt:
                    ext = it.get("pbanc_sn")
                    ext_str = f"{ext}" if ext is not None else None
                    if ext_str == after_external_ref:
                        found_marker = True
                        # 마커 전까지만 수집(중복 방지)
                        logger.info("[CURSOR] marker found externalRef=%s at page=%s", after_external_ref, page)
                        break
                    all_items.append(it)

                if found_marker:
                    break

                page += 1
                if sleep_between_batches:
                    await asyncio.sleep(sleep_between_batches)

        # 2) after_external_ref가 없는 경우: 기존 배치 병렬 수집 ---
        else:
            # 1) 첫 페이지로 총 페이지 수 추정
            first = await _safe_fetch_json(client, {
                "serviceKey": SERVICE_KEY, "page": 1, "perPage": num_rows, "returnType": "json"
            })
            pages_scanned += 1
            first_items = (first.get("data") or [])
            all_items.extend(_filter_and_dedupe(first_items, seen))

            total_pages: Optional[int] = None
            try:
                total_count = int(first.get("totalCount") or first.get("total_count") or 0)
                if total_count > 0 and num_rows > 0:
                    total_pages = max(1, (total_count + num_rows - 1) // num_rows)
            except Exception:
                total_pages = None
            logger.info("[INFO] estimated total_pages=%s (total_count=%s, page_size=%s)",
                        total_pages, first.get("totalCount") or first.get("total_count"), num_rows)

            # 2) 나머지 페이지 수집 (배치)
            page = 2
            while True:
                if total_pages is not None and page > total_pages:
                    logger.info("[STOP] reached end of pages (%s)", total_pages)
                    break
                if page > hard_max_pages:
                    logger.info("[STOP] hard_max_pages(%s) 도달", hard_max_pages)
                    break

                pages = list(range(page, page + batch_concurrency))
                if total_pages is not None:
                    pages = [p for p in pages if p <= total_pages]
                    if not pages:
                        break

                logger.debug("[LOOP-B] batch pages=%s", pages)
                tasks = [asyncio.create_task(_fetch_page_items(client, p, num_rows)) for p in pages]
                results = await asyncio.gather(*tasks)
                pages_scanned += len(results)

                raw_non_empty = 0
                batch_added = 0
                for items in results:
                    if items:
                        raw_non_empty += 1
                    filt = _filter_and_dedupe(items, seen)
                    all_items.extend(filt)
                    batch_added += len(filt)

                logger.debug("[LOOP-B] raw_non_empty=%s batch_added=%s total_collected=%s",
                             raw_non_empty, batch_added, len(all_items))

                if raw_non_empty == 0:
                    empty_batches += 1
                    logger.debug("[LOOP-B] empty batch count=%s", empty_batches)
                    if empty_batches >= max_empty_batches:
                        logger.info("[STOP] max_empty_batches(%s) 도달", max_empty_batches)
                        break
                else:
                    empty_batches = 0

                page += batch_concurrency
                if sleep_between_batches:
                    await asyncio.sleep(sleep_between_batches)

    # DTO 변환
    dtos: List[CreateStartupResponseDTO] = []
    dto_fail = 0
    for it in all_items:
        try:
            dtos.append(to_create_startup_response(it))
        except Exception as e:
            dto_fail += 1
            logger.warning("[WARN] DTO 변환 실패 (pbanc_sn=%s): %s", it.get("pbanc_sn"), e)
    # ★ 임베딩/인덱스 업데이트 (제목+본문만, external_ref 기준)
    try:
        vectorize_and_upsert_from_dtos(dtos)
    except Exception as e:
        logger.error("[VEC][ERROR] 벡터화 실패: %s", e)

    logger.info("[SUMMARY] 처리한 페이지=%s 수집한 원본 데이터=%s DTO 변환 성공=%s DTO 변환 실패=%s",
                pages_scanned, len(all_items), len(dtos), dto_fail)
    return dtos
