from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os  # provides ways to access the Operating System and allows us to read the environment variables
import re

load_dotenv()

app = Flask(__name__)

uri = os.getenv('URI')
user = os.getenv("USERNAME1")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")

# Zwraca Pracowników firmy
def get_workers(tx, sort='',sortType='', filtr='', filtrType=''):
    query = "MATCH (m:Employee) RETURN m"
    if(sortType == 'asc'):
        if(sort == 'name'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.name"
        elif(sort == 'surname'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.surname"
        elif(sort == 'position'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.position"
    if(sortType == 'desc'):        
        if(sort == 'name'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.name DESC"
        elif(sort == 'surname'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.surname DESC"
        elif(sort == 'position'):
            query = "MATCH (m:Employee) RETURN m ORDER BY m.position DESC"    
    if(filtrType == 'name'):
        query = f"MATCH (m:Employee) WHERE m.name CONTAINS '{filtr}' RETURN m"          
    if(filtrType == 'surname'):
        query = f"MATCH (m:Employee) WHERE m.surname CONTAINS '{filtr}' RETURN m"   
    if(filtrType == 'position'):
        query = f"MATCH (m:Employee) WHERE m.position CONTAINS '{filtr}' RETURN m"                 
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return workers


@app.route('/employees', methods=['GET'])
def get_workers_route():
    args = request.args
    sort = args.get("sort")
    sortType = args.get("sortType")
    filtr = args.get("filtr")
    filtrType = args.get("filtrType")
    with driver.session() as session:
        workers = session.execute_read(get_workers, sort,sortType, filtr, filtrType)
    # add filtring and sorting
    response = {'workers': workers}
    return jsonify(response)



# Zwraca pracowników danego menadzera
def get_workers_subordinates(tx, name, surname):
    query = f"""MATCH (p:Employee), (p1:Employee {{name:'{name}', surname:'{surname}'}})-[r]-(d) 
               WHERE NOT (p)-[:MANAGES]-(:Department) 
               AND (p)-[:WORKS_IN]-(:Department {{name:d.name}}) 
               RETURN p"""
    results = tx.run(query).data()
    workers = [{'name': result['p']['name'],
               'surname': result['p']['surname']} for result in results[:len(results)//2]]
    return workers

@app.route('/employees/<person>/subordinates', methods=['GET'])
def get_workers_subordinates_route(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
    with driver.session() as session:
        workers = session.read_transaction(get_workers_subordinates, name, surname)
    response = {'workers': workers}
    return jsonify(response)



#Zwraca wszystkie Deprartamenty
def get_departments(tx, sort='', sortType='', filtr='', filtrType=''):
    # zwraca Departamenty
    query = "MATCH (m:Department) RETURN m"
    if(sortType == 'asc'):
        if(sort == 'name'):
            query = "MATCH (m:Department) RETURN m ORDER BY m.name"
        if(sort == 'numberOfEmployees'):
            query = f"""MATCH 
               (m:Employee)-[r:WORKS_IN]-(d:Department)
               RETURN d.name ORDER BY count(m)"""    
    if(sortType == 'desc'):        
        if(sort == 'name'):
            query = "MATCH (m:Department) RETURN m ORDER BY m.name DESC"
        if(sort == 'numberOfEmployees'):
            query = f"""MATCH 
               (m:Employee)-[r:WORKS_IN]-(d:Department)
               RETURN d.name ORDER BY count(m) DESC"""    
    if(filtrType == 'name'):
        query = f"MATCH (m:Department) WHERE m.name CONTAINS '{filtr}' RETURN m"          
    if(filtrType == 'numberOfEmployees'):
        query = f"""MATCH 
               (m:Employee)-[r:WORKS_IN]-(d:Department)
               WHERE count(m) = '{filtr}'               
               RETURN d.name"""     
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
    query = f"""MATCH 
               (m:Employee {{name:'{name}', surname:'{surname}'}})-[r:WORKS_IN]-(d:Department), 
               (m1:Employee)-[r1:MANAGES]-(d1:Department {{name:d.name}}),
               (m2:Employee)-[r2:WORKS_IN]-(d2:Department {{name:d.name}}) 
               RETURN d.name AS name, m1.name AS Manager, count(m2) AS Number_of_Employees"""
    result = tx.run(query).data()
    departments = [{'Name': result[0]['name'], 'Manager': result[0]['Manager'], 'Number of employees':result[0]['Number_of_Employees']+1 }]
    return departments


@app.route('/employees/<string:person>/department', methods=['GET'])
def get_departments_route_from_employee(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
    with driver.session() as session:
        departments = session.read_transaction(get_departments_from_employee, name, surname)
    response = {'department': departments}
    return jsonify(response)



# Zwraca pracowników danego departamentu
def get_departments_employees(tx, name):
    query = f"MATCH (m:Employee)-[r:WORKS_IN]-(d:Department {{name:'{name}'}}) RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'], 'surname': result['m']['surname'], 'position': result['m']['position']} for result in results]
    return workers


@app.route('/departments/<string:name>/employees', methods=['GET'])
def get_departments_route_from_department(name):
    with driver.session() as session:
        workers = session.execute_read(get_departments_employees, name)
    response = {'workers': workers}
    return jsonify(response)



# Tworzy pracownika
def add_worker(tx, name, surname,position, department):
    query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' AND m.position='{position}' RETURN m"
    result = tx.run(query, name=name).data()
    if not result: 
        query = f"CREATE ({name}:Employee {{name:'{name}', surname:'{surname}', position:'{position}'}})"
        query2 = f"MATCH (a:Employee),(b:Department) WHERE a.name = '{name}' AND a.surname = '{surname}' AND b.name = '{department}' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)"
        tx.run(query, name=name, surname=surname, position=position)
        tx.run(query2, name=name, surname=surname, department=department)
    else:
        return 'Person exist'    


@app.route('/employees', methods=['POST'])
def add_worker_route():
    name = request.form['name']
    surname = request.form['surname']
    position = request.form['position']
    department = request.form['department']
    if(name == '' or surname == '' or position == '' or department == ''):
        return 'Not a complete request'

    with driver.session() as session:
        session.execute_write(add_worker, name, surname, position, department)

    response = {'status': 'success'}
    return jsonify(response)



# Updatuje Pracownika
def update_worker(tx, name, surname, new_name, new_surname, new_department, new_position):
    query = f"MATCH (m:Employee)-[r]-(d:Department) WHERE m.name='{name}' AND m.surname='{surname}' RETURN m,d,r"
    result = tx.run(query, name=name, surname=surname).data()
    print(result)
    print(result[1]['r'][1])
    if not result:
        return None
    else:
        query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' SET m.name='{new_name}', m.surname='{new_surname}', m.position='${new_position}'"
        query1 = f"MATCH (m:Employee {{name: '{name}', surname: '{surname}'}})-[r:WORKS_IN]->(d:Department {{name:'{result[0]['d']['name']}'}}) DELETE r"
        query2 = f"""MATCH (a:Employee),(b:Department) WHERE a.name = '{name}' AND a.surname = '{surname}' AND b.name = '{new_department}' CREATE (a)-[r:WORKS_IN]->(b) RETURN type(r)"""
        tx.run(query, name=name,surname=surname, new_name=new_name, new_surname=new_surname, new_position=new_position)
        tx.run(query1, name=name,surname=surname)
        tx.run(query2, name=name,surname=surname, new_department=new_department)
        return {'name': new_name, 'surname': new_surname, 'position':new_position, 'New department': new_department}


@app.route('/employees/<string:person>', methods=['PUT'])
def update_worker_route(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
    new_name = request.form['name']
    new_surname = request.form['surname']
    new_department = request.form['department']
    new_position = request.form['position']

    with driver.session() as session:
        worker = session.write_transaction(
            update_worker,name, surname, new_name, new_surname, new_department, new_position)

    if not worker:
        response = {'message': 'Employee not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)



# Usuwa pracownika
def delete_worker(tx, name, surname):
    query = f"MATCH (m:Employee)-[r]-(d:Department) WHERE m.name='{name}' AND m.surname='{surname}' RETURN m,d,r"
    result = tx.run(query, name=name, surname=surname).data()
    # jeżeli menadzer departamentu nalezy dodać nowego menadzera lub usunąć departament
    if not result:
        return None
    else:
        query = f"MATCH (m:Employee) WHERE m.name='{name}' AND m.surname='{surname}' DETACH DELETE m"
        tx.run(query, name=name, surname=surname)
        if(len(result) > 1):
            query = f"MATCH (m:Employee)-[r:WORKS_IN]-(d:Department {{name:'{result[0]['d']['name']}'}}) RETURN m"
            results = tx.run(query).data()
            if(len(results) == 0):
                query = f"MATCH (d:Department) WHERE d.name='{result[0]['d']['name']}' DETACH DELETE d"
                tx.run(query, name=name, surname=surname)
            workers = [{'name': result['m']['name'], 'surname': result['m']['surname'], 'position': result['m']['position']} for result in results]
            query2 = f"""MATCH (a:Employee),(b:Department) WHERE a.name = '{workers[0]['name']}' AND a.surname = '{workers[0]['surname']}' AND b.name = '{result[0]['d']['name']}' CREATE (a)-[r:MANAGES]->(b) RETURN type(r)"""
            tx.run(query2)
        return {'name': name, 'surname':surname}


@app.route('/employees/<string:person>', methods=['DELETE'])
def delete_worker_route(person):
    person1 = re.split('(?<=.)(?=[A-Z])', person)
    name = person1[0]
    surname = person1[1]
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
