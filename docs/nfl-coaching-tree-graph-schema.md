# NFL Coaching Tree Graph Schema

## Nodes

- `Coach`
  - `coachId`
  - `coachSlug`
  - `coachName`
  - `profileUrl`
  - `jobTitle`
  - `currentTeamName`
  - `birthPlace`
  - `alumniOf`

- `Franchise`
  - `franchiseId`
  - `teamSlug`
  - `teamName`
  - `teamUrl`

## Relationships

- `(:Coach)-[:WORKED_UNDER]->(:Coach)`
- `(:Coach)-[:LINEAGE_OF]->(:Coach)`
- `(:Coach)-[:HELD_ROLE_AT]->(:Franchise)` via `staff_tenures.jsonl`

## Source-backed files

- `canonical/coaches.jsonl`
- `canonical/franchises.jsonl`
- `canonical/team_aliases.jsonl`
- `canonical/staff_tenures.jsonl`
- `canonical/worked_under_edges.jsonl`
- `canonical/lineage_edges.jsonl`
- `canonical/sources.jsonl`
- `canonical/claims.jsonl`
