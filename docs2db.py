"""It's ok, this code was not used in production."""
from os.path import join as pj

import pandas

from sqlalchemy import create_engine, text

try:
    from .. import config
    DB_STR = config['default'].SQLALCHEMY_DATABASE_URI
except (ImportError, AttributeError, KeyError) as e:
    print(f'Config loading error, switched to default\n\n{e}')
    DB_STR = 'yes'
    del e

DB = create_engine(DB_STR)


def log2db(connection, idtask, msg):
    """Функция для быстрой записи в лог."""
    connection.execute(
        text(
            "INSERT INTO tasks_log(idtask,note)VALUES(:idtask,:msg);"
        ).execution_options(autocommit=True),
        idtask=idtask,
        msg=msg
    )


def purge(table_name):
    """Deletes data without dropping the table."""
    DB.execute(
        text(
            f'DELETE FROM {table_name}'
        ).execution_options(autocommit=True)
    )


def get_settings():
    """Gets them."""
    return DB.execute(
        'SELECT xls_get_all_formats();'
    ).fetchall()[0][0]


def insert_template(xls_file_path, task_type):
    """Check xls with a template and insert it to the table."""
    templates = [x for x in get_settings() if x['task_type'] == task_type]
    df = pandas.read_excel(xls_file_path)
    for tmpl in templates:
        if df.shape[1] == tmpl['numcols']:
            # and tmpl['filename_template'].lower() in xls_file_path.lower():

            if 'del_cols' in tmpl and tmpl['del_cols']:
                df.drop(df.columns[tmpl['del_cols']], axis=1, inplace=True)
            if 'del_rows' in tmpl and tmpl['del_rows']:
                df.drop(tmpl['del_rows'], inplace=True)
            if 'tp_field' in tmpl and tmpl['tp_field']:
                tmpl['tp_field'] = [x for x in tmpl['tp_field'] if x]
                df.columns = tmpl['tp_field']

            purge(tmpl['result_table'])
            df.to_sql(tmpl['result_table'],
                      con=DB, if_exists='append', method='multi')
            return False
    return True


def do_xml_task(task_uuid):
    """Main."""
    pack = DB.execute(
        text(
            'select json_agg(row_to_json(row)) '
            'from ('
            'select task_type,infilename,inpath '
            'from tasks_load '
            f"where idtask='{task_uuid}' and task_status=-1"
            ')row;'
        ).execution_options(autocommit=True)
    ).fetchall()[0][0]
    try:
        if insert_template(
            pj(pack[0]['inpath'], pack[0]['infilename']),
            pack[0]['task_type']
        ):
            task_status(task_uuid, 2)
            log2db(DB, task_uuid, 'Заполнение промежуточных таблиц')
        else:
            task_status(task_uuid, 0)
            log2db(DB, task_uuid, 'Неверный формат файла')
    except Exception as err:  # noqa: W0703
        log2db(DB, task_uuid, f'Ошибка загрузки\n\n{err}')


def task_status(task_uuid, stat):
    """Change task status."""
    DB.execute(
        text(
            f'UPDATE tasks_load SET task_status={stat} '
            f'WHERE idtask={task_uuid}'
        ).execution_options(autocommit=True)
    )


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        sys.exit('Not enough args provided.\n'
                 'Must be:\n'
                 'python3 ./docs2db.py <task_type_num> <file_path>')
    insert_template(sys.argv[2], sys.argv[1])
