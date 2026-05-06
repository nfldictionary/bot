# NFL Coaching Tree Cypher Examples

```cypher
MATCH (c:Coach)
RETURN c.coachName
ORDER BY c.coachName
LIMIT 25;
```

```cypher
MATCH (child:Coach)-[:WORKED_UNDER]->(mentor:Coach)
RETURN child.coachName, mentor.coachName
ORDER BY mentor.coachName, child.coachName
LIMIT 25;
```

```cypher
MATCH (c:Coach)-[r:HELD_ROLE_AT]->(f:Franchise)
RETURN c.coachName, f.teamName, r.year, r.roles
ORDER BY r.year DESC
LIMIT 25;
```
