# Database functions catalog

## Purpose

Documents PostgreSQL functions used across service schemas — primarily trigger functions that enforce invariants too critical to trust to application code alone (see [`../constraints/constraints-catalog.md`](../constraints/constraints-catalog.md) for the constraints they back).

## `ledger` schema

### `balanced_batch_sum(transaction_id UUID) RETURNS NUMERIC`

Sums `ledger_entries.amount` for a transaction, with credits negated, returning zero for a balanced batch. Used by a `CHECK` constraint trigger on `ledger_entries` insert to reject an unbalanced posting before commit.

```sql
CREATE FUNCTION ledger.balanced_batch_sum(p_transaction_id UUID) RETURNS NUMERIC AS $$
  SELECT COALESCE(SUM(
    CASE entry_type WHEN 'debit' THEN amount ELSE -amount END
  ), 0)
  FROM ledger.ledger_entries
  WHERE transaction_id = p_transaction_id;
$$ LANGUAGE sql STABLE;
```

### `set_updated_at() RETURNS TRIGGER`

Standard `updated_at` maintenance trigger, applied to every table across every schema per [`../../docs/database/schema-conventions.md`](../../docs/database/schema-conventions.md) — application code never sets `updated_at` directly.

```sql
CREATE FUNCTION shared.set_updated_at() RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## `audit` schema

### `compute_hash(prev_hash TEXT, payload JSONB) RETURNS TEXT`

Computes `sha256(prev_hash || payload::text)`, used by a `BEFORE INSERT` trigger on `audit_entries` to hash-chain each entry to the previous one, making tampering with historical entries detectable (recomputing the chain from the start reveals any break).

```sql
CREATE FUNCTION audit.compute_hash(p_prev_hash TEXT, p_payload JSONB) RETURNS TEXT AS $$
  SELECT encode(digest(coalesce(p_prev_hash, '') || p_payload::text, 'sha256'), 'hex');
$$ LANGUAGE sql IMMUTABLE;
```

## `fraud` schema

### `velocity_window_count(customer_id UUID, window_minutes INT) RETURNS INT`

Used by `fraud-service`'s synchronous pre-transaction check path as a fallback when the Redis-backed velocity read model ([`../../architecture/cqrs-design.md`](../../architecture/cqrs-design.md)) is unavailable — a slower, durable-source equivalent so fraud checks degrade gracefully rather than fail open.

```sql
CREATE FUNCTION fraud.velocity_window_count(p_customer_id UUID, p_window_minutes INT) RETURNS INT AS $$
  SELECT COUNT(*)::INT
  FROM fraud.transaction_events
  WHERE customer_id = p_customer_id
    AND created_at > now() - (p_window_minutes || ' minutes')::interval;
$$ LANGUAGE sql STABLE;
```

## Usage policy

New trigger functions require sign-off from a database-owning service lead, since they run inside the write transaction and directly affect write latency and lock behavior — see [`../../CONTRIBUTING.md#database-migrations`](../../CONTRIBUTING.md#database-migrations).

See also: [`../constraints/constraints-catalog.md`](../constraints/constraints-catalog.md), [`../procedures/procedures-catalog.md`](../procedures/procedures-catalog.md).
