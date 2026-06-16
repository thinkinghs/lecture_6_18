"""
charts/report_charts.py — 표준 차트 함수 라이브러리

모든 함수의 통일 시그니처(CLAUDE.md 규칙):
    plot_xxx(df, *, x, y, group=None, title=None, palette=None, outfile=None, **kw)

원칙:
  - 차트 = 순수 함수, 열 이름은 파라미터(하드코딩 금지) → 어떤 데이터든 적응
  - 스타일은 charts/style.py 만 사용(여기서 룩을 다시 정의하지 않음)
  - 산출은 PNG 300dpi 단일 (style.save_fig)
  - 반환값 = 저장된 PNG 경로(str)

트랙 B: ①누적영역 ②100%누적영역 ③국가별 클러스터 라인(facet) ④히트맵
        ⑤바이올린 ⑥박스 ⑦산점도(+버블) ⑧발산형 분할막대
트랙 A: 세로막대·묶음막대·누적막대·가로순위막대·선·다중선·도넛·100%누적막대·콤보
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

try:
    from . import style                      # 패키지로 import 될 때
except ImportError:                          # 단독 실행/복사 폴백
    import style                             # type: ignore


# ======================================================================
# 트랙 B — 연구용 차트 ①~⑧
# ======================================================================
def plot_stacked_area(df, *, x, y, group=None, title=None, palette=None,
                      outfile=None, subtitle=None, source=None, **kw):
    """① 누적 영역차트: x(연도) × group(국가/클러스터)별 y(논문수) 누적."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    piv = df.pivot_table(index=x, columns=group, values=y, aggfunc="sum").fillna(0)
    cols = list(piv.columns)
    colors = _resolve_colors(cols, palette)
    ax.stackplot(piv.index, *[piv[c] for c in cols], labels=cols, colors=colors, alpha=0.9)
    ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "누적 영역차트", subtitle=subtitle,
                   source=source or _src())
    return style.save_fig(fig, outfile)


def plot_pct_stacked_area(df, *, x, y, group=None, title=None, palette=None,
                          outfile=None, subtitle=None, source=None, **kw):
    """② 100% 상대비중 누적영역: 각 x에서 group들의 비중(%)."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    piv = df.pivot_table(index=x, columns=group, values=y, aggfunc="sum").fillna(0)
    pct = piv.div(piv.sum(axis=1).replace(0, np.nan), axis=0) * 100
    cols = list(pct.columns)
    colors = _resolve_colors(cols, palette)
    ax.stackplot(pct.index, *[pct[c] for c in cols], labels=cols, colors=colors, alpha=0.9)
    ax.set_ylim(0, 100); ax.set_xlabel(x); ax.set_ylabel("비중(%)")
    style.finalize(ax, title=title or "100% 누적영역(상대비중)", subtitle=subtitle,
                   source=source or _src())
    return style.save_fig(fig, outfile)


def plot_facet_line(df, *, x, y, group=None, title=None, palette=None,
                    outfile=None, facet=None, subtitle=None, source=None, **kw):
    """③ 국가별 클러스터 라인(facet / small multiples).
    facet=국가, group=클러스터로 작은 그래프 여러 개를 격자 배치."""
    style.apply_house_style()
    facets = sorted(df[facet].unique())
    n = len(facets)
    ncol = 2
    nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(11, 3.2 * nrow), sharex=True)
    axes = np.array(axes).reshape(-1)
    groups = sorted(df[group].unique())
    colors = _resolve_colors(groups, palette)
    cmap = dict(zip(groups, colors))
    for i, fv in enumerate(facets):
        ax = axes[i]
        sub = df[df[facet] == fv]
        for g in groups:
            s = sub[sub[group] == g].groupby(x)[y].sum()
            ax.plot(s.index, s.values, color=cmap[g], linewidth=1.6, label=str(g))
        ax.set_title(str(fv), loc="left", fontsize=11, color=style.SUBTITLE_GRAY)
        style.style_axes(ax)
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=min(len(groups), 4),
               fontsize=9, frameon=False, bbox_to_anchor=(0.5, -0.02))
    if title:
        fig.suptitle(title, x=0.06, y=0.99, ha="left", fontsize=15, fontweight="bold")
    fig.text(0.01, 0.005, source or _src(), ha="left", va="bottom",
             fontsize=9, color=style.SOURCE_GRAY)
    fig.tight_layout(rect=(0, 0.04, 1, 0.96))
    from pathlib import Path
    Path(outfile).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(outfile, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(outfile)


def plot_heatmap(df, *, x, y, group=None, title=None, palette=None,
                 outfile=None, value=None, subtitle=None, source=None, **kw):
    """④ 히트맵: x × y 격자에 value(없으면 group을 값으로) 강도 표시."""
    style.apply_house_style()
    fig, ax = style.new_axes(figsize=(10, 6))
    valcol = value or group
    piv = df.pivot_table(index=y, columns=x, values=valcol, aggfunc="sum").fillna(0)
    im = ax.imshow(piv.values, aspect="auto", cmap="YlGnBu")
    ax.set_xticks(range(len(piv.columns)))
    ax.set_xticklabels(piv.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=9)
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02, label=valcol)
    style.style_axes(ax)
    ax.spines["left"].set_visible(False); ax.spines["bottom"].set_visible(False)
    if title:
        fig.suptitle(title, x=0.06, y=0.97, ha="left", fontsize=15, fontweight="bold")
    style.add_source(ax, source or _src())
    return style.save_fig(fig, outfile)


def plot_violin(df, *, x, y, group=None, title=None, palette=None,
                outfile=None, subtitle=None, source=None, **kw):
    """⑤ 바이올린: x(범주) 별 y(연속값) 분포."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    cats = sorted(df[x].unique())
    data = [df[df[x] == c][y].dropna().values for c in cats]
    parts = ax.violinplot(data, showmeans=True, showextrema=False)
    colors = _resolve_colors(cats, palette)
    for pc, col in zip(parts["bodies"], colors):
        pc.set_facecolor(col); pc.set_alpha(0.7); pc.set_edgecolor("white")
    ax.set_xticks(range(1, len(cats) + 1)); ax.set_xticklabels(cats)
    ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "바이올린 플롯", subtitle=subtitle,
                   legend=False, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_box(df, *, x, y, group=None, title=None, palette=None,
             outfile=None, subtitle=None, source=None, **kw):
    """⑥ 박스플롯: x(범주) 별 y(연속값) 사분위 분포."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    cats = sorted(df[x].unique())
    data = [df[df[x] == c][y].dropna().values for c in cats]
    bp = ax.boxplot(data, patch_artist=True, widths=0.6,
                    medianprops=dict(color="#333333", linewidth=1.4))
    colors = _resolve_colors(cats, palette)
    for patch, col in zip(bp["boxes"], colors):
        patch.set_facecolor(col); patch.set_alpha(0.6); patch.set_edgecolor("#4D4D4D")
    ax.set_xticklabels(cats); ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "박스플롯", subtitle=subtitle,
                   legend=False, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_scatter(df, *, x, y, group=None, title=None, palette=None,
                 outfile=None, size=None, subtitle=None, source=None, **kw):
    """⑦ 산점도(+버블): x × y, group으로 색, size로 버블 크기(옵션)."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    if group:
        groups = sorted(df[group].unique())
        colors = _resolve_colors(groups, palette)
        for g, col in zip(groups, colors):
            sub = df[df[group] == g]
            s = (sub[size] / sub[size].max() * 240 + 12) if size else 28
            ax.scatter(sub[x], sub[y], s=s, color=col, alpha=0.6,
                       edgecolor="white", linewidth=0.5, label=str(g))
    else:
        s = (df[size] / df[size].max() * 240 + 12) if size else 28
        ax.scatter(df[x], df[y], s=s, color=style.CLUSTER_PALETTE[0], alpha=0.6,
                   edgecolor="white", linewidth=0.5)
    ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "산점도", subtitle=subtitle,
                   source=source or _src())
    return style.save_fig(fig, outfile)


def plot_diverging_bar(df, *, x, y, group=None, title=None, palette=None,
                       outfile=None, subtitle=None, source=None, **kw):
    """⑧ 발산형/분할 막대: y가 양/음으로 0을 기준으로 좌우(상하) 분할.
    예) 전기 대비 증감, 평균 대비 편차 등."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    d = df.sort_values(y)
    colors = [style.COUNTRY_COLORS.get("한국", "#1F6FB2") if v >= 0
              else style.COUNTRY_COLORS.get("중국", "#C23B3B") for v in d[y]]
    ax.barh(d[x].astype(str), d[y], color=colors, alpha=0.85)
    ax.axvline(0, color="#4D4D4D", linewidth=1.0)
    ax.set_xlabel(y); ax.set_ylabel(x)
    style.finalize(ax, title=title or "발산형 분할 막대", subtitle=subtitle,
                   legend=False, source=source or _src())
    return style.save_fig(fig, outfile)


# ======================================================================
# 트랙 A — 행정용 기본 차트
# ======================================================================
def plot_bar(df, *, x, y, group=None, title=None, palette=None,
             outfile=None, subtitle=None, source=None, **kw):
    """세로 막대."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    s = df.groupby(x)[y].sum()
    ax.bar(s.index.astype(str), s.values, color=style.CLUSTER_PALETTE[0], alpha=0.9)
    ax.set_xlabel(x); ax.set_ylabel(y)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    style.finalize(ax, title=title or "세로 막대", subtitle=subtitle,
                   legend=False, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_grouped_bar(df, *, x, y, group=None, title=None, palette=None,
                     outfile=None, subtitle=None, source=None, **kw):
    """묶음 막대."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    piv = df.pivot_table(index=x, columns=group, values=y, aggfunc="sum").fillna(0)
    cats = list(piv.index); groups = list(piv.columns)
    colors = _resolve_colors(groups, palette)
    width = 0.8 / max(len(groups), 1)
    xpos = np.arange(len(cats))
    for i, g in enumerate(groups):
        ax.bar(xpos + i * width, piv[g].values, width=width, label=str(g),
               color=colors[i], alpha=0.9)
    ax.set_xticks(xpos + width * (len(groups) - 1) / 2)
    ax.set_xticklabels(cats, rotation=30, ha="right")
    ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "묶음 막대", subtitle=subtitle, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_stacked_bar(df, *, x, y, group=None, title=None, palette=None,
                     outfile=None, subtitle=None, source=None, **kw):
    """누적 막대."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    piv = df.pivot_table(index=x, columns=group, values=y, aggfunc="sum").fillna(0)
    cats = list(piv.index); groups = list(piv.columns)
    colors = _resolve_colors(groups, palette)
    bottom = np.zeros(len(cats))
    for i, g in enumerate(groups):
        ax.bar(cats, piv[g].values, bottom=bottom, label=str(g), color=colors[i], alpha=0.9)
        bottom += piv[g].values
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "누적 막대", subtitle=subtitle, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_pct_stacked_bar(df, *, x, y, group=None, title=None, palette=None,
                         outfile=None, subtitle=None, source=None, **kw):
    """100% 누적 막대(구성비)."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    piv = df.pivot_table(index=x, columns=group, values=y, aggfunc="sum").fillna(0)
    pct = piv.div(piv.sum(axis=1).replace(0, np.nan), axis=0) * 100
    cats = list(pct.index); groups = list(pct.columns)
    colors = _resolve_colors(groups, palette)
    bottom = np.zeros(len(cats))
    for i, g in enumerate(groups):
        ax.bar(cats, pct[g].values, bottom=bottom, label=str(g), color=colors[i], alpha=0.9)
        bottom += np.nan_to_num(pct[g].values)
    ax.set_ylim(0, 100)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.set_xlabel(x); ax.set_ylabel("비중(%)")
    style.finalize(ax, title=title or "100% 누적 막대", subtitle=subtitle, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_barh_ranked(df, *, x, y, group=None, title=None, palette=None,
                     outfile=None, top=None, subtitle=None, source=None, **kw):
    """가로 막대(순위): y 기준 내림차순."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    s = df.groupby(x)[y].sum().sort_values(ascending=True)
    if top:
        s = s.tail(int(top))
    ax.barh(s.index.astype(str), s.values, color=style.CLUSTER_PALETTE[2], alpha=0.9)
    ax.set_xlabel(y); ax.set_ylabel(x)
    style.finalize(ax, title=title or "가로 순위 막대", subtitle=subtitle,
                   legend=False, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_line(df, *, x, y, group=None, title=None, palette=None,
              outfile=None, subtitle=None, source=None, **kw):
    """단일 선."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    s = df.groupby(x)[y].sum()
    ax.plot(s.index, s.values, color=style.CLUSTER_PALETTE[0], linewidth=2.0)
    ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "선 그래프", subtitle=subtitle,
                   legend=False, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_multiline(df, *, x, y, group=None, title=None, palette=None,
                   outfile=None, subtitle=None, source=None, **kw):
    """다중 선: group 별 선."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    groups = sorted(df[group].unique())
    colors = _resolve_colors(groups, palette)
    for g, col in zip(groups, colors):
        s = df[df[group] == g].groupby(x)[y].sum()
        ax.plot(s.index, s.values, color=col, linewidth=1.8, label=str(g))
    ax.set_xlabel(x); ax.set_ylabel(y)
    style.finalize(ax, title=title or "다중 선", subtitle=subtitle, source=source or _src())
    return style.save_fig(fig, outfile)


def plot_donut(df, *, x, y, group=None, title=None, palette=None,
               outfile=None, subtitle=None, source=None, **kw):
    """파이/도넛: x 범주별 y 합계 비중."""
    style.apply_house_style()
    fig, ax = style.new_axes(figsize=(8, 6))
    s = df.groupby(x)[y].sum()
    colors = _resolve_colors(list(s.index), palette)
    wedges, _texts, autotexts = ax.pie(
        s.values, labels=s.index.astype(str), colors=colors, autopct="%1.0f%%",
        pctdistance=0.78, wedgeprops=dict(width=0.42, edgecolor="white"))
    ax.set(aspect="equal")
    if title:
        fig.suptitle(title, x=0.06, y=0.97, ha="left", fontsize=15, fontweight="bold")
    style.add_source(ax, source or _src())
    return style.save_fig(fig, outfile)


def plot_combo(df, *, x, y, group=None, title=None, palette=None,
               outfile=None, y2=None, subtitle=None, source=None, **kw):
    """콤보(막대+선): 막대 y + 보조축 선 y2."""
    style.apply_house_style()
    fig, ax = style.new_axes()
    g = df.groupby(x)
    bar = g[y].sum()
    ax.bar(bar.index.astype(str), bar.values, color=style.CLUSTER_PALETTE[0],
           alpha=0.85, label=y)
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.set_ylabel(y)
    if y2:
        ax2 = ax.twinx()
        line = g[y2].mean()
        ax2.plot(line.index.astype(str), line.values, color=style.COUNTRY_COLORS["미국"],
                 linewidth=2.2, marker="o", label=y2)
        ax2.set_ylabel(y2)
        ax2.spines["top"].set_visible(False)
    style.style_axes(ax)
    if title:
        fig.suptitle(title, x=0.06, y=0.97, ha="left", fontsize=15, fontweight="bold")
    style.add_source(ax, source or _src())
    return style.save_fig(fig, outfile)


# ======================================================================
# 내부 헬퍼
# ======================================================================
def _src():
    return "출처: KISTI 강의용 샘플 데이터(시드 고정)"


def _resolve_colors(keys, palette=None):
    """국가명이면 고정색, 아니면 클러스터 팔레트 순환."""
    if palette and isinstance(palette, (list, tuple)):
        return [palette[i % len(palette)] for i in range(len(keys))]
    out = []
    for i, k in enumerate(keys):
        if str(k) in style.COUNTRY_COLORS:
            out.append(style.COUNTRY_COLORS[str(k)])
        else:
            out.append(style.CLUSTER_PALETTE[i % len(style.CLUSTER_PALETTE)])
    return out


# 함수 이름 → 함수 매핑(run_report.py 가 config의 func 문자열로 호출)
REGISTRY = {
    # 트랙 B
    "plot_stacked_area": plot_stacked_area,
    "plot_pct_stacked_area": plot_pct_stacked_area,
    "plot_facet_line": plot_facet_line,
    "plot_heatmap": plot_heatmap,
    "plot_violin": plot_violin,
    "plot_box": plot_box,
    "plot_scatter": plot_scatter,
    "plot_diverging_bar": plot_diverging_bar,
    # 트랙 A
    "plot_bar": plot_bar,
    "plot_grouped_bar": plot_grouped_bar,
    "plot_stacked_bar": plot_stacked_bar,
    "plot_pct_stacked_bar": plot_pct_stacked_bar,
    "plot_barh_ranked": plot_barh_ranked,
    "plot_line": plot_line,
    "plot_multiline": plot_multiline,
    "plot_donut": plot_donut,
    "plot_combo": plot_combo,
}
