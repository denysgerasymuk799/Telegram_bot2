#!/usr/bin/python

import psycopg2
from harmix_db import config


def create_tables():
    """ create tables in the PostgreSQL database"""
    commands = (
        """
            CREATE TABLE users_data (
            username  VARCHAR(255) NOT NULL,
            language VARCHAR(255) NOT NULL,
            n_videos INTEGER
        )
        """,
        """ CREATE TABLE answers_on_survey (
                username VARCHAR(255) NOT NULL,
                question1 VARCHAR(255) NOT NULL,
                question2 VARCHAR(255) NOT NULL,
                question3 VARCHAR(255) NOT NULL,
                question4 VARCHAR(255) NOT NULL
                )
        """
       )
    conn = None
    try:
        # read the connection parameters
        params = config.config()
        # connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # create table one by one
        for command in commands:
            cur.execute(command)
        # close communication with the PostgreSQL database server
        cur.close()
        # commit the changes
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def insert_sql(table_name, answers):
    """ insert a new vendor into the vendors table """
    n_values = ['%s'] * len(answers)
    n_values = ', '.join(map(str, n_values))

    name_columns = ''

    if table_name == 'users_data':
        name_columns = 'username, language, n_videos'

    elif table_name == 'answers_on_survey':
        name_columns = 'username, question1, question2, question3, question4'

    sql = """INSERT INTO {0} ({1}) 
            VALUES ({2})""".format(table_name, name_columns, n_values)
    conn = None
    try:
        # read database configuration
        params = config.config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the INSERT statement
        cur.execute(sql, answers)
        # commit the changes to the database
        conn.commit()
        # close communication with the database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def update_sql(name_table, name_parameter, username, parameter):
    """ update vendor name based on the vendor id """
    print("update")
    sql = """ UPDATE {}
                SET {} = %s
                WHERE username = %s""".format(name_table, name_parameter)
    conn = None
    updated_rows = 0
    try:
        # read database configuration
        params = config.config()
        # connect to the PostgreSQL database
        conn = psycopg2.connect(**params)
        # create a new cursor
        cur = conn.cursor()
        # execute the UPDATE  statement
        cur.execute(sql, (str(parameter), username))
        # get the number of updated rows
        updated_rows = cur.rowcount
        # Commit the changes to the database
        conn.commit()
        # Close communication with the PostgreSQL database
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

    return updated_rows


def start_collect_user_data(username):
    insert_sql('users_data', [username, "uk", 0])


if __name__ == '__main__':
    create_tables()
    # insert_sql('users_data', username, "uk", 0)
    insert_sql('answers_on_survey', "@denysger88", "ru", "yes", "no", "no")
    update_sql('users_data', 'language', "@denysger88", 'ua')
