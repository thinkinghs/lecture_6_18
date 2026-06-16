# CLAUDE.md — KISTI 차트 프로그램 프로젝트 규칙

이 파일은 Claude Code가 **세션 시작 때마다 자동으로 읽는 프로젝트 규칙서**입니다.
여기에 규칙을 못 박아 두면, 누가 언제 어떤 프롬프트를 던져도 **코드의 룩·구조가
갈리지 않습니다.** (이 파일이 표준 코드 폴백이 즉시 호환되는 비결입니다.)

---

## 0. 이 프로젝트가 하는 일
연구/행정 데이터를 받아 **보고서용 차트(PNG)** 를 일관된 스타일로 자동 생성한다.

## 1. 폴더·파일 규칙 (반드시 지킬 것)
- 차트 **이미지 저장 경로**: `output/`
- 차트 **이미지 파일명**: `chart_<id>.png` (예: `output/chart_area.png`)
- **공유 스타일 자산**: `charts/style.py`  → **★ 절대 수정 금지 ★** (읽기 전용처럼 취급)
- **차트 함수 라이브러리**: `charts/report_charts.py`  → 차트 추가·변경은 **여기서만**
- **얇은 매핑 설정**: `config.yaml`  → 어떤 CSV·어떤 열이 x/y/group·어떤 차트·제목
- **검증·파이프라인**: `validate.py`, `run_report.py`

## 2. 모든 차트 함수의 통일 시그니처 (예외 없음)
```python
def plot_xxx(df, *, x, y, group=None, title=None, palette=None, outfile=None, **kw):
    ...
    return outfile   # 저장된 PNG 경로를 반환
```
- 열 이름은 **하드코딩 금지** — 반드시 `x`, `y`, `group` 등 **파라미터**로 받는다.
- 차트별로 추가 인자가 필요하면 `**kw` 로 받되, **위 5개 핵심 인자 형태는 고정**한다.

## 3. 스타일 규칙 (charts/style.py 만 사용)
- 모든 차트는 `charts/style.py` 의 함수만 써서 룩을 적용한다.
  - `apply_house_style()` / `new_axes()` / `finalize(...)` / `save_fig(fig, outfile, dpi=300)`
- **출력은 PNG 300dpi 단일** — 인터랙티브 HTML 트윈을 만들지 않는다.
  (인터랙티브는 블록 2의 Claude.ai 영역. 여기 표준 코드는 인쇄용 PNG.)
- 국가 고정색·클러스터 팔레트·맑은 고딕·마이너스 기호 보정·"출처:" 라인은
  모두 `style.py` 가 책임진다. **차트 함수에서 색·폰트를 다시 정의하지 않는다.**

## 4. 작업 방식
- 새 차트·변형은 `report_charts.py` 와 `config.yaml` 에서만 한다.
- `charts/style.py` 를 바꿔야 할 것 같으면 — **멈추고** 다른 방법을 찾는다(공유 자산).
- 큰 변경 전에는 **plan mode(Shift+Tab 두 번)** 로 계획을 먼저 보여주고 승인받는다.

## 5. 환경
- OS Windows / Python 3.13 / 패키지 관리 **uv**(venv 아님).
- 실행은 항상 `uv run ...` 로 한다 (예: `uv run run_report.py`).
