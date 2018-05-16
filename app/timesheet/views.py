import datetime

from flask import Blueprint, jsonify, json, request, abort
from flask_cors import cross_origin

from ..config import DbConfig
from ..db import DbManagerABC, MySqlDbManager
from ..token_auth import requires_auth


def construct_timesheet(db_manager: DbManagerABC = None) -> Blueprint:
    timesheet_blp = Blueprint('timesheet', __name__, url_prefix='/timesheet')

    if db_manager is None:
        db_manager = MySqlDbManager(DbConfig)

    @timesheet_blp.route('/fetch-task-report/<employee>/<week>/<year>/<taskname>')
    @cross_origin()
    @requires_auth
    def fetch_task_report(employee, week, year, taskname):
        status = None
        tracked = []
        try:
            task_id = db_manager.select_from_table('tasks', ('task_id',), 'title=\'' + taskname + '\'')
            if len(task_id) is not 1 and len(task_id[0]) is not 1:
                abort(500)

            date_str = str(year) + " " + str(week) + " 1"
            date_from = datetime.datetime.strptime(date_str, "%Y %W %w").date()
            date_to = date_from + datetime.timedelta(days=4)
            reports = db_manager.select_from_table('daily_reports',
                                                   ('date', 'number_of_hours', 'description', 'status'),
                                                   'tsk_id=' + str(task_id[0][0]) +
                                                   ' AND (date BETWEEN \'' + str(date_from) +
                                                   '\' AND \'' + str(date_to) + '\')')
            if len(reports) > 0:
                status = reports[0][3]
            else:
                status = 'BRAK'
            tracked = []
            for date in (date_from + datetime.timedelta(days=n) for n in range(5)):
                daily_dict = {}
                for report in reports:
                    if report[0] == date:
                        daily_dict['day'] = date.strftime("%d/%m")
                        daily_dict['trackedTime'] = report[1]
                        if report[2] is not None:
                            daily_dict['description'] = report[2]
                        else:
                            daily_dict['description'] = ''
                if not daily_dict:
                    daily_dict = {
                        'day': date.strftime("%d/%m"),
                        'trackedTime': 0,
                        'description': ''
                    }
                tracked.append(daily_dict)
        except Exception as e:
            print(e)
            abort(500)
        return jsonify(tracked=tracked, status=status)

    @timesheet_blp.route('/save-report', methods=['POST'])
    @cross_origin()
    @requires_auth
    def save_report():
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['task_descriptions', 'week', 'year', 'selected_task', 'worker']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        new_tracked = data_dict['task_descriptions']
        if len(new_tracked) is not 5:
            abort(422)
        date_str = str(data_dict['year']) + " " + str(data_dict['week']) + " 1"
        date_from = datetime.datetime.strptime(date_str, "%Y %W %w").date()
        try:
            task_id = db_manager.select_from_table('tasks', ('task_id',),
                                                   'title=\'' + data_dict['selected_task'] + '\'')
            if len(task_id) is not 1 and len(task_id[0]) is not 1:
                abort(500)
            for date in (date_from + datetime.timedelta(days=n) for n in range(5)):
                delta = (date - date_from).days
                updated = db_manager.update_columns('daily_reports',
                                                    {'number_of_hours': str(
                                                        new_tracked[delta]['trackedTime']),
                                                        'description': new_tracked[delta]['description'],
                                                        'status': 'Zapisany'},
                                                    'tsk_id=' + str(task_id[0][0]) +
                                                    " AND date=\'" + str(date) + '\'')
                if updated == 0 and new_tracked[delta]['trackedTime'] != 0:
                    exist_check = db_manager.select_from_table('daily_reports', ('*',),
                                                               'tsk_id=' + str(task_id[0][0]) +
                                                               " AND date=\'" + str(date) + '\'')
                    if len(exist_check) is 0:
                        db_manager.insert_values('daily_reports',
                                                 ('tsk_id', 'date', 'number_of_hours', 'description', 'status'),
                                                 (str(task_id[0][0]), str(date),
                                                  str(new_tracked[delta]['trackedTime']),
                                                  new_tracked[delta]['description'],
                                                  'Zapisany'))
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    @timesheet_blp.route('/fetch-timesheet/<employee>/<week>/<year>', methods=['GET'])
    @cross_origin()
    @requires_auth
    def fetch_timesheet(employee, week, year):
        tmsht_id = None
        task_list = []
        try:
            timesheets = db_manager.select_from_table('timesheets', ('id_tmsht', 'tsk_id'),
                                                      'employee=\'' + employee + '\'')
            date_str = str(year) + " " + str(week) + " 1"
            date_from = datetime.datetime.strptime(date_str, "%Y %W %w").date()
            date_to = date_from + datetime.timedelta(days=4)
            for timesheet in timesheets:
                if timesheet[0] != timesheets[0][0]:
                    abort(500)
                task_info = db_manager.select_from_table('tasks', ('title', 'time_limit'),
                                                         'task_id=' + str(timesheet[1]))[0]
                reports = db_manager.select_from_table('daily_reports',
                                                       ('date', 'number_of_hours', 'description', 'status'),
                                                       'tsk_id=' + str(timesheet[1]) +
                                                       ' AND (date BETWEEN \'' + str(date_from) +
                                                       '\' AND \'' + str(date_to) + '\')')
                if len(reports) > 0:
                    status = reports[0][3]
                else:
                    status = 'NONE'
                tracked = []
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
            tmsht_id = None
            if len(timesheets) > 0:
                tmsht_id = timesheets[0][0]
        except Exception as e:
            print(e)
            abort(500)
        return jsonify(workername=employee, week=week, year=year, id_tmsht=tmsht_id, tasks=task_list)

    @timesheet_blp.route('/save-timesheet', methods=['POST'])
    @cross_origin()
    @requires_auth
    def save_timesheet():
        if not request.json:
            abort(400)
        data = request.data
        data_dict = json.loads(data)
        keys = ['task_descriptions', 'timesheet']
        if any(key not in list(data_dict.keys()) for key in keys):
            abort(422)
        new_tracked = data_dict['task_descriptions']
        tasks = data_dict['timesheet']['tasks']
        if len(tasks) != len(new_tracked) / 5:
            abort(422)
        date_str = str(data_dict['timesheet']['year']) + " " + str(data_dict['timesheet']['week']) + " 1"
        date_from = datetime.datetime.strptime(date_str, "%Y %W %w").date()
        try:
            for task in tasks:
                for date in (date_from + datetime.timedelta(days=n) for n in range(5)):
                    td = tasks.index(task)
                    delta = (date - date_from).days
                    updated = db_manager.update_columns('daily_reports',
                                                        {'number_of_hours': str(
                                                            new_tracked[5 * td + delta]['tracked_time']),
                                                            'description': new_tracked[5 * td + delta]['description'],
                                                            'status': 'SAVED'},
                                                        'tsk_id=' + str(task['task_id']) +
                                                        " AND date=\'" + str(date) + '\'')
                    if updated == 0 and new_tracked[5 * td + delta]['tracked_time'] != 0:
                        exist_check = db_manager.select_from_table('daily_reports', ('*',),
                                                                   'tsk_id=' + str(task['task_id']) +
                                                                   " AND date=\'" + str(date) + '\'')
                        if len(exist_check) is 0:
                            db_manager.insert_values('daily_reports',
                                                     ('tsk_id', 'date', 'number_of_hours', 'description', 'status'),
                                                     (str(task['task_id']), str(date),
                                                      str(new_tracked[5 * td + delta]['tracked_time']),
                                                      new_tracked[5 * td + delta]['description'],
                                                      'SAVED'))
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    @timesheet_blp.route('/send-timesheet/<id_tmsht>/<week>/<year>', methods=['GET'])
    @cross_origin()
    @requires_auth
    def send_timesheet(id_tmsht, week, year):
        return update_status(id_tmsht, week, year, 'Wysłany')

    @timesheet_blp.route('/accept-timesheet/<id_tmsht>/<week>/<year>', methods=['GET'])
    @cross_origin()
    @requires_auth
    def accept_timesheet(id_tmsht, week, year):
        return update_status(id_tmsht, week, year, 'Zaakceptowany')

    @timesheet_blp.route('/decline-timesheet/<id_tmsht>/<week>/<year>', methods=['GET'])
    @cross_origin()
    @requires_auth
    def decline_timesheet(id_tmsht, week, year):
        return update_status(id_tmsht, week, year, 'Odrzucony')

    @timesheet_blp.route('/update-status/<id_tmsht>/<week>/<year>/<status>', methods=['GET'])
    @cross_origin()
    @requires_auth
    def update_status(id_tmsht, week, year, status):
        values_to_check = [id_tmsht, week, year]
        if any(value is None for value in values_to_check):
            abort(400)
        try:
            date_str = str(year) + " " + str(week) + " 1"
            date_from = datetime.datetime.strptime(date_str, "%Y %W %w").date()
            date_to = date_from + datetime.timedelta(days=4)
            tsk_ids = db_manager.select_from_table('timesheets', ('tsk_id',), 'id_tmsht=' + str(id_tmsht))
            for task_id in tsk_ids:
                db_manager.update_columns('daily_reports', {'status': status},
                                          'tsk_id=' + str(task_id[0]) + ' AND (date BETWEEN \''
                                          + str(date_from) + '\' AND \'' + str(date_to) + '\')')
        except Exception as e:
            print(e)
            abort(500)
        return "OK"

    return timesheet_blp
