import mysql.connector
from keys_and_codes import db_conf

def isnumber(value):
    try:
        float(str(value))
        return True
    except ValueError:
        return False

def connect_db(db_name):
    DBConnection = mysql.connector.connect(
        host = db_conf['host'],
        user = db_conf['user'],
        password = db_conf['password'],
        database = db_name
    )
    return DBConnection

def delete(database,table,conditions={}):
    store(database,table,{},update=True,conditions=conditions,delete=True)

def store(database,table,data,update=False,conditions={},delete=False):
    output=None
    if not update and not delete:
        insert=True
        if isinstance(data, dict):
            data=[data]
    else:
        insert=False
        if isinstance(data, list):
            return False,f"Error: Can't update or delete multiple rows at once"

    db = connect_db(database)
    db_cursor = db.cursor()
    failed=False

    if insert:
        field_names = list(data[0].keys())
        fields_string = ', '.join(field_names)
        print(fields_string)
        values=[]
        for index,row in enumerate(data):
            row_values=[]
            for field_name in field_names:
                if field_name not in row:
                    return False,f"Error: Field '{field_name}' not in row {index}"
                if isnumber(row[field_name]):
                    field_value = row[field_name]
                elif isinstance(row[field_name], str):
                    field_value = f"'{row[field_name]}'"
                elif isinstance(row[field_name], list):
                    print(row[field_name])
                    field_value = ', '.join(str(val) for val in row[field_name])
                    field_value = f"'{field_value}'"
                else:
                    return False, f"Error: Unsupported type ({type(row[field_name])}) for field '{field_name}' in row {index}"

                row_values.append(field_value)
            row_string=', '.join(str(val) for val in row_values)
            values.append(f"({row_string})")
        values_string=', '.join(str(val) for val in values)
        query = f"INSERT INTO {table}({fields_string}) VALUES{values_string};"
    else:
        pairs=[]
        for key,value in data.items():
            pairs.append(f"{key} = '{value}'")
        pairs = ', '.join(pairs)

        conditions_string=''
        if len(conditions) != 0:
            conditions_list=[]
            for key,value in conditions.items():
                if isnumber(value):
                    conditions_list.append(f"{key} = {value}")
                else:
                    conditions_list.append(f"{key} = '{value}'")
            conditions_string = 'WHERE ' + ' AND '.join(conditions_list)
        if delete:
            query=f"DELETE FROM {table} {conditions_string};"
        elif update:
            query = f"UPDATE {table} SET {pairs} {conditions_string};"

    if db_conf['debug_queries']:
        print(query)

    try:
        db_cursor.execute(query)
        db_cursor.execute('SELECT LAST_INSERT_ID();')
        queryResult = db_cursor.fetchall()
        last_insert_id=queryResult[0][0]

    except mysql.connector.Error as error:
        issue_resolved=False
        if error.errno == 1062:
            output = "Duplicate entry"
            failed=True
        if not issue_resolved:
            output = f"insert_query Failed, Rolling back. Error : {error}"
            db.rollback()
            failed=True

        # mysql.connector.errors.ProgrammingError: 1044 (42000): Access denied for user 'ctkxbot'@'%' to database 'reports'
            # Still happens when the db doesn't exist
        # mysql.connector.errors.ProgrammingError: 1146 (42S02): Table 'reports.reporties' doesn't exist
        # mysql.connector.errors.ProgrammingError: 1054 (42S22): Unknown column 'guilad_id' in 'field list'
        # mysql.connector.errors.DataError:        1136 (21S01): Column count doesn't match value count at row 1
    finally:
        if db.is_connected():
            db_cursor.close()
            db.commit()
            db.close()

        if failed:
            return False,output
        else:
            return True,last_insert_id

def get_columns(db,table):
    db_cursor = db.cursor()
    query=f"SHOW COLUMNS FROM {table};"
    if db_conf['debug_queries']:
        print(query)
    db_cursor.execute(query)
    queryResult = db_cursor.fetchall()
    db_cursor.close()
    columns=[]
    for row in queryResult:
        columns.append(row[0])
    return columns

def get(database,table,conditions={},auto_create=False):
    db = connect_db(database)
    fields=get_columns(db,table)
    db_cursor = db.cursor()
    fields_string = ', '.join(fields)

    conditions_string=''
    if len(conditions) != 0:
        conditions_list=[]
        for key,value in conditions.items():
            if key == 'id':
                conditions_list.append(f"{key} = {value}")
            else:
                conditions_list.append(f"{key} = '{value}'")
        conditions_string = 'WHERE ' + ' AND '.join(conditions_list)

    query=f"SELECT {fields_string} from {table} {conditions_string};"

    if db_conf['debug_queries']:
        print(query)

    db_cursor.execute(query)
    queryResult = db_cursor.fetchall()

    db_cursor.close()
    db.commit()
    db.close()
    output=[]
    if len(queryResult) == 0 and auto_create:
        store(database,table,conditions,update=False,update_id=None)
    for row in queryResult:
        row_dict={}
        for key,val in zip(fields,row):
            if "_list" in key:
                val=val.split(', ')
            row_dict[key]=val
        output.append(dict(zip(fields,row)))
    return output
