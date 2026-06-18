"""
run_report.py — 데이터 → 차트 무인 실행 파이프라인

흐름:
  1) config.yaml 읽기
  2) CSV 로드
  3) validate.py 로 검증 → output/validation_report.txt
  4) 검증 통과 시에만, config의 charts 명세대로 표준 함수 호출
  5) output/ 에 PNG 300dpi 일괄 저장

실행:  uv run run_report.py
       uv run run_report.py --config config.yaml
       uv run run_report.py --data ../data/trackB_aging_dirty.csv   # 깨진 데이터 시연
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pandas as pd
import yaml

from charts import report_charts as rc
import validate as V


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def apply_transform(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """config의 transform 키 처리(차트 전 전처리)."""
    if name == "papers_count":
        return df.groupby(["country", "year"]).size().reset_index(name="paper_count")
    if name == "cluster_growth":
        # 클러스터별 (2025 합) - (2015 합) 증감
        recent = df[df["year"] == df["year"].max()].groupby("cluster_name")["paper_count"].sum()
        base_year = max(df["year"].min(), df["year"].max() - 10)
        base = df[df["year"] == base_year].groupby("cluster_name")["paper_count"].sum()
        growth = (recent - base).reset_index()
        growth.columns = ["cluster_name", "paper_count"]
        return growth
    if name == "exec_rate_deviation":
        # 부서별 연평균 집행률 - 100 (플러스=초과, 마이너스=미달)
        avg = df.groupby("department")["exec_rate"].mean().reset_index()
        avg["exec_rate"] = avg["exec_rate"] - 100
        return avg
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--data", default=None,
                    help="aggregated CSV 경로를 덮어쓴다(깨진 데이터 시연 등)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    out_dir = cfg.get("output_dir", "output")
    source_folders = {k: Path(v).stem for k, v in cfg["data"].items()}

    # --- 데이터 로드 --------------------------------------------------
    # config의 data 블록을 모두 로드(--data 는 aggregated 경로만 덮어씀)
    sources = {}
    for name, path in cfg["data"].items():
        if name == "aggregated" and args.data:
            path = args.data
        sources[name] = pd.read_csv(path)

    print(f"[1/3] 데이터 로드: {', '.join(f'{k}={v}' for k, v in cfg['data'].items())}")

    # --- 검증 --------------------------------------------------------
    all_passed = True
    full_report = []
    for src_name, df in sources.items():
        rules = cfg.get("validation", {}).get(src_name, {})
        if not rules:
            continue
        passed, report = V.validate(df, rules)
        full_report.append(f"\n##### 소스: {src_name} #####\n{report}")
        all_passed = all_passed and passed
    report_path = V.write_report("\n".join(full_report), output_dir=out_dir)
    print(f"[2/3] 검증 리포트: {report_path}  →  {'통과 ✅' if all_passed else '실패 ❌'}")

    if not all_passed:
        print("검증 실패로 차트 생성을 중단합니다. "
              f"자세한 내용은 {report_path} 를 확인하세요.")
        sys.exit(1)

    # --- 차트 일괄 생성 ----------------------------------------------
    made = []
    for spec in cfg["charts"]:
        func = rc.REGISTRY.get(spec["func"])
        if func is None:
            print(f"  [건너뜀] 알 수 없는 함수: {spec['func']}")
            continue
        df = sources[spec.get("source", "aggregated")].copy()
        if spec.get("transform"):
            df = apply_transform(spec["transform"], df)
        src_name = spec.get("source", "aggregated")
        chart_dir = Path(out_dir) / source_folders[src_name]
        outfile = str(chart_dir / f"chart_{spec['id']}.png")
        # 통일 시그니처에 매핑 전달(없는 키는 함수가 무시)
        kwargs = {k: spec[k] for k in
                  ("x", "y", "group", "facet", "value", "size", "title")
                  if k in spec}
        func(df, outfile=outfile, **kwargs)
        made.append(outfile)
        print(f"  [생성] {outfile}")

    print(f"[3/3] 완료: 차트 {len(made)}개 + 검증 리포트")
    print(f"      출력 폴더: {Path(out_dir).resolve()}")


if __name__ == "__main__":
    main()
