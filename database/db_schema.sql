CREATE TABLE csv_file
(
fkz TEXT PRIMARY KEY,
ressort TEXT NOT NULL,
referat TEXT NOT NULL,
projekttraeger TEXT NOT NULL,
arbeitseinheit TEXT,
zuwendungsempfaenger TEXT NOT NULL,
zuwendungsempfaenger_kennziffer TEXT,
zuwendungsempfaenger_gemeinde TEXT,
zuwendungsempfaenger_ort TEXT,
zuwendungsempfaenger_bundesland TEXT,
zuwendungsempfaenger_staat TEXT,
ausfuehrende_stelle TEXT NOT NULL,
ausfuehrende_stelle_kennziffer TEXT,
ausfuehrende_stelle_gemeinde TEXT,
ausfuehrende_stelle_ort TEXT,
ausfuehrende_stelle_bundesland TEXT,
ausfuehrende_stelle_staat TEXT,
thema TEXT,
leistungsplansystematik TEXT,
leistungsplansystematik_klartext TEXT,
laufzeit_start DATE NOT NULL,
laufzeit_ende DATE NOT NULL,
foerdersumme NUMERIC NOT NULL,
foerderprofil TEXT,
verbundprojekt TEXT,
foerderart TEXT NOT NULL
);

CREATE TYPE ort_subclass AS ENUM ('gemeinde_inland', 'ort_inland', 'unbekannt_inland', 'ausland', 'nicht_zuzuordnen');
CREATE SEQUENCE ort_id;

CREATE TABLE orte
(
id INTEGER PRIMARY KEY DEFAULT nextval('ort_id'),
kennziffer TEXT,
gemeinde TEXT,
ort TEXT,
bundesland TEXT,
staat TEXT,
subclass ort_subclass NOT NULL
);
CREATE INDEX index_orte_columns ON orte (kennziffer, gemeinde, ort, bundesland, staat);

CREATE TABLE stellen
(
stelle TEXT,
ort_id INTEGER REFERENCES orte(id) NOT NULL,
PRIMARY KEY (stelle, ort_id)
);
CREATE INDEX foreign_key_stellen_on_orte ON stellen(ort_id);

CREATE TABLE foerdermittelgeber
(
ressort TEXT,
referat TEXT,
PRIMARY KEY (ressort, referat)
);

CREATE SEQUENCE projekttraeger_id;

CREATE TABLE projekttraeger
(
id INTEGER PRIMARY KEY DEFAULT nextval('projekttraeger_id'),
traeger TEXT NOT NULL,
arbeitseinheit TEXT
);


CREATE SEQUENCE ls_id;

CREATE TABLE leistungsplansystematiken
(
id INTEGER PRIMARY KEY DEFAULT nextval('ls_id'),
leistungsplansystematik TEXT,
klartext TEXT
);


CREATE TABLE foerderungen
(
-- primary key
fkz TEXT PRIMARY KEY,
-- normal attributes
thema TEXT,
laufzeit_start DATE NOT NULL,
laufzeit_ende DATE NOT NULL,
foerdersumme NUMERIC NOT NULL,
foerderprofil TEXT,
verbundprojekt TEXT,
foerderart TEXT NOT NULL,
-- foreign keys
ressort TEXT NOT NULL,
referat TEXT NOT NULL,
zuwendungsempfaenger TEXT NOT NULL,
zuwendungsempfaenger_ort_id INTEGER REFERENCES orte(id) NOT NULL,
ausfuehrende_stelle TEXT NOT NULL,
ausfuehrende_stelle_ort_id INTEGER REFERENCES orte(id) NOT NULL,
projekttraeger_id INTEGER REFERENCES projekttraeger(id) NOT NULL,
leistungsplansystematik_id INTEGER REFERENCES leistungsplansystematiken(id),
FOREIGN KEY (ressort, referat) REFERENCES foerdermittelgeber (ressort, referat),
FOREIGN KEY (zuwendungsempfaenger, zuwendungsempfaenger_ort_id) REFERENCES stellen (stelle, ort_id),
FOREIGN KEY (ausfuehrende_stelle, ausfuehrende_stelle_ort_id) REFERENCES stellen (stelle, ort_id)
);

-- CREATE MATERIALIZED VIEW stellen_orte AS
--     SELECT s.stelle, s.ort_id, o.kennziffer, o.gemeinde, o.ort, o.bundesland, o.staat, o.subclass
--     FROM stellen s JOIN orte o ON (s.ort_id = o.id)
-- WITH NO DATA;
-- CREATE UNIQUE INDEX unique_stellen_orte_id ON stellen_orte (stelle, ort_id);

--------------------
-- init functions --
--------------------
CREATE FUNCTION create_orte_from_csv() RETURNS VOID LANGUAGE PLPGSQL AS $$
	BEGIN
        WITH all_orte AS (
            SELECT csv_file.zuwendungsempfaenger_kennziffer AS kennziffer,
                csv_file.zuwendungsempfaenger_gemeinde AS gemeinde,
                csv_file.zuwendungsempfaenger_ort AS ort,
                csv_file.zuwendungsempfaenger_bundesland AS bundesland,
                csv_file.zuwendungsempfaenger_staat AS staat
            FROM csv_file
            UNION
            SELECT csv_file.ausfuehrende_stelle_kennziffer AS kennziffer,
                csv_file.ausfuehrende_stelle_gemeinde AS gemeinde,
                csv_file.ausfuehrende_stelle_ort AS ort,
                csv_file.ausfuehrende_stelle_bundesland AS bundesland,
                csv_file.ausfuehrende_stelle_staat AS staat
            FROM csv_file
        )
        INSERT INTO orte (kennziffer, gemeinde, ort, bundesland, staat, subclass) 
            SELECT *,
                CASE
                    WHEN staat='Deutschland'
                        AND kennziffer IS DISTINCT FROM '00000000'
                        AND gemeinde IS NOT NULL
                        AND bundesland IS NOT NULL
                        THEN 'gemeinde_inland'::ort_subclass
                    WHEN staat='Deutschland'
                        AND kennziffer IS NULL
                        AND gemeinde IS NULL
                        AND bundesland IS NULL
                        AND ort IS NOT NULL
                        THEN 'ort_inland'::ort_subclass
                    WHEN kennziffer='00000000'
                        AND gemeinde='Inland - nicht zuzuordnen'
                        THEN 'unbekannt_inland'::ort_subclass
                    WHEN kennziffer='99999999'
                        AND gemeinde = 'Ausland'
                        AND staat IS DISTINCT FROM 'Deutschland'
                        THEN 'ausland'::ort_subclass
                    ELSE 'nicht_zuzuordnen'::ort_subclass
                END subclass
            FROM all_orte;
	END $$;

CREATE FUNCTION create_stellen_from_csv() RETURNS VOID LANGUAGE PLPGSQL AS $$
	BEGIN
        WITH all_stellen AS (
            SELECT csv_file.zuwendungsempfaenger AS stelle, 
                csv_file.zuwendungsempfaenger_kennziffer AS kennziffer,
                csv_file.zuwendungsempfaenger_gemeinde AS gemeinde,
                csv_file.zuwendungsempfaenger_ort AS ort,
                csv_file.zuwendungsempfaenger_bundesland AS bundesland,
                csv_file.zuwendungsempfaenger_staat AS staat
            FROM csv_file
            UNION
            SELECT csv_file.ausfuehrende_stelle AS stelle,
                csv_file.ausfuehrende_stelle_kennziffer AS kennziffer,
                csv_file.ausfuehrende_stelle_gemeinde AS gemeinde,
                csv_file.ausfuehrende_stelle_ort AS ort,
                csv_file.ausfuehrende_stelle_bundesland AS bundesland,
                csv_file.ausfuehrende_stelle_staat AS staat
            FROM csv_file
        )
        INSERT INTO stellen (stelle, ort_id) 
            SELECT s.stelle, o.id AS ort_id
            FROM orte o JOIN all_stellen s ON (
                -- o.kennziffer IS NOT DISTINCT FROM s.kennziffer
                -- AND o.gemeinde IS NOT DISTINCT FROM s.gemeinde
                -- AND o.ort IS NOT DISTINCT FROM s.ort
                -- AND o.bundesland IS NOT DISTINCT FROM s.bundesland
                -- AND o.staat IS NOT DISTINCT FROM s.staat
                ((o.kennziffer IS NULL AND s.kennziffer IS NULL) OR (o.kennziffer = s.kennziffer)) AND
                ((o.gemeinde IS NULL AND s.gemeinde IS NULL) OR (o.gemeinde = s.gemeinde)) AND
                ((o.ort IS NULL AND s.ort IS NULL) OR (o.ort = s.ort)) AND
                ((o.bundesland IS NULL AND s.bundesland IS NULL) OR (o.bundesland = s.bundesland)) AND
                ((o.staat IS NULL AND s.staat IS NULL) OR (o.staat = s.staat))
            )
        ;
	END $$;

CREATE FUNCTION create_foerdermittelgeber_from_csv() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        INSERT INTO foerdermittelgeber
            SELECT DISTINCT ressort, referat FROM csv_file;
    END $$;

CREATE FUNCTION create_projekttraeger_from_csv() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        INSERT INTO projekttraeger (traeger, arbeitseinheit)
            SELECT DISTINCT projekttraeger, arbeitseinheit FROM csv_file;
    END $$;

CREATE FUNCTION create_leistungsplansystematiken_from_csv() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        INSERT INTO leistungsplansystematiken (leistungsplansystematik, klartext)
            SELECT DISTINCT leistungsplansystematik, leistungsplansystematik_klartext FROM csv_file
            WHERE leistungsplansystematik IS NOT NULL OR leistungsplansystematik_klartext IS NOT NULL;
    END $$;

CREATE FUNCTION create_foerderungen_from_csv() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        INSERT INTO foerderungen (
            fkz,
            thema,
            laufzeit_start,
            laufzeit_ende,
            foerdersumme,
            foerderprofil,
            verbundprojekt,
            foerderart,
            ressort,
            referat,
            projekttraeger_id,
            leistungsplansystematik_id,
            ausfuehrende_stelle,
            ausfuehrende_stelle_ort_id,
            zuwendungsempfaenger,
            zuwendungsempfaenger_ort_id
        )
            SELECT 
                c.fkz,
                c.thema,
                c.laufzeit_start,
                c.laufzeit_ende,
                c.foerdersumme,
                c.foerderprofil,
                c.verbundprojekt,
                c.foerderart,
                c.ressort,
                c.referat,
                p.id AS projekttraeger_id,
                l.id AS leistungsplansystematik_id,
                c.ausfuehrende_stelle,
                ausfuehrung.id AS ausfuehrende_stelle_ort_id,
                c.zuwendungsempfaenger,
                zuwendung.id AS zuwendungsempfaenger_ort_id
            FROM csv_file c JOIN projekttraeger p ON (
                p.traeger = c.projekttraeger AND
                p.arbeitseinheit IS NOT DISTINCT FROM c.arbeitseinheit
            ) LEFT JOIN leistungsplansystematiken l ON (
                l.leistungsplansystematik IS NOT DISTINCT FROM c.leistungsplansystematik AND
                l.klartext IS NOT DISTINCT FROM c.leistungsplansystematik_klartext
            ) JOIN orte ausfuehrung ON (
                ((ausfuehrung.kennziffer IS NULL AND c.ausfuehrende_stelle_kennziffer IS NULL) OR (ausfuehrung.kennziffer = c.ausfuehrende_stelle_kennziffer)) AND
                ((ausfuehrung.gemeinde IS NULL AND c.ausfuehrende_stelle_gemeinde IS NULL) OR (ausfuehrung.gemeinde = c.ausfuehrende_stelle_gemeinde)) AND
                ((ausfuehrung.ort IS NULL AND c.ausfuehrende_stelle_ort IS NULL) OR (ausfuehrung.ort = c.ausfuehrende_stelle_ort)) AND
                ((ausfuehrung.bundesland IS NULL AND c.ausfuehrende_stelle_bundesland IS NULL) OR (ausfuehrung.bundesland = c.ausfuehrende_stelle_bundesland)) AND
                ((ausfuehrung.staat IS NULL AND c.ausfuehrende_stelle_staat IS NULL) OR (ausfuehrung.staat = c.ausfuehrende_stelle_staat))
                -- ausfuehrung.kennziffer IS NOT DISTINCT FROM c.ausfuehrende_stelle_kennziffer AND
                -- ausfuehrung.gemeinde IS NOT DISTINCT FROM c.ausfuehrende_stelle_gemeinde AND
                -- ausfuehrung.ort IS NOT DISTINCT FROM c.ausfuehrende_stelle_ort AND
                -- ausfuehrung.bundesland IS NOT DISTINCT FROM c.ausfuehrende_stelle_bundesland AND
                -- ausfuehrung.staat IS NOT DISTINCT FROM c.ausfuehrende_stelle_staat
            ) JOIN orte zuwendung ON (
                ((zuwendung.kennziffer IS NULL AND c.zuwendungsempfaenger_kennziffer IS NULL) OR (zuwendung.kennziffer = c.zuwendungsempfaenger_kennziffer)) AND
                ((zuwendung.gemeinde IS NULL AND c.zuwendungsempfaenger_gemeinde IS NULL) OR (zuwendung.gemeinde = c.zuwendungsempfaenger_gemeinde)) AND
                ((zuwendung.ort IS NULL AND c.zuwendungsempfaenger_ort IS NULL) OR (zuwendung.ort = c.zuwendungsempfaenger_ort)) AND
                ((zuwendung.bundesland IS NULL AND c.zuwendungsempfaenger_bundesland IS NULL) OR (zuwendung.bundesland = c.zuwendungsempfaenger_bundesland)) AND
                ((zuwendung.staat IS NULL AND c.zuwendungsempfaenger_staat IS NULL) OR (zuwendung.staat = c.zuwendungsempfaenger_staat))
                -- zuwendung.kennziffer IS NOT DISTINCT FROM c.zuwendungsempfaenger_kennziffer AND
                -- zuwendung.gemeinde IS NOT DISTINCT FROM c.zuwendungsempfaenger_gemeinde AND
                -- zuwendung.ort IS NOT DISTINCT FROM c.zuwendungsempfaenger_ort AND
                -- zuwendung.bundesland IS NOT DISTINCT FROM c.zuwendungsempfaenger_bundesland AND
                -- zuwendung.staat IS NOT DISTINCT FROM c.zuwendungsempfaenger_staat
            );
    END $$;

CREATE FUNCTION check_correctness_of_normalization() RETURNS VOID LANGUAGE PLPGSQL AS $$
    BEGIN
        CREATE TEMPORARY TABLE reconstructed_csv ON COMMIT DROP AS
            SELECT 
                f.fkz,
                f.ressort,
                f.referat,
                p.traeger AS projekttraeger,
                p.arbeitseinheit,
                f.zuwendungsempfaenger,
                zuwendung.kennziffer AS zuwendungsempfaenger_kennziffer,
                zuwendung.gemeinde AS zuwendungsempfaenger_gemeinde,
                zuwendung.ort AS zuwendungsempfaenger_ort,
                zuwendung.bundesland AS zuwendungsempfaenger_bundesland,
                zuwendung.staat AS zuwendungsempfaenger_staat,
                f.ausfuehrende_stelle,
                ausfuehrung.kennziffer AS ausfuehrende_stelle_kennziffer,
                ausfuehrung.gemeinde AS ausfuehrende_stelle_gemeinde,
                ausfuehrung.ort AS ausfuehrende_stelle_ort,
                ausfuehrung.bundesland AS ausfuehrende_stelle_bundesland,
                ausfuehrung.staat AS ausfuehrende_stelle_staat,
                f.thema,
                l.leistungsplansystematik,
                l.klartext AS leistungsplansystematik_klartext,
                f.laufzeit_start,
                f.laufzeit_ende,
                f.foerdersumme,
                f.foerderprofil,
                f.verbundprojekt,
                f.foerderart
            FROM foerderungen f JOIN projekttraeger p ON (
                p.id = f.projekttraeger_id
            ) LEFT JOIN leistungsplansystematiken l ON (
                l.id = f.leistungsplansystematik_id
            ) JOIN orte ausfuehrung ON (
                ausfuehrung.id = f.ausfuehrende_stelle_ort_id
            ) JOIN orte zuwendung ON (
                zuwendung.id = f.zuwendungsempfaenger_ort_id
            );
        IF EXISTS (SELECT * FROM reconstructed_csv EXCEPT SELECT * FROM csv_file) THEN
            raise exception 'There are tuples in the normalized data that are not in the original csv_file!'; 
        ELSIF EXISTS (SELECT * FROM reconstructed_csv EXCEPT SELECT * FROM csv_file) THEN
            raise exception 'There are tuples in the original csv_file that are not in the normalized data!'; 
        END IF;
    END $$;

CREATE FUNCTION init_schema_from_csv() RETURNS VOID LANGUAGE PLPGSQL AS $$
	BEGIN
        PERFORM create_orte_from_csv();
        PERFORM create_stellen_from_csv();
        PERFORM create_foerdermittelgeber_from_csv();
        PERFORM create_projekttraeger_from_csv();
        PERFORM create_leistungsplansystematiken_from_csv();
        PERFORM create_foerderungen_from_csv();
        PERFORM check_correctness_of_normalization();
	END $$;