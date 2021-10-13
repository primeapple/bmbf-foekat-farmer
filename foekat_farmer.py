#!/usr/local/bin python3
import argparse
import csv
import datetime
import io
import logging
import logging.handlers
import os
import psycopg2.extras
import re
import requests
import sys
import time
from typing import IO

# .csv files from foerderportal.bund.de/foekat are always in this encoding
ENCODING = 'ISO-8859-1'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def download_csv_content(filename: str):
    session = requests.Session()
    quicksearch_data = {
        'suche.detailSuche': 'false',
        'suche.schnellSuche': '',
        'submitAction': ' Schnellsuche+starten'
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    session.post('https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=searchlist', headers=headers,
                 data=quicksearch_data)
    logging.info('Downloading csv for all entries from https://foerderportal.bund.de/foekat/')
    with session.get('https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=print&presentationType=csv',
                     headers=headers, stream=True) as r:
        # raise exception if HTTP Error
        r.raise_for_status()

        dl = 0
        dl_mb = 0
        start = time.time()
        with open(filename, mode='wb') as output_file:
            for chunk in r.iter_content(chunk_size=8192):
                output_file.write(chunk)
                # the following is only for logging
                dl += len(chunk)
                # only show message after each 10 mb
                if (current_mb := dl // 1000000) % 10 == 0 and current_mb > dl_mb:
                    dl_mb = current_mb
                    logging.info("{} MB downloaded, speed of {} kB/s".format(dl_mb, 1000 // (time.time() - start)))
                    start = time.time()
            logging.info('Download finished!')


def clean(string: str) -> str or float or None or datetime.date:
    # it is empty string
    if string == '':
        return None
    # it is string like '="something"'
    elif string[0:2] == '="' and string[len(string) - 1] == '"':
        cleaned_string = string[2:len(string) - 1]
        # it is date
        if re.match(r'[0-9]{2}\.[0-9]{2}\.[0-9]{4}', cleaned_string):
            day, month, year = cleaned_string.split('.')
            return datetime.date(year=int(year), month=int(month), day=int(day))
        # it is empty
        elif cleaned_string == '':
            return None
        # it is an actual string
        else:
            return cleaned_string
    # it is a numeric value (something like 23.123.233,20)
    elif re.match(r'-?([0-9]{1,3}\.)*[0-9]{1,3},[0-9]{2}', string):
        return float(string.translate(str.maketrans(',', '.', '.')))
    # Something weird..., so far we return it as a String
    else:
        logging.debug("Unknown entry format found, returning it as it is: {}".format(string))
        return string


def parse_csv(f: IO) -> [dict]:
    reader = csv.reader(f, delimiter=';')
    # first line are the keys
    keys = []
    last_orga = None
    next_orga_keys = 0
    for key in next(reader):
        cleaned_key = clean(key)
        if cleaned_key == 'Zuwendungsempfänger' or cleaned_key == 'Ausführende Stelle':
            last_orga = cleaned_key
            next_orga_keys = 5
        elif next_orga_keys > 0:
            cleaned_key = last_orga + '_' + cleaned_key
            next_orga_keys -= 1
        keys.append(cleaned_key)
    # now zip each line with the keys and add it to an array
    return [dict(zip(keys, [clean(value) for value in line])) for line in reader]


def create_db_schema(connection, schemaname: str):
    logging.info('Creating Schema {}'.format(schemaname))
    with connection.cursor() as cur:
        # creating schema
        cur.execute("CREATE SCHEMA {}".format(schemaname))
        cur.execute("SET search_path TO {}".format(schemaname))
        # initializing schema
        cur.execute(open('database/db_schema.sql', 'r').read())


def insert_in_database(dicts: [dict], schemaname: str):
    with psycopg2.connect(dbname=os.environ.get('POSTGRES_DB'),
                          user=os.environ.get('POSTGRES_USER'),
                          password=os.environ.get('POSTGRES_PASSWORD'),
                          host=os.environ.get('POSTGRES_HOST'),
                          port=os.environ.get('POSTGRES_PORT')) as con:
        create_db_schema(con, schemaname)
        logging.info('Filling the Database! This may take a little bit.')
        with con.cursor() as cur:
            query = "INSERT INTO csv_file (fkz, ressort, referat, projekttraeger, arbeitseinheit, zuwendungsempfaenger, zuwendungsempfaenger_kennziffer, zuwendungsempfaenger_gemeinde, zuwendungsempfaenger_ort, zuwendungsempfaenger_bundesland, zuwendungsempfaenger_staat, ausfuehrende_stelle, ausfuehrende_stelle_kennziffer, ausfuehrende_stelle_gemeinde, ausfuehrende_stelle_ort, ausfuehrende_stelle_bundesland, ausfuehrende_stelle_staat, thema, leistungsplansystematik, leistungsplansystematik_klartext, laufzeit_start, laufzeit_ende, foerdersumme, foerderprofil, verbundprojekt, foerderart) VALUES %s"
            template = "(%(FKZ)s, %(Ressort)s, %(Referat)s, %(PT)s, %(Arb.-Einh.)s, %(Zuwendungsempfänger)s, %(Zuwendungsempfänger_Gemeindekennziffer)s, %(Zuwendungsempfänger_Stadt/Gemeinde)s, %(Zuwendungsempfänger_Ort)s, %(Zuwendungsempfänger_Bundesland)s, %(Zuwendungsempfänger_Staat)s, %(Ausführende Stelle)s, %(Ausführende Stelle_Gemeindekennziffer)s, %(Ausführende Stelle_Stadt/Gemeinde)s, %(Ausführende Stelle_Ort)s, %(Ausführende Stelle_Bundesland)s, %(Ausführende Stelle_Staat)s, %(Thema)s, %(Leistungsplansystematik)s, %(Klartext Leistungsplansystematik)s, %(Laufzeit von)s, %(Laufzeit bis)s, %(Fördersumme in EUR)s, %(Förderprofil)s, %(Verbundprojekt)s, %(Förderart)s)"
            psycopg2.extras.execute_values(
                cur, query, dicts, template=template, page_size=1000
            )
            con.commit()


def create_unique_identifier(path=None):
    if path is None:
        return 'foekat_data_from_{}'.format(datetime.datetime.now().strftime('date_%Y_%m_%d_time_%H_%M_%S'))
    else:
        # replace unwanted characters with '_'
        return re.sub(r'[^0-9a-zA-Z]', '_', os.path.basename(path))


def main():
    parser = argparse.ArgumentParser(
        description='Handles the foerderkatalog csv.file at https://foerderportal.bund.de/foekat/')
    parser.add_argument('csv_files', metavar='F', type=str, nargs='*',
                        help='Provides .csv files, to read the data from.')
    parser.add_argument('--store_in_path', '-path', type=str,
                        help='Downloads and stores the csv file from the foekat in the given path.')
    parser.add_argument('--store_in_database', '-db', action='store_true',
                        help='Stores the file(s) in new schema(s) in the database')
    parser.add_argument('--log_level', '-log', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='Sets Log Level (see https://docs.python.org/3/howto/logging.html), defaults to INFO')
    ARGS = parser.parse_args()

    logging.basicConfig(level=ARGS.log_level, stream=sys.stdout, format=LOG_FORMAT)

    # download and store the csv file from foekat
    if ARGS.store_in_path is not None:
        identifier = create_unique_identifier()
        file_path = os.path.join(ARGS.store_in_path, "{}.csv".format(identifier))
        download_csv_content(file_path)
        logging.info('Downloaded csv file to path: {}'.format(file_path))
        ARGS.csv_files.append(file_path)

    # stores all given files (as well as the downloaded one) in the database
    if ARGS.store_in_database:
        for path in ARGS.csv_files:
            # always use this newline for the csv parser, see https://docs.python.org/3/library/csv.html#id3
            with open(path, mode='r', newline='', encoding=ENCODING) as csv_file:
                logging.info('Parsing csv file {}'.format(path))
                values = parse_csv(csv_file)
                identifier = create_unique_identifier(path=path)
                insert_in_database(values, identifier)


def mail_log(subject=u'Information in research-mining cronjob!'):
    logger = logging.getLogger(name='mail_logger')
    logger.setLevel(logging.DEBUG)
    env_vars = {
        'user': os.environ.get('LOGGING_EMAIL_USERNAME'),
        'password': os.environ.get('LOGGING_EMAIL_PASSWORD'),
        'server': os.environ.get('LOGGING_EMAIL_SMTP_SERVER'),
        'port': os.environ.get('LOGGING_EMAIL_SMTP_PORT'),
        'receiver': os.environ.get('LOGGING_EMAIL_RECEIVER'),
        'sender': os.environ.get('LOGGING_EMAIL_SENDER')
    }
    if None not in env_vars.values() and '' not in env_vars.values():
        mail_handler = logging.handlers.SMTPHandler(mailhost=(env_vars['server'], int(env_vars['port'])),
                                                    fromaddr=env_vars['sender'],
                                                    toaddrs=env_vars['receiver'],
                                                    subject=subject,
                                                    credentials=(env_vars['user'], env_vars['password']))
        mail_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(mail_handler)
    else:
        print('No correct mailconfig found, skipping mail logger')
    return logger


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        mail_log(subject=u'Exception in Foekat_Farmer').exception(e)
    else:
        mail_log().info('Finished foekat_farmer successfully!')
