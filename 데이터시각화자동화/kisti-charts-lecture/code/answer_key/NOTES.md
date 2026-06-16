# answer_key — 블록 4 적응 실습 정답본 (강사용)

라이브 적응(시나리오 C)이 깨졌을 때 **즉시 데모를 착지**시키기 위한 정답본입니다.

## 구성
- `config_trackC.yaml` — 트랙 C(열 이름이 다른 데이터)에 맞춘 **정답 매핑/검증 설정**.
- `report_charts_trackC_addition.py` — 적응에 새로 필요한 **롤리팝 차트 함수**(`plot_lollipop`) 스니펫.

## 폴백 적용 방법 (1분)
1. 정답 설정 복사:
   ```powershell
   copy code\answer_key\config_trackC.yaml config_trackC.yaml
   ```
2. `report_charts_trackC_addition.py` 의 `plot_lollipop` 함수를
   `charts\report_charts.py` 의 **REGISTRY 정의 바로 앞**에 붙여넣는다.
3. `charts\report_charts.py` 의 `REGISTRY` 딕셔너리에 한 줄 추가:
   ```python
   "plot_lollipop": plot_lollipop,
   ```
4. 실행:
   ```powershell
   uv run run_report.py --config config_trackC.yaml
   ```
   → 검증 통과 후 `output_trackC/` 에 차트 생성(롤리팝 포함). `style.py` 불변이라 룩 유지.

## 통제된 차이 (의도)
- ⓐ **열 매핑 변경**: country→nation, cluster_id→field_id, cluster_name→field,
  year→pub_year, paper_count→n_papers
- ⓑ **이미 지원하는 계열의 차트 1개 추가**: 롤리팝(막대 계열 변형)

> 목적은 "적응이 완벽히 돌아가는 것"이 아니라 **"적응이 어떻게 생겼나 + 막히면 어떻게 회복하나"**
> 를 학생에게 보여주는 것입니다. 50분 안에 리허설 가능한 경계로 차이를 제한했습니다.
