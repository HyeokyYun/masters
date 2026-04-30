# 석사학위논문 — 더 진행되어야 하는 작업 정리

**전체 흐름(분석→분류→예측)과 “뭘 더 해야 하나” 요약은 `research_flow_and_thesis_checklist.md` 참고.**

## 1. 문서화·논문 작성

- [ ] **방법론 섹션**: 260213 미팅 반영 — 경제 시계열 클러스터링 방법 소개, K-Shape/거리 기반 한계, K=6·K-Shape 선정 이유 명시 (참고: `docs/260213_meeting_clustering_methodology.md`)
- [ ] **결과 섹션**: `thesis_results_summary.md`의 표·경로 기준으로 표/그림 번호 매기기 (클러스터 비교, 예측, ablation, 성공률)
- [ ] **재현성**: 실행 순서 정리 (260204 run_01 → run_02_cluster_fix / run_04; 260211 build_30w → run_prediction_80_20)

## 2. 실험·스크립트 (선택)

- [ ] **260204 run_01_prepare_features**: `data_features_clean.parquet` 생성. 이 파일이 없으면 run_04_storyline_ablation 실패. (이미 있다면 생략)
- [ ] **260211**: `features_30w_and_labels.parquet` 없으면 build_30w 실행 후 run_prediction_80_20 재실행 가능 (이미 결과 있으면 생략)
- [ ] **클러스터 비교 표**: `compare_methods_no_dtw.csv`를 논문용 표로 정리 (method, K, ARI, NMI, bootstrap ARI, M1 F1)

## 3. 260216에 모아 둔 결과

- `docs/260213_meeting_clustering_methodology.md` — 미팅 내용 반영
- `docs/thesis_results_summary.md` — 필요 결과 목록·핵심 수치
- `docs/thesis_remaining_tasks.md` — 본 문서
- `outputs/tables/` — 핵심 CSV 복사본 (아래 스크립트로 복사 가능)
- `outputs/figures/` — 핵심 그림 복사본

## 4. 복사 권장 파일 목록

논문 작성 시 한곳에서 참조하려면 아래를 260216로 복사:

```
260204/outputs/tables/compare_methods_no_dtw.csv       → 260216/outputs/tables/
260204/outputs/tables/cluster_stability_summary.csv   → 260216/outputs/tables/
260204/outputs/tables/success_rate_by_cluster.csv      → 260216/outputs/tables/
260204/outputs/tables/ablation_results.csv             → 260216/outputs/tables/
260211/outputs/tables/prediction_80_20_results.csv    → 260216/outputs/tables/
260204/outputs/figures/cluster_means_K6.png           → 260216/outputs/figures/
260211/outputs/figures/prediction_80_20_M0_vs_M1.png  → 260216/outputs/figures/
```

위 복사는 `scripts/copy_thesis_results.py` 또는 수동으로 실행 가능.
