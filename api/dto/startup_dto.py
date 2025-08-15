from datetime import date
from typing import Optional
from pydantic import BaseModel

class CreateStartupResponseDTO(BaseModel):
    # 지원사업명
    title: str
    # 지원분야
    support_area: Optional[str] = None
    # 지역 (Enum 값 문자열)
    region: Optional[str] = None
    # 업력 대상 (Enum 값 문자열)
    business_duration: Optional[str] = None
    # 주관기관명
    agency: Optional[str] = None
    # 나이 제한
    target_age: Optional[str] = None
    # 지원 대상
    target: Optional[str] = None
    # 연락처
    contact: Optional[str] = None
    # 상세링크 (K-Startup 상세 페이지)
    link: Optional[str] = None
    # 모집 시작일
    start_date: Optional[date] = None
    # 모집 종료일
    end_date: Optional[date] = None
    # 신청 방법
    apply_method: Optional[str] = None  # aply_mthd_onli_rcpt_istc
    # 지원 내용
    support_details: Optional[str] = None


# 추가
    # 외부 참조 ID (pbanc_sn)
    external_ref: Optional[str] = None
    # 안내 페이지 URL
    guidance_url: Optional[str] = None
    # 모집 진행 여부
    is_recruiting: Optional[bool] = None
