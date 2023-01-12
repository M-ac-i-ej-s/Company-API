CREATE (Grzegorz:Employee {name:"Grzegorz", surname: "Pasternak", position:"UI/UX"})
CREATE (Mariusz:Employee {name:"Mariusz", surname: "Padzianowski", position:"Tester"})
CREATE (Szymon:Employee {name:"Szymon", surname: "Kalinowski", position:"Fullstack"})
CREATE (Matylda:Employee {name:"Matylda", surname: "Szymańska", position:"Recruiter"})
CREATE (Marysia:Employee {name:"Marysia", surname: "Szczyrk", position:"Intern"})
CREATE (HR:Department {name:"HR"})
CREATE (IT:Department {name:"IT"})

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Grzegorz' AND b.name = 'IT'
CREATE (a)-[r:WORKS_IN]->(b)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Mariusz' AND b.name = 'IT'
CREATE (a)-[r:WORKS_IN]->(b)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Szymon' AND b.name = 'IT'
CREATE (a)-[r:WORKS_IN]->(b)<-[:MANAGES]-(a)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Matylda' AND b.name = 'HR'
CREATE (a)-[r:WORKS_IN]->(b)<-[:MANAGES]-(a)
RETURN type(r)

MATCH
  (a:Employee),
  (b:Department)
WHERE a.name = 'Marysia' AND b.name = 'HR'
CREATE (a)-[r:WORKS_IN]->(b)
RETURN type(r)