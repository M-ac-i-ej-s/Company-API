from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os  # provides ways to access the Operating System and allows us to read the environment variables

load_dotenv()

app = Flask(__name__)

uri = os.getenv('URI')
user = os.getenv("USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")

# Zwraca Pracowników firmy
def get_workers(tx):
    query = "MATCH (m:Employee) RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return workers


@app.route('/employees', methods=['GET'])
def get_workers_route():
    with driver.session() as session:
        workers = session.execute_read(get_workers)
    # add filtring and sorting
    response = {'workers': workers}
    return jsonify(response)



# Zwraca pracowników danego menadzera
def get_workers_subordinates(tx, name, surname):
    query = """MATCH (p:Employee), (p1:Employee {name:$name, surname:$surname})-[r]-(d) 
               WHERE NOT (p)-[:MANAGES]-(:Department) 
               AND (p)-[:WORKS_IN]-(:Department {name:d.name}) 
               RETURN p"""
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return workers

@app.route('/employees/<string:name>_<string:surname>/subordinates', methods=['GET'])
def get_workers_subordinates_route(name, surname):
    with driver.session() as session:
        workers = session.read_transaction(get_workers_subordinates, name, surname)
    response = {'workers': workers}
    return jsonify(response)



#Zwraca wszystkie Deprartamenty
def get_departments(tx):
    # zwraca Departamenty
    query = "MATCH (m:Departments) RETURN m"
    results = tx.run(query).data()
    departments = [{'name': result['m']['name']} for result in results]
    return departments


@app.route('/departments', methods=['GET'])
def get_departments_route():
    with driver.session() as session:
        departments = session.read_transaction(get_departments)
    # add filtring and sorting
    response = {'departments': departments}
    return jsonify(response)



#Zwraca informacje o departamencie gdzie pracuje dany pracownik
def get_departments_from_employee(tx, name, surname):
    query = """MATCH 
               (m:Employee {name:$name, surname:$surname})-[r:WORKS_IN]-(d:Department), 
               (m1:Employee)-[r1:MANAGES]-(d1:Department {name:d.name}),
               (m2:Employee)-[r2:WORKS_IN]-(d2:Department {name:d.name}) 
               RETURN d.name AS name, m1.name AS Manager, count(m2) AS Number_of_Employees"""
    result = tx.run(query).data()
    departments = [{'Name': result['name'], 'Manager': result['Manager'], 'Number of employees':result['Number_of_Employees'] }]
    return departments


@app.route('/employees/<string:name>_<string:surname>/department', methods=['GET'])
def get_departments_route(name, surname):
    with driver.session() as session:
        departments = session.read_transaction(get_departments_from_employee, name, surname)
    response = {'departments': departments}
    return jsonify(response)



# Zwraca pracowników danego departamentu
def get_departments_employees(tx, name):
    query = "MATCH (m:Employee)-[r:WORKS_IN]-(d:Department {name:$name}) RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name']} for result in results]
    return workers


@app.route('/departments/<string:name>/employees', methods=['GET'])
def get_departments_route(name):
    with driver.session() as session:
        workers = session.read_transaction(get_departments_employees, name)
    response = {'workers': workers}
    return jsonify(response)



# Tworzy pracownika
def add_worker(tx, name, surname,position, department):
    query = "MATCH (m:Employee) WHERE m.name=$name AND m.surname=$surname AND m.position=$position AND m.department = $department RETURN m"
    result = tx.run(query, name=name).data()
    if not result: 
        query = "CREATE (m:Employee {name: $name, surname: $surname, position: $position})-[:WORKS_IN]->(d:$department)"
        tx.run(query, name=name, surname=surname, position=position, department=department)
    else:
        return 'Person exist'    


@app.route('/employees', methods=['POST'])
def add_worker_route():
    name = request.json['name']
    surname = request.json['surname']
    position = request.json['position']
    department = request.json['department']
    if(name == '' or surname == '' or position == '' or department == ''):
        return 'Not a complete request'

    with driver.session() as session:
        session.write_transaction(add_worker, name, surname, position, department)

    response = {'status': 'success'}
    return jsonify(response)



# Updatuje Pracownika
def update_worker(tx, name, surname, new_name, new_surname, new_department, new_position):
    query = "MATCH (m:Worker) WHERE m.name=$name AND m.surname=$surname RETURN m"
    result = tx.run(query, name=name, surname=surname).data()
    # add department change
    if not result:
        return None
    else:
        query = "MATCH (m:Employee) WHERE m.name=$name AND m.surname=$surname SET m.name=$new_name, m.surname=$new_surname, m.position=$new_position"
        tx.run(query, name=name,surname=surname new_name=new_name, new_surname=new_surname, new_position=new_position)
        return {'name': new_name, 'surname': new_surname, 'position':new_position}


@app.route('/employees/<string:name>_<string:surname>', methods=['PUT'])
def update_worker_route(name, surname):
    new_name = request.json['name']
    new_surname = request.json['surname']
    new_department = request.json['department']
    new_position = request.json['position']

    with driver.session() as session:
        worker = session.write_transaction(
            update_worker, name,surname,  new_name, new_surname, new_department, new_position)

    if not worker:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)



# Usuwa pracownika
def delete_worker(tx, name, surname):
    query = "MATCH (m:Employee) WHERE m.name=$name AND m.surname=$surname RETURN m"
    result = tx.run(query, name=name, surname=surname).data()
    # jeżeli menadzer departamentu nalezy dodać nowego menadzera lub usunąć departament
    if not result:
        return None
    else:
        query = "MATCH (m:Employee) WHERE m.name=$name AND m.surname=$surname DETACH DELETE m"
        tx.run(query, name=name, surname=surname)
        return {'name': name, 'surname':surname}


@app.route('/workers/<string:name>_<string:surname>', methods=['DELETE'])
def delete_worker_route(name, surname):
    with driver.session() as session:
        worker = session.write_transaction(delete_worker, name, surname)

    if not worker:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)


if __name__ == '__main__':
    app.run()
