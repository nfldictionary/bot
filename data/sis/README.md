# Local SIS Data

이 디렉터리는 로컬 전용 SIS seasonal data 작업 공간입니다.

- `raw/{season}/`: 원본 JSON
- `parquet/{season}/`: parquet 출력
- `reports/`: 시각적 검증용 HTML 리포트
- `stories/{season}/`: 콘텐츠형 HTML 번들
- `manifest.json`: 마지막 동기화/빌드/검증 요약

`raw/`와 `parquet/`는 `.gitignore`에 포함되어 있어 로컬에서만 유지됩니다.
