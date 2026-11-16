-- Proteção real de append-only no PostgreSQL para o ledger de consentimento.
-- Adicione esta migration após criar a tabela "ConsentEvent" pelo Prisma Migrate.

CREATE OR REPLACE FUNCTION prevent_consent_event_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'Append-only violation: operation % is prohibited on table %', TG_OP, TG_TABLE_NAME
    USING ERRCODE = '55000';
END;
$$;

DROP TRIGGER IF EXISTS trg_consent_event_no_update_delete ON "ConsentEvent";
CREATE TRIGGER trg_consent_event_no_update_delete
BEFORE UPDATE OR DELETE ON "ConsentEvent"
FOR EACH ROW
EXECUTE FUNCTION prevent_consent_event_mutation();

DROP TRIGGER IF EXISTS trg_consent_event_no_truncate ON "ConsentEvent";
CREATE TRIGGER trg_consent_event_no_truncate
BEFORE TRUNCATE ON "ConsentEvent"
FOR EACH STATEMENT
EXECUTE FUNCTION prevent_consent_event_mutation();

-- Hardening recomendado para a role usada pela aplicação web (ajuste o nome da role):
-- REVOKE UPDATE, DELETE, TRUNCATE ON "ConsentEvent" FROM app_runtime;
-- GRANT SELECT, INSERT ON "ConsentEvent" TO app_runtime;
