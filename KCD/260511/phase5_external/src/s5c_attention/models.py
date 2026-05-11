"""SMB-specific attention/weighting 모델 3종 (Phase 5C).

1. FeatureAttnMLP — 56-D tabular feature 입력. Squeeze-Excite 스타일
   feature-attention gate로 중요 feature를 동적으로 강조.
2. TimeAttnLSTM — 6채널 sequence 입력. LSTM hidden states에 softmax
   attention을 적용해 weighted pool. step06 vanilla LSTM(last-step)보다
   더 expressive.
3. FiLM_TenureLSTM — sequence + scalar tenure_log 입력. tenure_log에서
   γ, β 를 학습해 LSTM hidden state 에 FiLM 변조. 미팅 피드백
   "업력이 상승에 유의미"를 모델 구조로 인코딩.

학습 루프는 common/cv_harness.py의 seq_train_eval / rf_baseline_folds를 그대로
재사용.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class FeatureAttnMLP(nn.Module):
    """Squeeze-Excite feature-attention over tabular features.

    Input: x [B, F]  (F-dim tabular features after standardization)
    Forward: gate = sigmoid(W2 ReLU(W1 BN(x)))  → x_gated = gate * x  → MLP head
    """

    def __init__(self, n_feat: int, n_cls: int = 3, hidden: int = 64, gate_hidden: int = 32):
        super().__init__()
        self.bn = nn.BatchNorm1d(n_feat)
        self.gate = nn.Sequential(
            nn.Linear(n_feat, gate_hidden),
            nn.ReLU(),
            nn.Linear(gate_hidden, n_feat),
            nn.Sigmoid(),
        )
        self.head = nn.Sequential(
            nn.Linear(n_feat, hidden), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden, hidden // 2), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(hidden // 2, n_cls),
        )

    def forward(self, x_tab: torch.Tensor) -> torch.Tensor:
        z = self.bn(x_tab)
        g = self.gate(z)
        x_gated = g * x_tab
        return self.head(x_gated)


class TimeAttnLSTM(nn.Module):
    """LSTM with softmax attention over time-steps.

    Input: x [B, T, C]
    Forward:
        out, _ = LSTM(x)            # [B, T, H]
        a = softmax(W_a out, dim=1) # [B, T, 1]
        pooled = (a * out).sum(1)   # [B, H]
        logits = head(pooled)
    """

    def __init__(self, c: int, h: int = 64, n_cls: int = 3):
        super().__init__()
        self.lstm = nn.LSTM(c, h, batch_first=True)
        self.attn_w = nn.Linear(h, 1)
        self.head = nn.Sequential(
            nn.Linear(h, 32), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(32, n_cls),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)              # [B, T, H]
        scores = self.attn_w(out)          # [B, T, 1]
        weights = F.softmax(scores, dim=1) # [B, T, 1]
        pooled = (weights * out).sum(dim=1)  # [B, H]
        return self.head(pooled)


class FiLM_TenureLSTM(nn.Module):
    """LSTM with FiLM modulation conditioned on tenure_log scalar.

    Input: x [B, T, C], cond [B] (tenure_log)
    Forward:
        out, _ = LSTM(x)                # [B, T, H]
        last = out[:, -1, :]            # [B, H]
        gamma, beta = FiLM(cond)        # [B, H], [B, H]
        modulated = gamma * last + beta
        logits = head(modulated)
    """

    def __init__(self, c: int, h: int = 64, n_cls: int = 3, cond_dim: int = 1):
        super().__init__()
        self.lstm = nn.LSTM(c, h, batch_first=True)
        self.film = nn.Sequential(
            nn.Linear(cond_dim, 32), nn.ReLU(),
            nn.Linear(32, 2 * h),  # outputs γ and β concat
        )
        self.h = h
        self.head = nn.Sequential(
            nn.Linear(h, 32), nn.ReLU(), nn.Dropout(0.3),
            nn.Linear(32, n_cls),
        )

    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        out, _ = self.lstm(x)
        last = out[:, -1, :]                        # [B, H]
        film_p = self.film(cond)                    # [B, 2H]
        gamma, beta = film_p[:, :self.h], film_p[:, self.h:]
        # initialize γ as 1 by adding 1 to learned offset → starts close to identity
        modulated = (1.0 + gamma) * last + beta
        return self.head(modulated)
