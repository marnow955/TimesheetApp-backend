import datetime

from flask import Blueprint, jsonify, json, request, abort

from ..config import DbConfig
from ..db.db_manager_abc import DbManagerABC
from ..db.mysql_db_manager import MySqlDbManager
from ..token_auth import requires_auth


def construct_timesheet(db_manager: DbManagerABC = None) -> Blueprint:
    timesheet = Blueprint('timesheet', __name__, url_prefix='/timesheet')

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @timesheet.route('/fetch-timesheet/<employee>/<week>/<year>', methods=['GET'])
    @requires_auth
    def fetch_timesheet(employee, week, year):
        tmsht_id = None
        task_list = []
        try:
            timesheets = db_manager.select_from_table('timesheets', ('id_tmsht', 'tsk_id'),
                                                      'employee=\'' + employee + '\'', False)
            date_str = str(year) + " " + str(week) + " 1"
            date_from = datetime.datetime.strptime(date_str, "%Y %W %w").date()
            date_to = date_from + datetime.timedelta(days=4)
            print(date_from)
            print(date_to)
            for timesheet in timesheets:
                if timesheet[0] != timesheets[0][0]:
                    abort(500)
                task_info = db_manager.select_from_table('tasks', ('title', 'time_limit'),
                                                         'task_id=' + str(timesheet[1]), False)[0]
                tracked = []
                reports = db_manager.select_from_table('daily_reports',
                                                       ('date', 'number_of_hours', 'description', 'status'),
                                                       'tsk_id=' + str(timesheet[1]) +
                                                       ' AND (date BETWEEN \'' + str(date_from) +
                                                       '\' AND \'' + str(date_to) + '\')', False)
                status = None
                if len(reports) > 0:
                    status = reports[0][3]
                else:
                    status = 'NONE'
                for date in (date_from + datetime.timedelta(days=n) for n in range(5)):
                    daily_dict = {}
                    for report in reports:
                        if report[0] == date:
                            daily_dict['tracked_time'] = report[1]
                            if report[2] is not None:
                                daily_dict['description'] = report[2]
                            else:
                                daily_dict['description'] = ''
                    if not daily_dict:
                        daily_dict = {
                            'tracked_time': 0,
                            'description': ''
                        }
                    tracked.append(daily_dict)
                task_dict = {
                    'task_id': timesheet[1],
                    'title': task_info[0],
                    'time_limit': task_info[1],
                    'status': status,
                    'tracked': tracked
                }
                task_list.append(task_dict)

            tmsht_id = timesheets[0][0]
        except Exception as e:
            print(e)
            abort(500)
        return jsonify(workername=employee, week=week, year=year, id_tmsht=tmsht_id, tasks=task_list)

    @timesheet.route('/save-timesheet', methods=['POST'])
    @requires_auth
    def save_timesheet():
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['task_name', 'time_limit', 'employee']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        try:
            pass
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    @timesheet.route('/accept-timesheet/<id_tmsht>/<week>/<year>', methods=['GET'])
    @requires_auth
    def accept_timesheet(id_tmsht, week, year):
        return update_status(id_tmsht, week, year, 'ACCEPTED')

    @timesheet.route('/decline-timesheet/<id_tmsht>/<week>/<year>', methods=['GET'])
    @requires_auth
    def decline_timesheet(id_tmsht, week, year):
        return update_status(id_tmsht, week, year, 'REJECTED')

    @timesheet.route('/update-status/<id_tmsht>/<week>/<year>/<status>', methods=['GET'])
    @requires_auth
    def update_status(id_tmsht, week, year, status):
        values_to_check = [id_tmsht, week, year]
        if any(value is None for value in values_to_check):
            abort(400)
        try:
            date_str = str(year) + " " + str(week) + " 1"
            date_from = datetime.datetime.strptime(date_str, "%Y %W %w").date()
            date_to = date_from + datetime.timedelta(days=4)
            tsk_ids = db_manager.select_from_table('timesheets', ('tsk_id',), 'id_tmsht=' + str(id_tmsht), False)
            for task_id in tsk_ids:
                db_manager.update_columns('daily_reports', {'status': status},
                                          'tsk_id=' + str(task_id[0]) + ' AND (date BETWEEN \''
                                          + str(date_from) + '\' AND \'' + str(date_to) + '\')', False)
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    return timesheet
