# CPU/스레드 튜닝: 한 곳에서 통제
import os
import multiprocessing
import logging

log = logging.getLogger("cpu_tuning")

def _setenv(key: str, val: int):
    # 이미 지정돼 있으면 유지 (배포 서버에서 수동으로 설정할 수 있도록)
    os.environ.setdefault(key, str(int(val)))

def apply_cpu_tuning(default_workers: int | None = None) -> None:
    # 비상시를 위한 끄기 스위치 (기본: 켜짐)
    if os.getenv("ENABLE_CPU_TUNING", "1") in ("0", "false", "False"):
        log.info("[cpu] tuning skipped (ENABLE_CPU_TUNING=0)")
        return

    vcpu = int(os.getenv("VCPU", multiprocessing.cpu_count()))
    workers = int(os.getenv("APP_WORKERS", default_workers or 1))

    # 워커당 스레드 수
    per = max(1, vcpu // max(1, workers))
    per = min(per, int(os.getenv("THREADS_PER_WORKER_CAP", "4")))  # 4로 상한

    # BLAS/NumExpr
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        _setenv(k, per)

    # FAISS
    _setenv("FAISS_NUM_THREADS", per)
    try:
        import faiss  # noqa
        faiss.omp_set_num_threads(int(os.getenv("FAISS_NUM_THREADS", per)))
    except Exception:
        pass  # faiss 미사용 시 무시

    # PyTorch
    try:
        import torch  # noqa
        torch.set_num_threads(per)
        torch.set_num_interop_threads(1)
    except Exception:
        pass  # torch 미사용 시 무시

    log.info(f"[cpu] vcpu={vcpu} workers={workers} per={per} "
             f"(cap={os.getenv('THREADS_PER_WORKER_CAP','4')}) "
             f"env_set_if_empty=OMP/OPENBLAS/MKL/NUMEXPR/FAISS/PyTorch")
