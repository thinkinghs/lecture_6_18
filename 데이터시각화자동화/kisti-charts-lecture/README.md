# KISTI 데이터 시각화 자동화 — 실습 패키지

KISTI 직원 대상 "데이터 시각화 자동화" 실습 강의 자료 일습입니다.
강의안 + 샘플 데이터 + 실제로 동작하는 표준 코드 + 인터랙티브 템플릿 + 적응 정답본으로 구성됩니다.

> 기준: 2026년 6월 · Windows · Python 3.13 · uv · Claude Code 2.1.x(기본 Opus 4.8) · Claude.ai

---

## 📁 폴더 구성

```
kisti-charts-lecture/
├─ 강의안.md                  # 메인 강의안(한국어, 실습 step-by-step) ★여기부터 읽기★
├─ README.md                  # (이 문서) 구성·실행법
│
├─ data/                      # 샘플 데이터(시드 고정·재현 가능)
│  ├─ make_data.py            #   - 데이터 생성기(python make_data.py 로 재생성)
│  ├─ trackA_admin.csv        #   - 트랙 A(행정): 부서×월×예산·인력·과제   [블록 2]
│  ├─ trackB_aging.csv        #   - 트랙 B(연구) 집계본: 국가×클러스터×연도×논문수 [블록 3·4]
│  ├─ trackB_papers.csv       #   - 트랙 B 논문 단위: 피인용·공동연구자·국제공동연구
│  ├─ trackB_aging_next.csv   #   - "다음 호" 재생산용(같은 스키마)
│  ├─ trackB_aging_dirty.csv  #   - 일부러 깨진 데이터(검증 실습용)
│  └─ trackC_aging.csv        #   - 적응 실습용(열 이름이 다른 통제된 차이)  [블록 4]
│
├─ code/                      # 배포용 표준 코드(실제 동작 검증 완료)
│  ├─ CLAUDE.md               #   - 프로젝트 규칙서(블록 3·4의 앵커)
│  ├─ config.yaml             #   - 얇은 매핑 층(어떤 CSV·어떤 열·어떤 차트)
│  ├─ validate.py             #   - 데이터 검증(결측·이상치·스키마·도메인 규칙)
│  ├─ run_report.py           #   - 무인 실행 파이프라인(검증→차트 일괄)
│  ├─ charts/
│  │  ├─ style.py             #   - ★공유 스타일 자산(수정 금지)★
│  │  └─ report_charts.py     #   - 표준 차트 함수 라이브러리(①~⑧ + 트랙 A 기본)
│  ├─ output/                 #   - 실행 산출물 예시(검증 완료된 PNG 8종 + 리포트)
│  └─ answer_key/             #   - 블록 4 적응 실습 정답본(폴백용)
│     ├─ config_trackC.yaml
│     ├─ report_charts_trackC_addition.py
│     └─ NOTES.md
│
└─ templates/                 # 블록 2 전용 인터랙티브 Plotly HTML
   ├─ make_templates.py       #   - HTML 생성기(데이터 교체 재렌더용)
   └─ admin_report_template.html  # - 자체완결 인터랙티브 대시보드(브라우저로 열기)
```

> 인터랙티브 HTML은 **블록 2 전용**입니다. 블록 3·4 표준 코드의 산출물은 **PNG 300dpi 단일**입니다.
> (각 도구의 강점: matplotlib=인쇄용 PNG / Plotly=인터랙티브.)

---

## ▶ 빠른 실행 (강사/검증용)
① uv 설치 (PowerShell에 그대로 붙여넣기)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex“

  설치 후 PowerShell 닫았다 다시 열고 확인
uv --version

② 프로젝트 생성 후 이동
cd c:/
mkdir kisti_ai_study
cd kisti_ai_study
uv init kisti-charts
cd kisti-charts

③ Python 3.13 설치·고정
uv python install 3.13
uv python pin 3.13


④ 라이브러리 추가 
uv add pandas matplotlib seaborn plotly pyyaml

uv run python -c "import pandas, matplotlib, seaborn, plotly, yaml; print('ok')"



# 2) 샘플 데이터 재생성(선택, 시드 고정이라 항상 같은 결과)
uv run python data\make_data.py

# 3) 표준 파이프라인 실행 (code 폴더에서)
cd code
uv run run_report.py                                  # 정상본 → 차트 8종 + 검증 통과
uv run run_report.py --data ..\data\trackB_aging_dirty.csv   # 깨진 데이터 → 검증 실패·중단
uv run run_report.py --data ..\data\trackB_aging_next.csv    # 다음 호 → 동일 형식 재생산
uv run run_report.py --config answer_key\config_trackC.yaml  # 적응 정답본(롤리팝 추가 후)

# 4) 블록 2 인터랙티브 템플릿 생성/열기
cd ..\templates
uv run python make_templates.py
start admin_report_template.html
```

> ※ 위 경로는 프로젝트 루트 기준 예시입니다. `code/config.yaml` 의 데이터 경로(`../data/...`)는
> `code/` 폴더에서 실행하는 것을 전제로 합니다.

---

## 🎨 하우스 스타일 (style.py 에 고정)
흰 배경 / 위·오른쪽 축선 제거 / 가로 그리드만 옅게 / 제목 좌측 정렬 + 회색 부제 /
범례 위치 통일 / 국가 고정색(**한국 #1F6FB2 · 미국 #E1812C · 일본 #3C8C5A · 중국 #C23B3B**) /
클러스터 8색 정성 팔레트 / 맑은 고딕(Windows) + 마이너스 기호 보정 / figure 크기 통일·**300dpi** /
하단 "출처:" 라인.

> `charts/style.py` 는 **공유 자산이라 수정하지 않습니다.** 차트 변경·추가는
> `report_charts.py` 와 `config.yaml` 에서만 합니다. 이로써 어떤 데이터로 적응해도 룩이 유지됩니다.

## 🔤 폰트 안내
표준 코드는 Windows의 **맑은 고딕(Malgun Gothic)** 을 우선 사용하고, 없으면
AppleGothic→NanumGothic→Noto Sans CJK 순으로 안전하게 폴백합니다(한글·마이너스 기호 깨짐 방지).
