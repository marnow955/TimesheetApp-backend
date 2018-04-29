from flask import Blueprint, jsonify, json, request, abort
from ..db.db_manager_abc import DbManagerABC
from ..db.mysql_db_manager import MySqlDbManager
from ..config import DbConfig


def construct_task(db_manager: DbManagerABC = None) -> Blueprint:
    task = Blueprint('task', __name__, url_prefix='/task')

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @task.route('/fetch-tasks/<employer>', methods=['GET'])
    def fetch_tasks(employer):
        tasks_list = []
        try:
            timesheets = db_manager.select_from_table('timesheets', ('tsk_id', 'employee'),
                                                      'employer=\'' + employer + '\'', False)
            for tmsht in timesheets:
                task_name, task_time = db_manager.select_from_table('tasks', ('title', 'time_limit'),
                                                                    'task_id=\'' + str(tmsht[0]) + '\'', False)[0]

                task_dict = {
                    'task_id': tmsht[0],
                    'task_name': task_name,
                    'task_time': task_time,
                    'employee': tmsht[1]
                }

                tasks_list.append(task_dict)

        except Exception as e:
            print(e)
        return jsonify(tasks=tasks_list)

    @task.route('/add-task/<employer>', methods=['POST'])
    def add_task(employer):
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['task_name', 'time_limit', 'employee']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        try:
            tsk_id = db_manager.insert_values('tasks', ('title', 'time_limit'),
                                              (data_dict['task_name'], str(data_dict['time_limit'])), False)
            if tsk_id is 0:
                abort(500)
            tmsht = db_manager.select_from_table('timesheets', ('id_tmsht',),
                                                 'employee=\'' + str(data_dict['employee']) + '\'', False)
            tmsht_id = 0
            if len(tmsht) is 0:
                t_id = db_manager.select_from_table('timesheets', ('MAX(id_tmsht)',), join_transaction=False)[0][0]
                tmsht_id = t_id + 1
            else:
                tmsht_id = tmsht[0][0]
            db_manager.insert_values('timesheets', ('id_tmsht', 'tsk_id', 'employee', 'employer'),
                                     (str(tmsht_id), str(tsk_id), data_dict['employee'], employer), False)
            if tmsht_id is 0:
                db_manager.delete_rows('tasks', 'task_id=' + str(tsk_id), False)
                abort(500)
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    @task.route('/update-tasks', methods=['POST'])
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
                                                         'task_id=' + str(task['ids']), False)
                if update_count is 0:
                    abort(500)
                db_manager.update_columns('timesheets', {'employee': task['workers']},
                                          'tsk_id=' + str(task['ids']), False)
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    return task
