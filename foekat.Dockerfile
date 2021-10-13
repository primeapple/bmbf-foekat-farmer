FROM python:3.9-slim
LABEL maintainer=toni.mueller@student.uni-halle.de
RUN apt-get --yes update
RUN apt-get --yes install libpq-dev gcc cron

# setting up workspace
ENV APP_HOME /opt/app/bmbf-foekat
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME
COPY requirements.txt .
# install dependencies
RUN pip install -r requirements.txt
# copy the rest of the stuff
COPY . ${APP_HOME}
# make the foekat_farmer executable for cron
RUN chmod +x foekat_farmer_cron.sh

# Write the crontab:
# run foekat_farmer_cron.sh to download the csv file every day at 2 am
ARG CRON_TIME_FOEKAT
RUN crontab -l | { cat; echo "${CRON_TIME_FOEKAT} bash /opt/app/bmbf-foekat/foekat_farmer_cron.sh > /proc/1/fd/1 2>/proc/1/fd/2"; } | crontab -

CMD ["python", "-u", "foekat_farmer.py", "-h"]
