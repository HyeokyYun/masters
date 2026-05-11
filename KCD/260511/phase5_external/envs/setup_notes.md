# Phase 5 환경 설치 가이드

## 배경

- 기존 환경 `torch 2.9.1+cu128`은 sm_70+ 만 지원 → TITAN Xp (sm_61, 4장 × 12GB) 호환 불가
- 별도 conda env `phase5`에서 `torch 2.3.1+cu118` 사용 (sm_61 prebuilt 마지막 안정)
- 기존 `260430_claude/` 파이프라인 env는 건드리지 않음

## 설치 (GPU)

```bash
# 1) miniforge 또는 conda가 깔려 있다고 가정
conda env create -f /home/hyeoky98/kcd/260511/phase5_external/envs/phase5_sm61.yml
conda activate phase5

# 2) smoke test — 4장 모두 sm_61에서 CUDA 동작 확인
python - <<'PY'
import torch
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
print("device count:", torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    cap = torch.cuda.get_device_capability(i)
    name = torch.cuda.get_device_name(i)
    t = torch.randn(2, 3, device=f"cuda:{i}")
    print(f"  [{i}] {name}  sm_{cap[0]}{cap[1]}  test_sum={t.sum().item():.3f}")
PY
```

기대 출력: 각 GPU에 대해 `test_sum` 이 정상 출력되어야 한다. 만약
`no kernel image is available for execution on the device` 가 나오면 sm_61
호환이 깨진 것이므로 아래 CPU fallback 사용.

## 설치 (CPU fallback)

```bash
conda env create -f /home/hyeoky98/kcd/260511/phase5_external/envs/phase5_cpu.yml
conda activate phase5_cpu
```

CPU에서도 TimesFM-200m, Chronos-T5-small, Moirai-small 모두 동작 가능
(속도는 GPU 대비 10~30× 느림).

## 모델 가중치 사전 다운로드 (선택)

```bash
# HuggingFace에 로그인되어 있으면 자동 캐시됨 (~/.cache/huggingface/hub)
python - <<'PY'
from huggingface_hub import snapshot_download
for repo in [
    "google/timesfm-1.0-200m-pytorch",
    "amazon/chronos-t5-small",
    "amazon/chronos-bolt-small",
    "Salesforce/moirai-1.0-R-small",
]:
    print("downloading", repo)
    snapshot_download(repo_id=repo)
PY
```

총 약 2-4 GB 디스크 사용.

## 트러블슈팅

| 증상 | 원인 | 조치 |
|---|---|---|
| `RuntimeError: no kernel image` | torch가 sm_61 비호환 | conda env 다시 생성, `torch==2.3.1+cu118` 명시 |
| `ImportError: timesfm` | timesfm pip wheel 실패 | `pip install timesfm --no-deps` 후 deps 수동 설치 |
| `Chronos OOM` | batch_size 과대 | `predict(num_samples=20, batch_size=8)` 로 축소 |
| `neuralforecast trainer GPU not found` | env 비활성 | `conda activate phase5` 재확인 |
