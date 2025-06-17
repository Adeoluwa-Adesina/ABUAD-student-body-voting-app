-- Drop tables if they exist to start fresh (optional, use with caution)
DROP TABLE IF EXISTS vote CASCADE;
DROP TABLE IF EXISTS option CASCADE;
DROP TABLE IF EXISTS poll CASCADE;
DROP TABLE IF EXISTS organization CASCADE; -- Added organization table
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS settings CASCADE;

-- Users Table
-- Stores user information, including credentials and admin status.
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Organization Table
-- Stores information about each student organization.
CREATE TABLE organization (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL, -- e.g., "Students Representative Council"
    acronym VARCHAR(50) UNIQUE,        -- e.g., "SRC"
    logo_filename VARCHAR(255),        -- e.g., "src_logo.jpeg" (store only filename)
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Poll Table
-- Stores information about each poll, now linked to an organization.
CREATE TABLE poll (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    organization_id INTEGER REFERENCES organization(id) ON DELETE SET NULL, -- Link to organization
    -- user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Optional: To track poll creator
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Option Table
-- Stores the individual options for each poll.
CREATE TABLE option (
    id SERIAL PRIMARY KEY,
    poll_id INTEGER NOT NULL REFERENCES poll(id) ON DELETE CASCADE,
    text VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Vote Table
-- Records votes cast by users on poll options.
CREATE TABLE vote (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    option_id INTEGER NOT NULL REFERENCES option(id) ON DELETE CASCADE,
    poll_id INTEGER NOT NULL REFERENCES poll(id) ON DELETE CASCADE,
    voted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_user_poll_vote UNIQUE (user_id, poll_id) -- Ensures a user can vote only once per poll
);

-- Settings Table
-- Stores application-wide settings, managed via the admin panel.
CREATE TABLE settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT,
    description VARCHAR(255), -- Optional: for clarity
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_poll_organization_id ON poll(organization_id); -- New index
CREATE INDEX idx_option_poll_id ON option(poll_id);
CREATE INDEX idx_vote_user_id ON vote(user_id);
CREATE INDEX idx_vote_option_id ON vote(option_id);
CREATE INDEX idx_vote_poll_id ON vote(poll_id);

-- Pre-populate Organizations Table
INSERT INTO organization (name, acronym, logo_filename, description) VALUES
    ('Students Representative Council', 'SRC', 'src_logo.jpeg', 'The primary student governing body of ABUAD.'),
    ('Law Students Society ABUAD', 'LSS ABUAD', 'lss_abuad_logo.jpeg', 'Represents law students at Afe Babalola University.'),
    ('Nigerian University Engineering Students Association ABUAD', 'NUESA ABUAD', 'nuesa_abuad_logo.jpeg', 'For engineering students at ABUAD.'),
    ('Afe Babalola Medical Students Association', 'AMSA', 'amsa_logo.jpeg', 'Represents medical students at ABUAD.'),
    ('National Association of Computing Students ABUAD', 'NACOS ABUAD', 'nacos_abuad_logo.jpeg', 'For computing and IT students at ABUAD.'),
    ('Communication and Media Studies Students Association', 'COMSSA', 'comssa_logo.jpeg', 'Represents students in Communication and Media Studies.'),
    ('ABUAD Pharmacology Students Association', 'APSA', 'apsa_logo.jpeg', 'For pharmacology students at ABUAD.'),
    ('Pharmaceutical Association of Nigeria Students ABUAD', 'PANS ABUAD', 'pans_abuad_logo.jpeg', 'The student wing of the Pharmaceutical Association of Nigeria at ABUAD.'),
    ('College of Medicine and Health Sciences Students Association ABUAD', 'COMHSSA ABUAD', 'comhssa_abuad_logo.jpeg', 'Represents all students in the College of Medicine and Health Sciences.'),
    ('Social and Management Science Students Association', 'SAMSSA', 'samssa_logo.jpeg', 'For students in the College of Social and Management Sciences.'),
    ('College of Science Students Association', 'COSSA', 'cossa_logo.jpeg', 'For students in the College of Sciences.'),
    ('Institute of Electrical and Electronics Engineers ABUAD', 'IEEE ABUAD', 'ieee_abuad_logo.jpeg', 'Student branch of the IEEE at ABUAD.')
ON CONFLICT (name) DO NOTHING; -- Avoid errors if organizations already exist

-- Insert default settings (as expected by app.py admin_settings)
INSERT INTO settings (setting_key, setting_value, description)
VALUES
    ('site_name', 'ABUAD Student Voting', 'The name of the application displayed to users.'),
    ('max_votes_per_user', '1', 'Maximum number of votes a user can cast per poll (typically 1).'),
    ('results_visibility', 'public', 'Controls who can view poll results (e.g., public, voted_only, admin_only). Requires app logic changes to enforce fully.')
ON CONFLICT (setting_key) DO UPDATE SET
    setting_value = EXCLUDED.setting_value,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP; -- Update if settings already exist, especially site_name

-- Example of how to create an admin user (run this after table creation if needed)
-- INSERT INTO users (username, password_hash, is_admin)
-- VALUES ('admin', 'hashed_password_for_admin', TRUE);
-- Replace 'hashed_password_for_admin' with a password hash generated by generate_password_hash('your_admin_password')

-- --- How to use this schema: ---
-- 1. Save this content as a .sql file (e.g., schema.sql).
-- 2. Connect to your PostgreSQL database server using psql or a GUI tool.
-- 3. If you have an existing database for this app (e.g., voting_db):
--    psql -U your_postgres_user -d voting_db -f path/to/schema.sql
-- 4. If you need to create the database first:
--    CREATE DATABASE voting_db;
--    Then run the command from step 3.

-- --- Notes: ---
-- - The `poll_id` column in the `vote` table is crucial for the `UNIQUE (user_id, poll_id)`
--   constraint.
-- - The `ON DELETE CASCADE` clauses ensure that if a referenced record is deleted,
--   related records in other tables are also removed.
-- - `ON DELETE SET NULL` for `poll.organization_id` means if an organization is deleted,
--   the poll remains but is no longer associated with it.
-- - Timestamps are stored with time zone information (`TIMESTAMP WITH TIME ZONE`).
-- - Logo filenames are placeholders; you'll need to ensure the actual image files
--   are stored in your static assets directory (e.g., static/images/organization_logos/).
