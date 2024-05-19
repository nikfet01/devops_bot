FROM postgres:15

RUN mkdir -p /oracle/pg_data/archive/ && \
    chown -R postgres:postgres /oracle/pg_data/archive/

COPY ./init.sql /docker-entrypoint-initdb.d

CMD ["pg_ctl", "-D", "/var/lib/postgresql/data", "-l", "logfile", "start"]
