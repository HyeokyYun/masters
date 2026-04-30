# 260216 — 석사논문 마무리용 정리

- **260213 미팅** 반영: 경제 데이터 시계열 클러스터링 방법, K-Shape 한계, (임의) 선정 이유 정리.
- **지금까지 결과** 종합 및 **필요 결과 목록** 정리.
- **추가 진행 작업** 정리 및 핵심 산출물을 이 폴더에 모음.

## 폴더 구조

```
260216/
├── README.md
├── docs/
│   ├── 260213_meeting_clustering_methodology.md   # 미팅: 경제 TS clustering, kshape 한계, 선정 이유
│   ├── data_source_and_original_data.md           # 원본 vs store_features_for_analysis.csv, 권장 방향
│   ├── performance_and_regression_guide.md        # 성능 향상 + 회귀(regression) 진행 가이드
│   ├── research_flow_and_thesis_checklist.md      # 연구 흐름(분석→분류→예측) + 논문 마무리 체크리스트
│   ├── thesis_results_summary.md                  # 논문용 결과 종합·필요 결과 목록
│   └── thesis_remaining_tasks.md                  # 더 진행할 작업 체크리스트
├── scripts/
│   └── copy_thesis_results.py                     # 핵심 결과 파일 → outputs 복사
└── outputs/
    ├── tables/                                    # 복사된 CSV (방법 비교, 안정성, 예측, ablation 등)
    └── figures/                                   # 복사된 그림 (cluster_means_K6, prediction M0 vs M1)
```

## 사용

1. **미팅 내용 논문 반영**: `docs/260213_meeting_clustering_methodology.md` 참고.
2. **표/그림 참조**: `docs/thesis_results_summary.md`의 경로·수치 사용.
3. **남은 작업**: `docs/thesis_remaining_tasks.md` 체크리스트 진행.
4. **결과 재복사**: `python3 scripts/copy_thesis_results.py` (260216에서 실행).
