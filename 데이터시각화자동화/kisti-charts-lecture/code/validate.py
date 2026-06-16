"""
validate.py — 데이터 품질 검증

점검 항목(도메인 규칙은 config.yaml의 validation 블록에서 주입):
  1) 필수열 스키마      : 빠진 열이 없는가
  2) 자료형             : 숫자여야 하는 열이 숫자인가
  3) 결측치             : 결측 셀 개수
  4) IQR 이상치         : 1.5*IQR 밖 값 개수
  5) 음수 차단          : 음수가 있으면 안 되는 열(예: 논문수)
  6) 연도 범위          : year 가 허용 범위 안인가
  7) 화이트리스트       : 국가/클러스터 등 허용 목록 밖 값이 없는가

산출: output/validation_report.txt + (통과 여부 bool, 리포트 문자열)
검증 실패 시 run_report.py 는 차트를 만들지 않고 중단한다.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path


def validate(df: pd.DataFrame, rules: dict) -> tuple[bool, str]:
    lines: list[str] = []
    problems = 0

    def log(msg):
        lines.append(msg)

    log("=" * 60)
    log("데이터 검증 리포트")
    log("=" * 60)
    log(f"행 수: {len(df)}, 열: {list(df.columns)}")
    log("")

    # 1) 필수열 스키마 -------------------------------------------------
    required = rules.get("required_columns", [])
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        problems += 1
        log(f"[실패] 필수열 누락: {missing_cols}")
    else:
        log(f"[통과] 필수열 모두 존재: {required}")

    # 2) 자료형 -------------------------------------------------------
    numeric_cols = [c for c in rules.get("numeric_columns", []) if c in df.columns]
    for c in numeric_cols:
        coerced = pd.to_numeric(df[c], errors="coerce")
        bad = coerced.isna().sum() - df[c].isna().sum()
        if bad > 0:
            problems += 1
            log(f"[실패] 숫자형이어야 할 열 '{c}'에 숫자 아님 {bad}건")
        else:
            log(f"[통과] 자료형 OK: '{c}' (숫자형)")

    # 3) 결측치 -------------------------------------------------------
    na = df.isna().sum()
    na = na[na > 0]
    if len(na):
        problems += 1
        log("[실패] 결측치 발견:")
        for c, n in na.items():
            log(f"        - {c}: {int(n)}건")
    else:
        log("[통과] 결측치 없음")

    # 4) IQR 이상치 ---------------------------------------------------
    for c in numeric_cols:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out = s[(s < lo) | (s > hi)]
        if len(out):
            ex = [int(v) if float(v).is_integer() else round(float(v), 1)
                  for v in sorted(out.unique())[:3]]
            log(f"[경고] IQR 이상치 '{c}': {len(out)}건 (허용 {lo:.0f}~{hi:.0f}, "
                f"예: {ex})")
        else:
            log(f"[통과] IQR 이상치 없음: '{c}'")

    # 5) 음수 차단 ----------------------------------------------------
    for c in [c for c in rules.get("nonnegative_columns", []) if c in df.columns]:
        s = pd.to_numeric(df[c], errors="coerce")
        neg = int((s < 0).sum())
        if neg > 0:
            problems += 1
            log(f"[실패] 음수 불가 열 '{c}'에 음수 {neg}건")
        else:
            log(f"[통과] 음수 없음: '{c}'")

    # 6) 연도 범위 ----------------------------------------------------
    yr = rules.get("year_column")
    yrange = rules.get("year_range")
    if yr and yrange and yr in df.columns:
        s = pd.to_numeric(df[yr], errors="coerce")
        bad = df[(s < yrange[0]) | (s > yrange[1])]
        if len(bad):
            problems += 1
            vals = sorted(pd.to_numeric(bad[yr], errors="coerce").dropna().unique().tolist())
            log(f"[실패] 연도 범위 밖 '{yr}': {len(bad)}건 "
                f"(허용 {yrange[0]}~{yrange[1]}, 예: {vals[:3]})")
        else:
            log(f"[통과] 연도 범위 OK: {yrange[0]}~{yrange[1]}")

    # 7) 화이트리스트 -------------------------------------------------
    for col, allowed in rules.get("whitelist", {}).items():
        if col not in df.columns:
            continue
        bad_vals = sorted(set(df[col].dropna().unique()) - set(allowed))
        if bad_vals:
            problems += 1
            log(f"[실패] 허용 목록 밖 '{col}': {bad_vals}")
        else:
            log(f"[통과] 화이트리스트 OK: '{col}'")

    log("")
    log("-" * 60)
    passed = problems == 0
    log(f"종합: {'통과 ✅ (차트 생성 진행)' if passed else f'실패 ❌ ({problems}건) → 중단'}")
    log("-" * 60)
    return passed, "\n".join(lines)


def write_report(report: str, output_dir="output", filename="validation_report.txt") -> str:
    out = Path(output_dir) / filename
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    return str(out)
