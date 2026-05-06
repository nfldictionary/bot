CREATE CONSTRAINT coach_id_unique IF NOT EXISTS
FOR (c:Coach)
REQUIRE c.coachId IS UNIQUE;

CREATE CONSTRAINT franchise_id_unique IF NOT EXISTS
FOR (f:Franchise)
REQUIRE f.franchiseId IS UNIQUE;
