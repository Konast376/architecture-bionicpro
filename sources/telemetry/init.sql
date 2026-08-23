CREATE TABLE IF NOT EXISTS telemetry (
    event_id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL,
    prosthesis_id VARCHAR(100) NOT NULL,
    event_time TIMESTAMP NOT NULL,
    movement VARCHAR(100) NOT NULL,
    success BOOLEAN NOT NULL,
    signal_strength DOUBLE PRECISION NOT NULL,
    battery_pct DOUBLE PRECISION NOT NULL,
    error_code VARCHAR(100)
);

INSERT INTO telemetry
(client_id, prosthesis_id, event_time, movement, success, signal_strength, battery_pct, error_code)
VALUES
(101, 'BP-ARM-001', NOW() - INTERVAL '2 hours', 'grip', TRUE, 0.91, 82, NULL),
(101, 'BP-ARM-001', NOW() - INTERVAL '90 minutes', 'release', TRUE, 0.87, 80, NULL),
(101, 'BP-ARM-001', NOW() - INTERVAL '40 minutes', 'rotate', FALSE, 0.45, 77, 'LOW_SIGNAL'),
(102, 'BP-ARM-002', NOW() - INTERVAL '3 hours', 'grip', TRUE, 0.88, 64, NULL),
(102, 'BP-ARM-002', NOW() - INTERVAL '1 hour', 'release', TRUE, 0.92, 61, NULL),
(103, 'BP-HAND-003', NOW() - INTERVAL '4 hours', 'pinch', TRUE, 0.79, 90, NULL),
(103, 'BP-HAND-003', NOW() - INTERVAL '30 minutes', 'grip', FALSE, 0.51, 86, 'ACTUATOR_RETRY');
