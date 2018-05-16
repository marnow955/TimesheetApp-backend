from flask import Blueprint, jsonify, json, request, abort
from flask_cors import cross_origin

from ..config import DbConfig
from ..db import DbManagerABC, MySqlDbManager
from ..token_auth import requires_auth


def construct_task(db_manager: DbManagerABC = None) -> Blueprint:
    task_blp = Blueprint('task', __name__, url_prefix='/task')

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @task_blp.route('/employer/fetch-tasks/<employer>', methods=['GET'])
    @cross_origin()
    @requires_auth
    def fetch_employer_tasks(employer):
        tasks_list = []
        try:
            timesheets = db_manager.select_from_table('timesheets', ('tsk_id', 'employee'),
                                                      'employer=\'' + employer + '\'')
            for tmsht in timesheets:
                task_name, task_time = db_manager.select_from_table('tasks', ('title', 'time_limit'),
                                                                    'task_id=\'' + str(tmsht[0]) + '\'')[0]

                task_dict = {
                    'id': tmsht[0],
                    'name': task_name
                }

                tasks_list.append(task_dict)

        except Exception as e:
            print(e)
            abort(500)
        return jsonify(tasks=tasks_list)

    @task_blp.route('/employee/fetch-tasks/<employee>', methods=['GET'])
    @cross_origin()
    @requires_auth
    def fetch_employee_tasks(employee):
        tasks_list = []
        try:
            timesheets = db_manager.select_from_table('timesheets', ('tsk_id',),
                                                      'employee=\'' + employee + '\'')
            for tmsht in timesheets:
                task_name = db_manager.select_from_table('tasks', ('title',),
                                                         'task_id=\'' + str(tmsht[0]) + '\'')[0][0]
                tasks_list.append(task_name)

        except Exception as e:
            print(e)
            abort(500)
        return jsonify(tasks=tasks_list)

    @task_blp.route('/fetch-details', methods=['POST'])
    @cross_origin()
    @requires_auth
    def fetch_details():
        task_time = None
        employee = None
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['task']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        try:
            task_id = db_manager.select_from_table('tasks', ('task_id',),
                                                   'title=\'' + data_dict['task'] + '\'')
            if len(task_id) is not 1 and len(task_id[0]) is not 1:
                abort(500)
            employee = db_manager.select_from_table('timesheets', ('employee',),
                                                    'tsk_id=\'' + str(task_id[0][0]) + '\'')
            if len(employee) is not 1 and len(employee[0]) is not 1:
                abort(500)
            task_time = db_manager.select_from_table('tasks', ('time_limit',),
                                                     'task_id=\'' + str(task_id[0][0]) + '\'')
            if len(task_time) is not 1 and len(task_time[0]) is not 1:
                abort(500)

        except Exception as e:
            print(e)
            abort(500)
        return jsonify(time=task_time[0][0], worker=employee[0][0])

    @task_blp.route('/update-details', methods=['POST'])
    @cross_origin()
    @requires_auth
    def update_details():
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['task', 'time', 'worker']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        try:
            worker_exist = db_manager.select_from_table('users', ('*',), 'username=\'' + data_dict['worker'] + '\'')
            if len(worker_exist) is not 1:
                abort(422)
            task_id = db_manager.select_from_table('tasks', ('task_id',),
                                                   'title=\'' + data_dict['task'] + '\'')
            if len(task_id) is not 1 and len(task_id[0]) is not 1:
                abort(500)
            db_manager.update_columns('tasks', {'time_limit': str(data_dict['time'])},
                                      'task_id=' + str(task_id[0][0]))
            db_manager.update_columns('timesheets', {'employee': data_dict['worker']},
                                      'tsk_id=' + str(task_id[0][0]))

        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    @task_blp.route('/add-task/<employer>', methods=['POST'])
    @cross_origin()
    @requires_auth
    def add_task(employer):
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['task_name', 'task_time', 'employee']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        try:
            tsk_id = db_manager.insert_values('tasks', ('title', 'time_limit'),
                                              (data_dict['task_name'], str(data_dict['task_time'])))
            if tsk_id is 0:
                abort(500)
            tmsht = db_manager.select_from_table('timesheets', ('id_tmsht',),
                                                 'employee=\'' + str(data_dict['employee']) + '\'')
            if len(tmsht) is 0:
                t_id = db_manager.select_from_table('timesheets', ('MAX(id_tmsht)',))[0][0]
                tmsht_id = t_id + 1
            else:
                tmsht_id = tmsht[0][0]
            db_manager.insert_values('timesheets', ('id_tmsht', 'tsk_id', 'employee', 'employer'),
                                     (str(tmsht_id), str(tsk_id), data_dict['employee'], employer))
            if tmsht_id is 0:
                db_manager.delete_rows('tasks', 'task_id=' + str(tsk_id))
                abort(500)
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    @task_blp.route('/update-tasks', methods=['POST'])
    @cross_origin()
    @requires_auth
    def update_tasks():
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['ids', 'names', 'times', 'workers']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        first_length = len(data_dict['ids'])
        if any(len(value) != first_length for value in data_dict.values()):
            abort(422)
        try:
            tasks = [dict(zip(data_dict, t)) for t in zip(*data_dict.values())]
            for task in tasks:
                update_count = db_manager.update_columns('tasks',
                                                         {'title': task['names'], 'time_limit': str(task['times'])},
                                                         'task_id=' + str(task['ids']))
                if update_count is 0:
                    abort(500)
                db_manager.update_columns('timesheets', {'employee': task['workers']},
                                          'tsk_id=' + str(task['ids']))
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    return task_blp
