CREATE TABLE IF NOT EXISTS clients (
    client_id BIGINT PRIMARY KEY,
    auth_user_id VARCHAR(64) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    prosthesis_id VARCHAR(100) NOT NULL,
    prosthesis_model VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO clients
(client_id, auth_user_id, username, full_name, email, prosthesis_id, prosthesis_model, country)
VALUES
(101, '11111111-1111-1111-1111-111111111111', 'prothetic1', 'Prothetic One', 'prothetic1@example.com', 'BP-ARM-001', 'BionicPRO Arm X1', 'Russia'),
(102, '22222222-2222-2222-2222-222222222222', 'prothetic2', 'Prothetic Two', 'prothetic2@example.com', 'BP-ARM-002', 'BionicPRO Arm X1', 'Russia'),
(103, '33333333-3333-3333-3333-333333333333', 'prothetic3', 'Prothetic Three', 'prothetic3@example.com', 'BP-HAND-003', 'BionicPRO Hand H2', 'Russia')
ON CONFLICT (client_id) DO NOTHING;
