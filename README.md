# Company-API

Simple Neo4j + Python(Flask) with Company Management app

GET:

endpoint returns:

/employees - all workers  
/employees/**person**/subordinates - all subordinates of the manager of the department their in  
/departments - all departments with info about their name and the number of employees  
/employees/**person**/department - info about the department person currently is  
/departments/name/employees - all employees of the department

POST:

/employees - creates new employee

Query Parameters - name, surname, position, department

PUT:

/employees/**person** - edits employee

Query Parameters - name, surname, position, department

DELETE:

/employees/**person** - deletes employee

*when employee who manages the department is deleted, new employee will repace him  
*when there are no employees left the department will be deleted  
\*the variable **person** must be written in a pattern **NameSurname**
