"""
answer_key/report_charts_trackC_addition.py
─────────────────────────────────────────────────────────────────────
블록 4 적응 실습(시나리오 C) "정답 적응본" — 추가 차트 함수 1개.

용도: 라이브 적응이 막혔을 때 강사가 즉시 폴백.
사용법: 아래 plot_lollipop 함수를 charts/report_charts.py 끝에 붙여넣고,
        REGISTRY 딕셔너리에 "plot_lollipop": plot_lollipop 한 줄을 추가한다.
        (charts/style.py 는 절대 수정하지 않는다 — 룩은 그대로 유지)

이 차트는 '막대 계열'의 변형(롤리팝)으로, 이미 지원하는 스타일 자산만 사용한다.
"""
import matplotlib.pyplot as plt
try:
    from . import style
except ImportError:
    import style  # type: ignore


def plot_lollipop(df, *, x, y, group=None, title=None, palette=None,
                  outfile=None, top=None, subtitle=None, source=None, **kw):
    """롤리팝 차트(막대 계열 변형): x(범주)별 y(값)을 줄기+점으로 순위 표시."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    s = df.groupby(x)[y].sum().sort_values(ascending=True)
    if top:
        s = s.tail(int(top))
    ypos = range(len(s))
    ax.hlines(y=ypos, xmin=0, xmax=s.values, color=style.GRID_GRAY, linewidth=2)
    ax.plot(s.values, list(ypos), "o", markersize=9,
            color=style.CLUSTER_PALETTE[0])
    ax.set_yticks(list(ypos))
    ax.set_yticklabels(s.index.astype(str))
    ax.set_xlabel(y); ax.set_ylabel(x)
    style.finalize(ax, title=title or "롤리팝 차트", subtitle=subtitle,
                   legend=False, source=source or "출처: KISTI 강의용 샘플 데이터(시드 고정)")
    return style.save_fig(fig, outfile)


# REGISTRY 에 추가할 항목(복붙용):
#   "plot_lollipop": plot_lollipop,
