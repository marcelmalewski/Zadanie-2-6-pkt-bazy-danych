### Wymagania:
* Plik `.env` z zmiennymi środowiskowymi, np:
```
NEO4J_USERNAME="neo4j"
PASSWORD="test1234"
URI="bolt://localhost:7687"
```
* Neo4j z pluginem `apoc`

### Założenia:
* każdy Departament ma conajmniej jednego managera

### Zadanie + endpoint:
* Zadanie 8 `GET /departments/{departmentUuid}/details`
