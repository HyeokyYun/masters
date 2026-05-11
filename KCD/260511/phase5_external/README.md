# 260511 / phase5_external — Phase 5 외부 SOTA · SMB-specific Novelty

본 폴더는 2026-05-07 교수 미팅 피드백("더 나은 prediction · 주식 literature 비교
· 새 모델 · feature weight")에 정량으로 응답한 Phase 5의 모든 코드/결과/문서.

## 한 줄 결과

> **LightGBM 이 RF tabular baseline 을 일관되게 이김 (+0.008 macro_F1, 5/6 panels).
> 그 외 외부 SOTA / foundation / SMB-specific attention 14종은 모두 RF에 큰 폭으로 패배.**

자세한 결과: `docs/phase5_findings.md`

## 빠른 안내

| 무엇이 | 어디에 |
|---|---|
| 한 줄 결과 + 종합표 | `docs/phase5_findings.md` |
| 70편 문헌 설문조사 | `docs/stock_vs_smb_literature.md` |
| 사전 설계 | `docs/phase5_design.md` |
| 리스크 일지 | `docs/risks_timebox.md` |
| 종합 CSV | `outputs/tables/phase5_summary.csv`, `phase5_master.csv` |
| 막대 그래프 | `outputs/figures/phase5_macro_f1_bars.png`, `phase5_delta_vs_rf.png` |
| 코드 | `src/` (`common/`, `s5{a,b,c,d}_*`, `analysis_*`, `figures_*`) |
| 환경 | `envs/phase5_sm61.yml`, `phase5_cpu.yml`, `setup_notes.md` |

## 워크스트림 결과

| WS | 무엇 | 모델 수 | 결과 |
|---|---|---:|---|
| 5A | TS Foundation Models | 2–3 | Chronos-Bolt: F1=0.289 (Δ-0.21). TimesFM: F1=0.230 (Δ-0.27). 모두 6/6 p<0.001 패배 |
| 5B | Stock SOTA (neuralforecast) | 7 | DLinear best (F1=0.361, Δ-0.14). 모두 6/6 p<0.001 패배 |
| 5C | SMB-attention | 3 | FeatureAttnMLP best (F1=0.462, Δ-0.035). 모두 패배. FiLM-tenure > TimeAttn |
| 5D | Feature weight / cost-sens | 7 | **LGBM tabular (F1=0.505, Δ+0.008, 5/6 wins)** ✓ |
| 5E | 문헌 설문 | 70편 | 6 영역 인용 + 비교 매트릭스. 본 thesis 차별화 5가지 명시 |

## 재실행

```bash
conda activate phase5
python src/s5c_attention/run_attention.py
python src/s5d_weighting/run_weighting.py
python src/s5b_neuralforecast/run_neuralforecast.py
python src/s5a_foundation/run_foundation.py --models chronos_bolt_small
python src/s5a_foundation/run_foundation.py --models timesfm_200m
python src/s5a_foundation/run_foundation.py --models moirai_small
python src/s5a_foundation/reconstruct_from_log.py
python src/analysis_paired_phase5.py
python src/figures_phase5.py
```

## v5_thesis_final 통합 권고

- **§5 또는 §6 ablation**: LightGBM 추가 비교를 conditional contribution으로
  (+0.008 macro_F1, M5 우승자 패턴 transfer).
- **§6.5/§7**: foundation/stock SOTA/SMB-attention 14종 negative finding을
  단일 narrative로 — "stock-style 직접 이식이 SMB 단기 분류에 안 통하는 정량
  증거".
- main contribution(seasonal alignment) 유지, 변경 없음.

## 환경 주의

기존 `torch 2.9.1`은 TITAN Xp(sm_61)과 호환 안 되므로 본 폴더는 **별도 conda env
`phase5`** (torch 2.3.1+cu118)를 빌드. 기존 `260430_claude/` 파이프라인 env는
건드리지 않음. 자세한 설치: `envs/setup_notes.md`.
