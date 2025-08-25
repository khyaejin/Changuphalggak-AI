# CPU/스레드 튜닝: 한 곳에서 통제
import os
import platform
import multiprocessing
import logging

log = logging.getLogger("cpu_tuning")
IS_DARWIN = platform.system() == "Darwin"

def _setenv(key: str, val: int | str):
    # 값이 이미 있으면 건들이지 않음
    os.environ.setdefault(key, str(val))

def apply_cpu_tuning(default_workers: int | None = None) -> None:
    # 필요하면 끄기
    if os.getenv("ENABLE_CPU_TUNING", "1") in ("0", "false", "False"):
        log.info("[cpu]: 튜닝 비활성화 (ENABLE_CPU_TUNING=0)")
        return

    vcpu = int(os.getenv("VCPU", multiprocessing.cpu_count()))
    workers = int(os.getenv("APP_WORKERS", default_workers or 1))

    # macOS는 OpenMP 충돌 방지 위해 1스레드 고정
    if IS_DARWIN:
        per = 1
    else:
        per = max(1, vcpu // max(1, workers))
        per = min(per, int(os.getenv("THREADS_PER_WORKER_CAP", "4")))

    # 라이브러리들이 로드될 때 읽어가는 값들 (여기서는 import 금지)
    for k in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
            "FAISS_NUM_THREADS",
            "TORCH_NUM_THREADS",
    ):
        _setenv(k, per)

    # 토크나이저 병렬 억제
    _setenv("TOKENIZERS_PARALLELISM", "false")

    if IS_DARWIN:
        _setenv("KMP_INIT_AT_FORK", "FALSE")
        _setenv("OMP_WAIT_POLICY", "PASSIVE")
        # 응급용(개발용)
        if os.getenv("ENABLE_KMP_DUP", "0") in ("1", "true", "True"):
            _setenv("KMP_DUPLICATE_LIB_OK", "TRUE")
            log.warning("cpu: KMP_DUPLICATE_LIB_OK=TRUE 사용됨(개발용)")

    # 로깅
    log.info(f"[cpu]: per={per}, [workers]={workers}, [vcpu]={vcpu}, [darwin]={IS_DARWIN}")
