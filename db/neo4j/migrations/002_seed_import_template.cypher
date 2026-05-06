// Example seed import template.
// Replace file URLs with your exported CSV paths when running bulk import.

LOAD CSV WITH HEADERS FROM 'file:///coaches.csv' AS row
MERGE (c:Coach {coachId: row.coachId})
SET c.coachName = row.coachName,
    c.coachSlug = row.coachSlug,
    c.profileUrl = row.profileUrl;
