"""
KISTI 데이터 시각화 강의 — 샘플 데이터 생성기 (시드 고정, 재현 가능)
실행: python make_data.py
생성물:
  트랙 A (행정, 블록 2)
    - trackA_admin.csv              정상본
  트랙 B (연구, 블록 3·4)
    - trackB_aging.csv              집계본(국가×클러스터×연도×논문수)
    - trackB_papers.csv            논문 단위(피인용·공동연구자·국제공동연구)
    - trackB_aging_next.csv         "다음 호" 재생산용(같은 스키마)
    - trackB_aging_dirty.csv        일부러 깨진 데이터(결측·이상치·음수·범위밖)
  트랙 C (적응 실습, 블록 4)
    - trackC_aging.csv              스키마가 다른 적응 실습용(열 이름 변경)
"""
import numpy as np
import pandas as pd
from pathlib import Path

SEED = 20260601
rng = np.random.default_rng(SEED)
HERE = Path(__file__).resolve().parent

# ----------------------------------------------------------------------
# 공통 정의
# ----------------------------------------------------------------------
COUNTRIES = ["한국", "미국", "일본", "중국"]
# 국가별 전체 규모 가중치(미·중이 크고, 한·일은 상대적으로 작게)
COUNTRY_SCALE = {"한국": 0.55, "미국": 1.6, "일본": 0.8, "중국": 1.4}

CLUSTERS = {
    1: "노인성질환",
    2: "인지·치매",
    3: "돌봄·요양",
    4: "노동·은퇴",
    5: "연금·소득보장",
    6: "고령친화기술",
    7: "사회참여·복지",
    8: "인구·정책",
}
YEARS = list(range(1985, 2026))  # 1985~2025

# ----------------------------------------------------------------------
# 트랙 B — 집계본(국가 × 클러스터 × 연도 × 논문수)
# ----------------------------------------------------------------------
def make_trackB_aggregated():
    rows = []
    for c in COUNTRIES:
        for cid, cname in CLUSTERS.items():
            # 클러스터별 기준 규모 & 성장 패턴(시간이 지날수록 증가, 클러스터마다 다름)
            base = rng.uniform(3, 12)
            growth = rng.uniform(0.04, 0.11)          # 연 성장률
            # 고령친화기술(6)·인지치매(2)는 최근 급성장
            late_boost = 2.2 if cid in (2, 6) else 1.0
            for y in YEARS:
                t = y - 1985
                trend = base * np.exp(growth * t)
                if cid in (2, 6):
                    # 2005년 이후 가속
                    trend *= 1 + max(0, (y - 2005)) * 0.03 * (late_boost - 1)
                noise = rng.normal(1.0, 0.12)
                val = trend * COUNTRY_SCALE[c] * noise
                paper_count = int(max(0, round(val)))
                rows.append([c, cid, cname, y, paper_count])
    df = pd.DataFrame(rows, columns=["country", "cluster_id", "cluster_name", "year", "paper_count"])
    return df

# ----------------------------------------------------------------------
# 트랙 B — 논문 단위(피인용·공동연구자·국제공동연구)
# ----------------------------------------------------------------------
def make_trackB_papers(agg):
    """집계본의 최근 연도(2015~2025) 표본을 논문 단위로 풀어 속성 부여."""
    recent = agg[agg["year"].between(2015, 2025)].copy()
    # 표본이 너무 커지지 않게 연도·클러스터당 일부만 샘플
    rows = []
    pid = 1
    for _, r in recent.iterrows():
        n_sample = min(int(r["paper_count"]), 6)  # 셀당 최대 6편 샘플
        for _ in range(n_sample):
            country = r["country"]
            cid = int(r["cluster_id"])
            year = int(r["year"])
            # 국제공동연구일수록 피인용·공동연구자 ↑
            intl = int(rng.random() < (0.25 + 0.04 * (cid in (2, 6))))
            coauthors = int(max(1, rng.poisson(4 + 3 * intl)))
            base_cite = rng.gamma(shape=2.2, scale=4 + 5 * intl)
            citations = int(round(base_cite * (1 + 0.04 * (2025 - year))))
            rows.append([pid, country, cid, CLUSTERS[cid], year, citations, coauthors, intl])
            pid += 1
    df = pd.DataFrame(rows, columns=[
        "paper_id", "country", "cluster_id", "cluster_name", "year",
        "citations", "coauthors", "intl_collab"
    ])
    return df

# ----------------------------------------------------------------------
# 트랙 B — "다음 호" 재생산용(같은 스키마, 값만 갱신: 2026년 한 해 추가)
# ----------------------------------------------------------------------
def make_trackB_next(agg):
    nxt = agg[agg["year"].between(2024, 2025)].copy()
    # 같은 스키마로 2026년 한 해를 덧붙인 버전
    add = []
    for (c, cid, cname), g in agg.groupby(["country", "cluster_id", "cluster_name"]):
        last = g[g["year"] == 2025]["paper_count"].iloc[0]
        val = int(round(last * rng.uniform(1.02, 1.12)))
        add.append([c, cid, cname, 2026, val])
    df = pd.concat([agg, pd.DataFrame(add, columns=agg.columns)], ignore_index=True)
    return df

# ----------------------------------------------------------------------
# 트랙 B — 일부러 깨진 데이터(검증 실습용)
# ----------------------------------------------------------------------
def make_trackB_dirty(agg):
    d = agg.copy()
    # 1) 결측치 주입
    idx = rng.choice(d.index, size=8, replace=False)
    d.loc[idx[:4], "paper_count"] = np.nan
    # 2) 음수 논문 수(있을 수 없는 값)
    d.loc[idx[4:6], "paper_count"] = -5
    # 3) 극단 이상치(IQR로 잡힐 값)
    d.loc[idx[6], "paper_count"] = 999999
    # 4) 연도 범위 밖
    d.loc[idx[7], "year"] = 1899
    # 5) 화이트리스트에 없는 국가
    extra = pd.DataFrame([["프랑스", 1, "노인성질환", 2025, 10]], columns=d.columns)
    d = pd.concat([d, extra], ignore_index=True)
    return d

# ----------------------------------------------------------------------
# 트랙 C — 적응 실습용(통제된 차이: 열 이름 변경)
#   country -> nation, year -> pub_year, paper_count -> n_papers,
#   cluster_name -> field, cluster_id -> field_id
# ----------------------------------------------------------------------
def make_trackC(agg):
    c = agg.rename(columns={
        "country": "nation",
        "cluster_id": "field_id",
        "cluster_name": "field",
        "year": "pub_year",
        "paper_count": "n_papers",
    })
    # 적응 실습은 최근 구간만(가벼운 스코프)
    c = c[c["pub_year"].between(2010, 2025)].reset_index(drop=True)
    return c

# ----------------------------------------------------------------------
# 트랙 A — 행정 운영 데이터(부서 × 월)
# ----------------------------------------------------------------------
def make_trackA():
    depts = ["기획조정실", "정보화본부", "연구데이터본부", "경영지원실", "미래전략실"]
    dept_scale = {"기획조정실": 1.0, "정보화본부": 1.4, "연구데이터본부": 1.6,
                  "경영지원실": 0.8, "미래전략실": 0.7}
    months = [f"2025-{m:02d}" for m in range(1, 13)]
    rows = []
    for dpt in depts:
        budget_plan = rng.uniform(800, 1500) * dept_scale[dpt]  # 연 예산편성(백만원)
        headcount = int(rng.uniform(18, 45) * dept_scale[dpt])
        n_projects = int(rng.uniform(6, 20) * dept_scale[dpt])
        for i, mth in enumerate(months):
            # 월별 집행은 연초 낮고 연말 높은 패턴 + 잡음
            seasonal = 0.4 + 0.9 * (i / 11)
            exec_amt = budget_plan / 12 * seasonal * rng.normal(1.0, 0.1)
            exec_amt = max(0, round(exec_amt, 1))
            hc = max(1, headcount + int(rng.normal(0, 1.2)))
            proj = max(0, n_projects + int(rng.normal(0, 1.0)))
            rows.append([dpt, mth, round(budget_plan / 12, 1), exec_amt, hc, proj])
    df = pd.DataFrame(rows, columns=[
        "department", "month", "budget_plan", "budget_exec", "headcount", "projects"
    ])
    # 집행률(%) 파생
    df["exec_rate"] = (df["budget_exec"] / df["budget_plan"] * 100).round(1)
    return df

# ----------------------------------------------------------------------
def main():
    agg = make_trackB_aggregated()
    papers = make_trackB_papers(agg)
    nxt = make_trackB_next(agg)
    dirty = make_trackB_dirty(agg)
    trackC = make_trackC(agg)
    trackA = make_trackA()

    agg.to_csv(HERE / "trackB_aging.csv", index=False, encoding="utf-8-sig")
    papers.to_csv(HERE / "trackB_papers.csv", index=False, encoding="utf-8-sig")
    nxt.to_csv(HERE / "trackB_aging_next.csv", index=False, encoding="utf-8-sig")
    dirty.to_csv(HERE / "trackB_aging_dirty.csv", index=False, encoding="utf-8-sig")
    trackC.to_csv(HERE / "trackC_aging.csv", index=False, encoding="utf-8-sig")
    trackA.to_csv(HERE / "trackA_admin.csv", index=False, encoding="utf-8-sig")

    print("생성 완료:")
    for f, df in [
        ("trackA_admin.csv", trackA), ("trackB_aging.csv", agg),
        ("trackB_papers.csv", papers), ("trackB_aging_next.csv", nxt),
        ("trackB_aging_dirty.csv", dirty), ("trackC_aging.csv", trackC),
    ]:
        print(f"  {f:28s} rows={len(df):5d}  cols={list(df.columns)}")

if __name__ == "__main__":
    main()
