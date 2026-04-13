# bot

SIS seasonal data를 로컬에 동기화하고 `parquet`으로 정리하는 간단한 파이프라인입니다.

## 설치

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 로컬 source에서 가져오기

기본값으로 아래 경로의 기존 season feed raw 데이터를 찾습니다.

```text
../nfldictionary/nfldictionary.github.io/data_archive/season_feed/v7
```

전체 시즌을 로컬로 가져오고 parquet/validation까지 한 번에 만들려면:

```bash
python src/main.py all-local --start-year 2016 --end-year 2025
```

생성 결과:

```text
data/sis/
  manifest.json
  raw/{season}/
    team_seasonal.json
    player_seasonal.json
  parquet/{season}/
    team_seasonal.parquet
    player_seasonal.parquet
    player_passing.parquet
    player_rushing.parquet
    player_receiving.parquet
    player_defense.parquet
    _validation.json
```

## API에서 직접 다시 받기

`STATS_API_KEY`가 있으면 원격 fetch도 가능합니다.

```bash
export STATS_API_KEY="YOUR_KEY"
python src/main.py all-fetch --start-year 2016 --end-year 2025
```

기본 base URL은 코드에 들어 있으며, 필요하면 `--base-url`로 덮어쓸 수 있습니다.

## 개별 명령

```bash
python src/main.py sync-local --start-year 2024 --end-year 2025
python src/main.py build --start-year 2024 --end-year 2025
python src/main.py validate --start-year 2024 --end-year 2025
python src/main.py report-html --season 2025
python src/main.py story-html --season 2025
```

샘플 시각화 검증 리포트는 기본적으로 아래 경로에 생성됩니다.

```text
data/sis/reports/sis_validation_2025.html
```

스토리형 HTML 번들은 아래 경로에 생성됩니다.

```text
data/sis/stories/2025/
  index.html
  strategy-atlas.html
  skill-stars.html
  franchise-fingerprints.html
  roster-currents.html
```

## 테스트

```bash
pytest -q
```
