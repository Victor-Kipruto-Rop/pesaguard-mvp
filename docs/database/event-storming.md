# Event storming notes

## Purpose

This document captures the output of the big-picture event storming sessions used to identify PesaGuard's bounded contexts and domain events before service boundaries were finalized. It's kept as a reference for why the boundaries are where they are — not a live design tool.

## Method

Sessions followed the standard event-storming format: orange sticky notes for **domain events** (past tense, e.g., "Payment Initiated"), blue for **commands** (imperative, e.g., "Initiate Payment"), yellow for **aggregates**, pink for **external systems**, and purple for **policies** ("whenever X happens, do Y").

## Key timeline (payment happy path)

```
[Customer requests payment]
        │ command: Initiate Payment
        ▼
  Payment Requested ─────────────┐
        │                        │ policy: score before proceeding
        ▼                        ▼
  STK Push Sent            Fraud Pre-Check Requested
        │                        │
        ▼                        ▼
  Provider Callback Received   Fraud Score Returned
        │                        │
        └───────────┬────────────┘
                     ▼
             Payment Completed ──────┐
                     │               │ policy: post ledger entries
                     ▼               ▼
           Transaction Created   Ledger Entries Posted
                     │
                     ▼
        policy: notify customer + merchant
                     │
                     ▼
           Notification Sent (SMS/email)
```

## Key timeline (fraud hold path)

```
Transaction Created
        │ policy: evaluate velocity + device signals
        ▼
  Fraud Flagged ──────────┐
        │                 │ policy: hold settlement
        ▼                 ▼
  Case Opened for Review   Transaction Held
        │
        ▼ (analyst decision)
  Fraud Cleared  or  Fraud Confirmed
        │                     │
        ▼                     ▼
  Transaction Released   Transaction Reversed
```

## Boundary decisions that came out of these sessions

- **`fraud-service` was split from `risk-service`** after storming revealed two distinct temporal patterns: `fraud-service` reacts to a specific transaction in near-real-time; `risk-service` maintains longer-running behavioral/graph-based risk profiles that inform but don't gate individual transactions.
- **`transaction-service` and `ledger-service` were kept separate** despite always co-occurring, because their consistency and audit requirements differ: a transaction can be corrected via a new reversal event, but a ledger entry, once posted, is never mutated — only offset by a new balancing entry.
- **`notification-service` was made a thin fan-out layer** over `sms-service`/`email-service` rather than merged with either, since the events that trigger a notification (payment, fraud, settlement) are far more varied than the channels that deliver it.

See also: [Domain model](domain-model.md), [Event-Driven Design](../../architecture/event-driven-design.md), [Domain-Driven Design](../../architecture/domain-driven-design.md).
