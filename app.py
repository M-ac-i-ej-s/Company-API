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


def get_workers(tx):
    query = "MATCH (m:Worker) RETURN m"
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


def get_workers_subordinates(tx):
    # zwraca wszystkich którzy są pod nim
    query = "MATCH (m:Worker) RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return workers

@app.route('/employees/<string:name>/subordinates', methods=['GET'])
def get_workers_subordinates_route():
    with driver.session() as session:
        workers = session.read_transaction(get_workers_subordinates)
    # add filtring and sorting
    response = {'workers': workers}
    return jsonify(response)

def get_departments(tx):
    # zwraca Departamenty
    query = "MATCH (m:Departments) RETURN m"
    results = tx.run(query).data()
    workers = [{'name': result['m']['name'],
               'surname': result['m']['surname']} for result in results]
    return workers


@app.route('/departments', methods=['GET'])
def get_departments_route():
    with driver.session() as session:
        workers = session.read_transaction(get_workers_subordinates)
    # add filtring and sorting
    response = {'workers': workers}
    return jsonify(response)


def add_worker(tx, name, surname, department):
    # czy unikalne i czy wszystko podane
    query = "CREATE (m:Worker {name: $name, surname: $surname})-[:WORKS_IN]->($department)"
    tx.run(query, name=name, surname=surname)


@app.route('/employees', methods=['POST'])
def add_worker_route():
    name = request.json['name']
    surname = request.json['surname']

    with driver.session() as session:
        session.write_transaction(add_worker, name, surname)

    response = {'status': 'success'}
    return jsonify(response)


def update_worker(tx, name, new_name, new_surname):
    query = "MATCH (m:Worker) WHERE m.name=$name RETURN m"
    result = tx.run(query, name=name).data()
    # add department change
    if not result:
        return None
    else:
        query = "MATCH (m:Worker) WHERE m.name=$name SET m.name=$new_name, m.surname=$new_surname"
        tx.run(query, name=name, new_name=new_name, new_surname=new_surname)
        return {'name': new_name, 'surname': new_surname}


@app.route('/employees/<string:name>', methods=['PUT'])
def update_worker_route(name):
    new_name = request.json['name']
    new_surname = request.json['surname']

    with driver.session() as session:
        worker = session.write_transaction(
            update_worker, name, new_name, new_surname)

    if not worker:
        response = {'message': 'Movie not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)


def delete_worker(tx, name):
    query = "MATCH (m:Worker) WHERE m.name=$name RETURN m"
    result = tx.run(query, name=name).data()
    # jeżeli menadzer departamentu nalezy dodać nowego menadzera lub usunąć departament
    if not result:
        return None
    else:
        query = "MATCH (m:Worker) WHERE m.name=$name DETACH DELETE m"
        tx.run(query, name=name)
        return {'name': name}


@app.route('/workers/<string:name>', methods=['DELETE'])
def delete_worker_route(name):
    with driver.session() as session:
        worker = session.write_transaction(delete_worker, name)

    if not worker:
        response = {'message': 'Movie not found'}
        return jsonify(response), 404
    else:
        response = {'status': 'success'}
        return jsonify(response)


if __name__ == '__main__':
    app.run()
