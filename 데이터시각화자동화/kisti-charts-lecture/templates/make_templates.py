"""
templates/make_templates.py — 블록 2 노코딩 보강용 '인터랙티브 Plotly HTML' 생성기

블록 2의 기본 도구는 Claude.ai(노코딩)이지만, 같은 룩의 재사용 HTML 템플릿을
함께 제공한다. 데이터 교체 재렌더 = 이 스크립트의 CSV 경로만 바꿔 다시 실행.

실행: python make_templates.py
산출: templates/admin_report_template.html  (자체완결 인터랙티브 대시보드)

하우스 스타일: 흰 배경(plotly_white) + 국가 고정색과 동일 톤의 팔레트 + 한글 폰트.
※ 인터랙티브 HTML은 블록 2 전용. 블록 3·4 표준 코드는 PNG 단일.
"""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data" / "trackA_admin.csv"
OUT = HERE / "admin_report_template.html"

# 부서 팔레트(국가 고정색과 같은 톤)
DEPT_PALETTE = ["#1F6FB2", "#E1812C", "#3C8C5A", "#C23B3B", "#8C61C2"]
FONT = "Malgun Gothic, AppleGothic, NanumGothic, Noto Sans CJK KR, sans-serif"


def build(df: pd.DataFrame) -> go.Figure:
    depts = sorted(df["department"].unique())
    months = sorted(df["month"].unique())
    cmap = {d: DEPT_PALETTE[i % len(DEPT_PALETTE)] for i, d in enumerate(depts)}

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("부서별 월 예산집행(묶음막대)", "부서별 집행률 추이(선)",
                        "부서별 연간 집행액 비중(도넛)", "월별 총 과제 건수(막대)"),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "domain"}, {"type": "bar"}]],
        vertical_spacing=0.13, horizontal_spacing=0.10,
    )

    # (1) 묶음막대: 부서별 월 예산집행
    for d in depts:
        sub = df[df["department"] == d]
        fig.add_bar(x=sub["month"], y=sub["budget_exec"], name=d,
                    marker_color=cmap[d], legendgroup=d, row=1, col=1)

    # (2) 선: 부서별 집행률 추이
    for d in depts:
        sub = df[df["department"] == d]
        fig.add_scatter(x=sub["month"], y=sub["exec_rate"], name=d, mode="lines+markers",
                        line=dict(color=cmap[d], width=2), legendgroup=d,
                        showlegend=False, row=1, col=2)

    # (3) 도넛: 부서별 연간 집행액 비중
    annual = df.groupby("department")["budget_exec"].sum().reindex(depts)
    fig.add_pie(labels=depts, values=annual.values, hole=0.45,
                marker=dict(colors=[cmap[d] for d in depts]),
                textinfo="label+percent", legendgroup="pie",
                showlegend=False, row=2, col=1)

    # (4) 막대: 월별 총 과제 건수
    by_month = df.groupby("month")["projects"].sum().reindex(months)
    fig.add_bar(x=months, y=by_month.values, marker_color="#1F6FB2",
                name="과제건수", showlegend=False, row=2, col=2)

    fig.update_layout(
        template="plotly_white",
        title=dict(text="<b>KISTI 부서 운영 대시보드</b><br>"
                        "<span style='font-size:13px;color:#6B6B6B'>"
                        "출처: KISTI 강의용 샘플 데이터(시드 고정)</span>",
                   x=0.04, xanchor="left"),
        font=dict(family=FONT, size=12),
        barmode="group", height=820, width=1200,
        legend=dict(orientation="h", yanchor="bottom", y=-0.08, x=0),
        margin=dict(t=110, l=60, r=40, b=80),
    )
    fig.update_xaxes(tickangle=-45)
    return fig


def main():
    df = pd.read_csv(DATA)
    fig = build(df)
    pio.write_html(fig, file=str(OUT), include_plotlyjs="cdn",
                   full_html=True, config={"displayModeBar": True})
    print(f"생성 완료: {OUT}")


if __name__ == "__main__":
    main()
