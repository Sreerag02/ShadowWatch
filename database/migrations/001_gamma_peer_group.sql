-- Correct approved Gamma Bank metadata; operational records are unchanged.
-- Idempotent and guarded against an unexpected entity or existing peer group.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM entities
        WHERE entity_id = 'E003' AND entity_name = 'Gamma Bank' AND sector = 'Banking'
    ) THEN
        RAISE EXCEPTION 'Expected E003 Gamma Bank in Banking sector; migration aborted';
    END IF;
    IF EXISTS (
        SELECT 1 FROM entities
        WHERE entity_id = 'E003' AND peer_group IS NOT NULL AND peer_group <> 'Banking'
    ) THEN
        RAISE EXCEPTION 'Unexpected existing E003 peer group; migration aborted';
    END IF;
    UPDATE entities SET peer_group = 'Banking'
    WHERE entity_id = 'E003' AND peer_group IS NULL;
END
$$;
