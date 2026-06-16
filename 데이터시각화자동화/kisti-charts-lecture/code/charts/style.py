"""
charts/style.py — 공유 하우스 스타일 자산 (★ 수정 금지 ★)

이 파일은 '모든 차트가 같은 룩을 갖도록' 보장하는 단일 진실 원천입니다.
차트를 바꾸거나 추가할 때도 이 파일은 건드리지 않습니다.
(차트 변경·추가는 report_charts.py 와 config.yaml 에서만 합니다.)

제공 기능:
  - apply_house_style()         : matplotlib 전역 스타일 적용(폰트·색·격자 등)
  - COUNTRY_COLORS              : 국가 고정색 dict
  - CLUSTER_PALETTE             : 클러스터 8색 정성 팔레트
  - new_axes(...)               : 통일된 figure/axes 생성
  - finalize(ax, title, ...)    : 제목·부제·범례·출처 라인 통일 적용
  - save_fig(fig, outfile, dpi) : PNG 300dpi 단일 저장 (HTML 트윈 없음)
"""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")  # 화면 없이 PNG 저장
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# ----------------------------------------------------------------------
# 국가 고정색 (하우스 스타일 — 절대 바꾸지 않음)
# ----------------------------------------------------------------------
COUNTRY_COLORS = {
    "한국": "#1F6FB2",
    "미국": "#E1812C",
    "일본": "#3C8C5A",
    "중국": "#C23B3B",
}

# 클러스터 8색 정성 팔레트(색맹 친화·인쇄 안정)
CLUSTER_PALETTE = [
    "#1F6FB2", "#E1812C", "#3C8C5A", "#C23B3B",
    "#8C61C2", "#7B5544", "#D17AB0", "#7F7F7F",
]

GRID_GRAY = "#D9D9D9"
SUBTITLE_GRAY = "#6B6B6B"
SOURCE_GRAY = "#8A8A8A"

# ----------------------------------------------------------------------
# 한글 폰트 — Windows의 '맑은 고딕'을 우선, 없으면 안전하게 폴백
# (데이터 시각화 한글 깨짐/마이너스 기호 깨짐 방지)
# ----------------------------------------------------------------------
_KOREAN_FONT_PREFERENCE = [
    "Malgun Gothic",      # Windows (강의 기본 환경)
    "AppleGothic",        # macOS
    "NanumGothic",        # 나눔폰트 설치 시
    "Noto Sans CJK KR",   # 리눅스/노토
    "Noto Sans CJK JP",
    "DejaVu Sans",        # 최후의 폴백(한글은 깨질 수 있음)
]


def _pick_korean_font() -> str:
    available = {f.name for f in fm.fontManager.ttflist}
    for name in _KOREAN_FONT_PREFERENCE:
        if name in available:
            return name
    return "DejaVu Sans"


def apply_house_style() -> None:
    """matplotlib 전역 스타일을 하우스 스타일로 고정한다."""
    font_name = _pick_korean_font()
    plt.rcParams.update({
        "figure.figsize": (10, 6),     # figure 크기 통일
        "figure.dpi": 110,
        "savefig.dpi": 300,             # 기본 300dpi
        "font.family": font_name,
        "font.size": 12,
        "axes.unicode_minus": False,    # 마이너스 기호 깨짐 보정
        "axes.facecolor": "white",
        "figure.facecolor": "white",
        "axes.edgecolor": "#4D4D4D",
        "axes.linewidth": 0.9,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID_GRAY,
        "grid.linewidth": 0.8,
        "xtick.color": "#4D4D4D",
        "ytick.color": "#4D4D4D",
        "legend.frameon": False,
    })


def new_axes(figsize=(10, 6)):
    """통일된 figure/axes 한 쌍을 만든다."""
    fig, ax = plt.subplots(figsize=figsize)
    return fig, ax


def style_axes(ax) -> None:
    """위·오른쪽 축선 제거 + 가로 그리드만 옅게."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color=GRID_GRAY, linewidth=0.8)
    ax.grid(axis="x", visible=False)


def add_source(ax, source: str = "출처: KISTI 강의용 샘플 데이터(시드 고정)") -> None:
    """그림 하단 왼쪽에 '출처:' 라인을 통일 적용."""
    ax.figure.text(0.01, 0.01, source, ha="left", va="bottom",
                   fontsize=9, color=SOURCE_GRAY)


def finalize(ax, *, title=None, subtitle=None, legend=True,
             source="출처: KISTI 강의용 샘플 데이터(시드 고정)") -> None:
    """제목(좌측 정렬)·회색 부제·범례·출처 라인을 한 번에 통일 적용."""
    style_axes(ax)
    if subtitle:
        ax.set_title(subtitle, loc="left", fontsize=11,
                     color=SUBTITLE_GRAY, pad=6)
    if title:
        ax.figure.suptitle(title, x=0.06, y=0.97, ha="left",
                           fontsize=15, fontweight="bold")
    if legend and ax.get_legend_handles_labels()[0]:
        ax.legend(loc="upper left", fontsize=10, ncol=1)
    add_source(ax, source)


def save_fig(fig, outfile, dpi: int = 300) -> str:
    """PNG 300dpi 단일 저장(HTML 트윈 없음). 폴더 자동 생성."""
    out = Path(outfile)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(out, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(out)


def color_for_country(country: str) -> str:
    return COUNTRY_COLORS.get(country, "#7F7F7F")
