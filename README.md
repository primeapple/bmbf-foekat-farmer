# Foerderdata Farming

## General Setup
Make sure to setup your environment variables. You may also change the username or password of the database:
```bash
cp example.env .env
```

## Usage

### Developing
To develop you need to setup the database first:
```bash
# setup database
docker-compose up
# install database dependencies to access it later
sudo apt-get install libpq-dev gcc 
```

Also you may need several Environment Variables set. Do NOT source the `.env` file directly, rather always do:
```bash
# you can only do this in this directory, so please navigate here before running the command
source outside_docker.sh
# if you are using the fish shell, please run instead:
exec bash -c "source outside_docker.sh; exec fish"
```

### Production with Docker (enables Cronjobs)
By default the python script will download the csv file from the foekat page and save it in the folder (csv-files/) every day at 2am.
To change this behaviour, check out your `.env` file, there you can edit the crontab as well as the commands to run.

First, build the images that run the farmers
```bash
docker-compose --profile cron build
```
Now start the cronjobs:
```bash
# all cronjobs:
docker-compose --profile cron up -d
# only specific services
docker-compose up -d bmbf-foekat
# only specific services without any dependencies (good if you don't need database)
docker-compose up -d --no-deps bmbf-foekat
```

You can also run the farmers in docker manually. Please have a look at the `docker-compose.yml` file to check out the volumes, so that you can easily access the data: 
```bash
# this will show all possible commands
docker-compose run bmbf-foekat python -u foekat_farmer.py -h

# this will download the current file from the foekat and save it to volumes/csv-files/
docker-compose run bmbf-foekat python -u foekat_farmer.py --store_in_path csv-files/

# this will download the current file from the foekat and save it to volumes/csv-files/ and create a schema for it
# make sure the database is up
docker-compose run bmbf-foekat python -u foekat_farmer.py -path csv-files/ --store_in_database

# this will create schemas for the given files, you can also write the schema
# make sure the database is up
docker-compose run bmbf-foekat python -u foekat_farmer.py -db csv-files/file1.csv csv-files/file2.csv
```

To stop the docker-compose, please run the following command in another terminal window:
```bash
docker-compose down
```

Be aware, that both the database and the csv-files volumes will be persistent and will be there when you start the docker-compose the next time.

### Monitoring
You can add an email smtp configuration to get noticed if anything breaks in the scheduled fetching of the data. This is especially recommended if you are using the docker cron setup.
To do this, edit the `.env` file and fill out the all the variables that start with `LOGGING_EMAIL`. You will be notified about each run, if there were any problems or if it was successful.

## Resources
Make sure you have enough resources, mostly disk space and RAM to load the data in the database. On my raspberry pi 1b I had to increase the swap size to 1024.
If you just want to download the csv files regularly, you should not need any RAM increasing.


## Working with the data
To see the current database state, got to http://localhost:8081/?pgsql=db&username=postgres&db=db&ns=. The passwort for user `postgres` is `postgres`. Use `PostgreSQL` as database system and `db` as server and database.
You can now choose your schema on the left side, behind `Schema:`. The schemas that matter, starting with `foekat_data`.

### Create "normalized" tables
We have transformed the CSV file into a table called `csv_file` in the schema. Also we tried to create a reasonable normalization of this big table. This is quite hard, because there are a lot of probably wrongly entered datasets. However, to work with our [schema](database/foerderschema_datamodeler.dmd), run the following query in the adminer:
```sql
-- this will take some time (for my machine it is around 10 minutes)
SELECT init_schema_from_csv();
```
