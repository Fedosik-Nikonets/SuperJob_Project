CREATE TABLE IF NOT EXISTS vacancies (
    source TEXT NOT NULL,
    id INTEGER NOT NULL,
    profession TEXT NOT NULL,
    town_id INTEGER,
    town_title TEXT,
    payment_from INTEGER,
    payment_to INTEGER,
    currency TEXT,
    agreement INTEGER,
    experience_id INTEGER,
    type_of_work_id INTEGER,
    place_of_work_id INTEGER,
    client_id INTEGER,
    firm_name TEXT,
    catalogues TEXT,
    date_published TEXT,
    work TEXT,
    candidat TEXT,
    compensation TEXT,
    raw_json TEXT,
    first_seen_at TEXT NOT NULL,
    PRIMARY KEY (source, id)
);

CREATE TABLE IF NOT EXISTS snapshots (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT,
    finished_at TEXT,
    params TEXT,
    n_found INTEGER,
    n_new INTEGER,
    n_errors INTEGER
);

CREATE INDEX IF NOT EXISTS idx_vac_client ON vacancies(client_id);
CREATE INDEX IF NOT EXISTS idx_vac_pub ON vacancies(date_published);