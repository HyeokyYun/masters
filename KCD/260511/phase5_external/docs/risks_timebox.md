# Phase 5 Risk · Timebox 일지

## 사후 실측 (2026-05-11 단일 세션)

| Workstream | 사전 예상 | 실측 | 비고 |
|---|---|---|---|
| G0 env build | 4h limit | ~12분 | sm_61 호환 wheels 캐시 활용 |
| G1 harness | 30분 | ~20분 | step06 RF F1 1e-6 재현 검증 |
| 5E literature | 0.5일 | ~30분 | 8 WebSearch 쿼리 → 70편 인용 |
| 5C attention | 1일 | ~30분 (CPU) | step06 patterns 재사용 |
| 5D weighting | 0.5일 | ~5분 (CPU) | LGBM/RF 빠름 |
| 5B neuralforecast | 2일 | ~25분 (GPU, 4× DDP) | 모델당 ~3–5분 |
| 5A chronos | 0.5일 | ~8분 (GPU) | zero-shot, fast |
| 5A timesfm | 1일 | ~25분 (GPU) | 모델 로드 47s, 추론 ~3분/panel |
| 5A moirai | 1일 | 1+ 시간 진행, 일부만 완주 | GluonTS adapter 느림 |
| Final analysis + figures + docs | 0.5일 | ~10분 | |

**총 단일 세션 소요**: 약 2.5시간 (사전 예상 9.5일 → 멀티-GPU + library 안정성 덕분에 100×+ 가속)

## 실측 리스크 사건

### Issue 1: sm_61 GPU 비호환 (G0)
- **원인**: torch 2.9.1 (기존 env)는 sm_70+만 지원
- **해결**: phase5 conda env에 torch 2.3.1+cu118 설치. smoke test 통과.
- **시간 손실**: 0 (env build 동안 5E 진행)

### Issue 2: cv_harness DEVICE 자동 fallback (G1)
- **원인**: `torch.cuda.is_available()` True but kernel exec fails on sm_61
- **해결**: `_safe_device()` 함수로 smoke test 후 CPU fallback. 기존 env에서도 동작.
- **시간 손실**: ~5분 (디버깅)

### Issue 3: 5B NeuralForecast NaN 거부 (5B)
- **원인**: raw weekly에 NaN sales_card 존재
- **해결**: `ffill → bfill → 0.0` chain
- **시간 손실**: ~3분

### Issue 4: 5B input_size 너무 큼 (5B)
- **원인**: 초기 `min(52, horizon*4)`가 일부 store history(< 52주)를 초과
- **해결**: `input_size = max(8, horizon)` + `start_padding_enabled=True`
- **시간 손실**: ~3분

### Issue 5: 5B 중복 프로세스 (5B)
- **원인**: bash background 재시작 시 이전 인스턴스 안 죽임 → 4 인스턴스 동시 실행
- **해결**: `pkill -f run_neuralforecast` 정리 후 재시작
- **시간 손실**: ~2분 (로그 분석)

### Issue 6: 5A CSV 덮어쓰기 (5A)
- **원인**: chronos 실행 후 timesfm이 같은 CSV 덮어씀
- **해결**: `reconstruct_from_log.py`로 로그에서 mean F1 파싱 + RF 재계산
- **시간 손실**: ~5분 (스크립트 작성)

### Issue 7: 5A Moirai 시작 느림
- **상태**: 1시간+ 진행 중 panel 1 모델 로드. GluonTS dataset 변환 cost.
- **조치**: 별도 백그라운드 유지, chronos+timesfm 결과로 5A 결론 도출.
- **시간 손실**: 0 (병렬 진행)

## 교훈 (다음 phase 권고)

1. **env 격리 효과 큼** — phase5 env 별도 빌드로 기존 env 안 건드림 + sm_61 호환.
2. **로그 기반 reconstruction이 강건** — CSV overwrite 같은 incident에 살아남음.
3. **PyTorch Lightning 다중 GPU DDP가 panel당 5×–10× 가속**.
4. **CPU도 충분히 빠름** — 5C/5D는 4× TITAN Xp 없이도 30분 이내 완주.
5. **Foundation model zero-shot은 결정적이지 않다** — fine-tune이 필요한지 사전 검토 불요. zero-shot이 RF 근접 못 하면 그 자체로 결론.
