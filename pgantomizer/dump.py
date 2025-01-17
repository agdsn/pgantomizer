import argparse
import logging
import os
import subprocess
import sys

import yaml


def get_pg_dump_db_args(db_args):
    return '-d {} -U {} -h {} -p {} '.format(
        *(db_args or [os.environ.get(var) for var in
                      ['DB_DEFAULT_NAME', 'DB_DEFAULT_USER',
                       'DB_DEFAULT_SERVICE', 'DB_DEFAULT_PORT']]))


def dump_db(dump_path, dump_format, schema_path, db_schema, db_conn, password='', *db_args):
    schema = yaml.safe_load(open(schema_path))
    password = password or os.environ.get('DB_DEFAULT_PASS', '')
    os.putenv('PGPASSWORD', password)
    cmd = 'PGPASSWORD={password} pg_dump {format} {args} {schema} {tables} -f {filename}'.format(
        password=password,
        format=dump_format,
        args=db_conn if db_conn else get_pg_dump_db_args(db_args),
        schema='-n {}'.format(db_schema) if db_schema else '',
        tables=' '.join('-t {}'.format(table) for table in schema),
        filename=dump_path
    )
    logging.debug('Dumping DB with following command: {}'.format(cmd))
    subprocess.run(cmd, shell=True)


def main():
    parser = argparse.ArgumentParser(description='Dump tables specified in YAML config file from production DB '
                                                 'for later anonymization.',
                                     epilog='Compressed Postgres format is used. See README.md for details.')
    parser.add_argument('-v', '--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--schema',  help='YAML config file with tables to dump', default='./schema.yaml',
                        required=True)
    parser.add_argument('--dump-file',  help='path to the file where to dump the DB', default='to_anonymize.sql')
    parser.add_argument('--dump-format', help='pg_dump parameters describing the dump format', default='-Fc -Z 9')
    parser.add_argument('--dbname',  help='name of the database to dump')
    parser.add_argument('--dbschema', help='name of the database schema to dump')
    parser.add_argument('--user', help='name of the Postgres user with access to the database')
    parser.add_argument('--password', help='password of the Postgres user with access to the database', default='')
    parser.add_argument('--host', help='host where the DB is running', default='localhost')
    parser.add_argument('--port', help='port where the DB is running', default='5432')
    parser.add_argument('--conn', help='connection string of the database to dump')
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(levelname)s: %(message)s")

    if not os.path.isfile(args.schema):
        sys.exit('File with schema "{}" does not exist.'.format(args.schema))

    dump_db(
        args.dump_file,
        args.dump_format,
        args.schema,
        args.dbschema,
        args.conn,
        args.password,
        *([args.dbname, args.user, args.host, args.port]
          if args.dbname and args.user else [])
    )

if __name__ == '__main__':
    main()
