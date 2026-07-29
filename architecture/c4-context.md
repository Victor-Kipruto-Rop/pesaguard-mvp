# C4 Model — Level 1: System Context

## Purpose

This diagram shows PesaGuard as a single system within its environment: who uses it, and which external systems it depends on.

```
                    ┌───────────────┐
                    │   Merchant     │
                    │   (business)   │
                    └───────┬────────┘
                            │ initiates payments, views settlements
                            ▼
┌───────────────┐   ┌──────────────────┐   ┌───────────────┐
│   End Customer │──▶│    PesaGuard      │◀──│  Ops / Compliance│
│  (payer, via   │   │                    │   │  Analyst          │
│  STK push)     │   │  Mobile money      │   └───────────────┘
└───────────────┘   │  payment,          │
                     │  fraud detection,   │
                     │  and ledger platform │
                     └─────────┬────────────┘
                               │
        ┌──────────────────────┼──────────────────────┬───────────────────┐
        ▼                      ▼                      ▼                   ▼
┌───────────────┐    ┌─────────────────┐   ┌──────────────────┐  ┌────────────────┐
│  Safaricom      │    │  Airtel Money    │   │  Partner Banks    │  │  CBK Regulatory │
│  M-Pesa Daraja   │    │  API              │   │  (settlement rail)│  │  Reporting APIs │
│  API              │    │                  │   │                    │  │                 │
└───────────────┘    └─────────────────┘   └──────────────────┘  └────────────────┘
        ▲
        │
┌───────────────┐
│  Telco SIM-swap │
│  signal feed     │
└───────────────┘
```

## Actors and external systems

| Actor / system | Type | Relationship to PesaGuard |
|---|---|---|
| End customer | Person | Pays via STK push / USSD initiated through a merchant integration |
| Merchant | Person/organization | Initiates payment requests, reconciles settlements, manages sub-users via `organization-service` |
| Ops / compliance analyst | Person | Investigates fraud alerts, produces regulatory reports |
| Safaricom M-Pesa Daraja API | External system | STK push initiation, C2B/B2C callbacks — integrated via `mpesa-service` |
| Airtel Money API | External system | Payment initiation and callbacks — integrated via `airtel-money-service` |
| Partner banks | External system | Settlement transfers — integrated via `bank-service` |
| CBK regulatory reporting endpoints | External system | Scheduled regulatory submissions from `report-service` |
| Telco SIM-swap signal feed | External system | Consumed by `fraud-service` for SIM-swap correlation |

## Notes

This is the highest level of the C4 model — no internal service boundaries are shown here. See [`c4-container.md`](c4-container.md) for the service-level (container) view and [`c4-component.md`](c4-component.md) for the internal structure of a representative service.
