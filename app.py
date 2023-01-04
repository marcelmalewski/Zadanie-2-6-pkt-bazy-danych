from flask import Flask, jsonify, request
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

uri = os.getenv('URI')
user = os.getenv("NEO4J_USERNAME")
password = os.getenv("PASSWORD")
driver = GraphDatabase.driver(uri, auth=(user, password), database="neo4j")


def get_employees(tx, name=None, surname=None, position=None, sort_by=None, sort_order=None):
    query = "MATCH (e:Employee)-[w:WORKS_IN]->(d:Department)"

    if name:
        query += f" WHERE e.name = '{name}'"
    if surname:
        query += f" WHERE e.surname = '{surname}'"
    if position:
        query += f" WHERE w.position = '{position}'"

    query += " RETURN e.uuid as uuid, e.name as name, e.surname as surname, w.position as position, " \
             "d.name as department"

    if sort_by == 'name' or sort_by == 'surname':
        query += f" ORDER BY e.{sort_by}"
    elif sort_by == 'position':
        query += " ORDER BY w.position"
    if sort_order:
        query += f" {sort_order}"

    results = tx.run(query).data()
    employees = [
        {'uuid': result['uuid'], 'name': result['name'], 'surname': result['surname'], 'position': result['position'],
         'department': result['department']} for result in results]
    return employees


@app.route('/employees', methods=['GET'])
def get_employees_route():
    name = request.args.get('name')
    surname = request.args.get('surname')
    position = request.args.get('position')
    sort_by = request.args.get('sortBy')
    sort_order = request.args.get('sortOrder')

    with driver.session() as session:
        employees = session.read_transaction(get_employees, name, surname, position, sort_by, sort_order)

    response = {'employees': employees}
    return jsonify(response)


def get_subordinates(tx, uuid):
    query = "MATCH (e:Employee {uuid: $uuid})-[:MANAGES]->(e2:Employee) " \
            "RETURN e2.uuid as uuid, e2.name as name, e2.surname as surname"
    results = tx.run(query, uuid=uuid).data()
    subordinates = [{'uuid': result['uuid'], 'name': result['name'], 'surname': result['surname']} for result in
                    results]
    return subordinates


@app.route('/employees/<string:uuid>/subordinates', methods=['GET'])
def get_employee_subordinates_route(uuid):
    with driver.session() as session:
        subordinates = session.read_transaction(get_subordinates, uuid)

    response = {'subordinates': subordinates}
    return jsonify(response)


def get_department_details(tx, uuid):
    query = "MATCH (manager:Employee)-[:WORKS_IN {position: 'Manager'}]->(d:Department {uuid: $uuid}) " \
            "MATCH (e:Employee)-[:WORKS_IN]->(d) " \
            "WITH d, manager.name as manager_name, count(e) as number_of_employees " \
            "RETURN d.name as name, manager_name, number_of_employees"
    result = tx.run(query, uuid=uuid).data()
    if not result:
        return None
    else:
        department = {'name': result[0]['name'], 'manager': result[0]['manager_name'],
                      'number_of_employees': result[0]['number_of_employees']}
        return department


@app.route('/departments/<string:name>/details', methods=['GET'])
def get_department_details_route(name):
    with driver.session() as session:
        department = session.read_transaction(get_department_details, name)
        if not department:
            return jsonify({'message': 'Department not found'}), 400
        department_details = session.read_transaction(get_department_details, name)

    return jsonify(department_details)


def get_departments(tx, manager_name, number_of_employees, sort_by, sort_order):
    query = "MATCH (manager:Employee)-[w:WORKS_IN {position: 'Manager'}]->(d:Department) " \
            "MATCH (e:Employee)-[:WORKS_IN]->(d) " \
            "WITH d, manager, count(e) as number_of_employees "

    if manager_name:
        query += f"WHERE manager.name = '{manager_name}' "

    if number_of_employees:
        query += f"WHERE number_of_employees = {number_of_employees} "

    query += "RETURN d.uuid as department_uuid, d.name as department, " \
             "manager.name as manager, number_of_employees "

    if sort_by == 'manager' or sort_by == 'number_of_employees':
        query += f"ORDER BY {sort_by} "

        if sort_order:
            query += f"{sort_order}"

    results = tx.run(query).data()
    departments = [{'department_uuid': result['department_uuid'], 'department': result['department'],
                    'manager': result['manager'], 'number_of_employees': result['number_of_employees']} for result in
                   results]
    return departments


@app.route('/departments', methods=['GET'])
def get_departments_route():
    manager_name = request.args.get('managerName')
    number_of_employees = request.args.get('numberOfEmployees')
    sort_by = request.args.get('sortBy')
    sort_order = request.args.get('sortOrder')

    with driver.session() as session:
        departments = session.read_transaction(get_departments, manager_name, number_of_employees, sort_by, sort_order)

    response = {'departments': departments}
    return jsonify(response)


def get_department_employees(tx, uuid):
    query = "MATCH (e:Employee)-[:WORKS_IN]->(d:Department {uuid: $uuid}) " \
            "RETURN e.uuid as uuid, e.name as name, e.surname as surname"
    results = tx.run(query, uuid=uuid).data()
    employees = [{'uuid': result['uuid'], 'name': result['name'], 'surname': result['surname']} for result in
                 results]
    return employees


@app.route('/departments/<string:name>/employees', methods=['GET'])
def get_department_employees_route(name):
    with driver.session() as session:
        department = session.read_transaction(get_department_details, name)
        if not department:
            return jsonify({'message': 'Department not found'}), 400
        department_employees = session.read_transaction(get_department_employees, name)

    return jsonify(department_employees)


def handle_employee_result(result):
    if not result:
        return None
    else:
        employee = {'uuid': result[0]['e']['uuid'], 'name': result[0]['e']['name'],
                    'surname': result[0]['e']['surname'], 'position': result[0]['position'],
                    'department': result[0]['department'], 'department_uuid': result[0]['department_uuid']}
        return employee


def get_department_by_uuid(tx, uuid):
    query = "MATCH (d:Department) WHERE d.uuid=$uuid RETURN d"
    result = tx.run(query, uuid=uuid).data()
    if not result:
        return None
    else:
        department = {'name': result[0]['d']['name']}
        return department


def get_employee_by_name(tx, name):
    query = "MATCH (e:Employee)-[w:WORKS_IN]->(d:Department) WHERE e.name=$name " \
            "RETURN e,w.position as position,d.name as department, d.uuid as department_uuid"
    result = tx.run(query, name=name).data()
    return handle_employee_result(result)


def get_employee_by_surname(tx, surname):
    query = "MATCH (e:Employee)-[w:WORKS_IN]->(d:Department) WHERE e.surname=$surname " \
            "RETURN e,w.position as position,d.name as department, d.uuid as department_uuid"
    result = tx.run(query, surname=surname).data()
    return handle_employee_result(result)


def get_employee_by_uuid(tx, uuid):
    query = "MATCH (e:Employee)-[w:WORKS_IN]->(d:Department) WHERE e.uuid=$uuid " \
            "RETURN e,w.position as position,d.name as department, d.uuid as department_uuid"
    result = tx.run(query, uuid=uuid).data()
    return handle_employee_result(result)


def add_employee(tx, name, surname, position, department_uuid):
    query = "MATCH (d:Department {uuid: $department_uuid}) " \
            "CREATE (e:Employee {uuid: apoc.create.uuid(), name: $name, surname: $surname}) " \
            "CREATE (e)-[w:WORKS_IN {position: $position }]->(d)"
    tx.run(query, name=name, surname=surname, position=position, department_uuid=department_uuid)


@app.route('/employees', methods=['POST'])
def add_employee_route():
    name = request.json.get('name', None)
    surname = request.json.get('surname', None)
    position = request.json.get('position', None)
    department_uuid = request.json.get('departmentUuid', None)

    if name is None:
        return jsonify({'error': 'name is required'}), 400

    if surname is None:
        return jsonify({'error': 'surname is required'}), 400

    if position is None:
        return jsonify({'error': 'position is required'}), 400

    if department_uuid is None:
        return jsonify({'error': 'departmentUuid is required'}), 400

    with driver.session() as session:
        employee_by_name = session.read_transaction(get_employee_by_name, name)
        if employee_by_name is not None:
            return jsonify({'error': 'This name is already used'}), 400

        employee_by_surname = session.read_transaction(get_employee_by_surname, surname)
        if employee_by_surname is not None:
            return jsonify({'error': 'This surname is already used'}), 400

        department_by_uuid = session.read_transaction(get_department_by_uuid, department_uuid)
        if department_by_uuid is None:
            return jsonify({'error': 'This department does not exist'}), 400

        session.write_transaction(add_employee, name, surname, position, department_uuid)

    response = {'status': 'success'}
    return jsonify(response)


def update_employee(tx, uuid, name, surname, position, department_uuid):
    query1 = "MATCH (e:Employee {uuid:$uuid})-[w:WORKS_IN]->(:Department) DELETE w"
    tx.run(query1, uuid=uuid)

    query2 = "MATCH (e:Employee {uuid: $uuid}) " \
             "MATCH (d:Department {uuid: $department_uuid}) " \
             "CREATE (e)-[w:WORKS_IN {position: $position }]->(d) " \
             "SET e.name=$name, e.surname=$surname " \
             "RETURN e,w,d"
    tx.run(query2, uuid=uuid, name=name, surname=surname, position=position, department_uuid=department_uuid)
    return {'name': name, 'surname': surname, 'position': position, 'department_uuid': department_uuid}


@app.route('/employees/<string:uuid>', methods=['PUT'])
def update_employee_route(uuid):
    name = request.json.get('name', None)
    surname = request.json.get('surname', None)
    position = request.json.get('position', None)
    department_uuid = request.json.get('departmentUuid', None)

    if name is None:
        return jsonify({'error': 'name is required'}), 400

    if surname is None:
        return jsonify({'error': 'surname is required'}), 400

    if position is None:
        return jsonify({'error': 'position is required'}), 400

    if department_uuid is None:
        return jsonify({'error': 'departmentUuid is required'}), 400

    with driver.session() as session:
        employee_by_id = session.read_transaction(get_employee_by_uuid, uuid)
        if employee_by_id is None:
            return jsonify({'error': 'Employee not found'}), 400

        if name != employee_by_id['name']:
            employee_by_name = session.read_transaction(get_employee_by_name, name)
            if employee_by_name is not None:
                return jsonify({'error': 'This name is already used'}), 400

        if surname != employee_by_id['surname']:
            employee_by_surname = session.read_transaction(get_employee_by_surname, surname)
            if employee_by_surname is not None:
                return jsonify({'error': 'This surname is already used'}), 400

        department_by_uuid = session.read_transaction(get_department_by_uuid, department_uuid)
        if department_by_uuid is None:
            return jsonify({'error': 'This department does not exist'}), 400

        employee = session.write_transaction(update_employee, uuid, name, surname, position, department_uuid)

    if employee is None:
        return jsonify({'error': 'Employee not found'}), 400

    response = {'status': 'success'}
    return jsonify(response)


def delete_employee(tx, uuid):
    query = "MATCH (e:Employee) WHERE e.uuid=$uuid DETACH DELETE e"
    tx.run(query, uuid=uuid)


def delete_department(tx, uuid):
    query = "MATCH (d:Department {uuid: $uuid}) DETACH DELETE d"
    tx.run(query, uuid=uuid)


def add_manager_to_department(tx, department_uuid, manager_uuid):
    query = "MATCH (m:Employee {uuid: $manager_uuid}) " \
            "MATCH (d:Department {uuid: $department_uuid}) " \
            "CREATE (m)-[w:WORKS_IN {position: 'Manager'}]->(d)"
    tx.run(query, manager_uuid=manager_uuid, department_uuid=department_uuid)


@app.route('/employees/<string:uuid>', methods=['DELETE'])
def delete_employee_route(uuid):
    new_manager_uuid = request.args.get('newManagerUuid')

    with driver.session() as session:
        employee_by_id = session.read_transaction(get_employee_by_uuid, uuid)
        if employee_by_id is None:
            return jsonify({'error': 'Employee not found'}), 400

        if employee_by_id['position'] == 'Manager':
            if new_manager_uuid is None:
                session.write_transaction(delete_department, employee_by_id['department_uuid'])
            else:
                new_manager = session.read_transaction(get_employee_by_uuid, new_manager_uuid)
                if new_manager is None:
                    return jsonify({'error': 'New manager not found'}), 400

                session.write_transaction(add_manager_to_department, employee_by_id['department_uuid'],
                                          new_manager_uuid)

        session.write_transaction(delete_employee, uuid)

    response = {'status': 'success'}
    return jsonify(response)


if __name__ == '__main__':
    app.run()
