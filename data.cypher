CREATE (e1:Employee {uuid: "1", name: 'Alice', surname: 'Smith'})-[w1:WORKS_IN {position: 'Manager'}]->(d1:Department {uuid: "1", name: 'Marketing'}),
       (e2:Employee {uuid: "2", name: 'Bob', surname: 'Johnson'})-[w2:WORKS_IN {position: 'Manager'}]->(d2:Department {uuid: "2", name: 'Sales'}),
       (e3:Employee {uuid: "3", name: 'Charlie', surname: 'Williams'})-[w3:WORKS_IN {position: 'Manager'}]->(d3:Department {uuid: "3", name: 'Engineering'})

CREATE (e4:Employee {uuid: "4", name: 'Dave', surname: 'Jones'})-[w4:WORKS_IN {position: 'Accountant'}]->(d1),
       (e5:Employee {uuid: "5", name: 'Eve', surname: 'Brown'})-[w5:WORKS_IN {position: 'Salesperson'}]->(d2),
       (e6:Employee {uuid: "6", name: 'Frank', surname: 'Davis'})-[w6:WORKS_IN {position: 'Engineer'}]->(d3),
       (e7:Employee {uuid: "7", name: 'Gina', surname: 'Miller'})-[w7:WORKS_IN {position: 'Marketing Specialist'}]->(d1),
       (e8:Employee {uuid: "8", name: 'Henry', surname: 'Wilson'})-[w8:WORKS_IN {position: 'Sales Manager'}]->(d2),
       (e9:Employee {uuid: "9", name: 'Irene', surname: 'Moore'})-[w9:WORKS_IN {position: 'Software Engineer'}]->(d3),
       (e10:Employee {uuid: "10", name: 'Jake', surname: 'Taylor'})-[w10:WORKS_IN {position: 'Accountant'}]->(d1)

CREATE (e1)-[:MANAGES]->(e2)
CREATE (e1)-[:MANAGES]->(e3)
CREATE (e3)-[:MANAGES]->(e4)
CREATE (e4)-[:MANAGES]->(e5)
CREATE (e5)-[:MANAGES]->(e6)