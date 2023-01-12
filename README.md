# Company-API

Simple Neo4j + Python(Flask) with Company Management app

GET:

endpoint returns:

/employees - all workers
/employees/_person_/subordinates - all subordinates of the manager of the department their in
/departments - all departments with info about their name and the number of employees
/employees/_person_/department - info about the department person currently is  
/departments/name/employees - all employees of the department

POST:

/employees - creates new employee

Query Parameters - name, surname, position, department

PUT:

/employees/_person_ - edits employee

Query Parameters - name, surname, position, department

DELETE:

/employees/_person_ - deletes employee

*when employee who manages the department is deleted, new employee will repace him
*when there are no employees left the department will be deleted
\*the variable _person_ must be written in a pattern _NameSurname_
