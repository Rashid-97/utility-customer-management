# Architecture Decisions

This file records why the design looks the way it does. Current behavior is defined in [Domain](../domain.md), [Architecture](../architecture.md), and [API contract](../api.md).

| Decision | Reason and trade-off |
|---|---|
| One `Subscriber` Aggregate Root | Account creation and termination belong to Subscriber invariants. A separate account table does not create a second aggregate. |
| `SubscriberAccount` is an Entity | It has identity and lifecycle, but all mutations still go through Subscriber. |
| Typed UUID IDs | `Id[Subscriber]` and `Id[SubscriberAccount]` prevent accidental mixing while remaining easy to store and expose as UUIDs. |
| Frozen dataclasses for values | Python already provides immutability and value equality; a ValueObject base class would add ceremony. |
| Composite identity key | Document numbers are not assumed globally unique, so Subscriber identity lookup uses `(document_type, document_number)`. |
| External `ServiceAddressId` reference | Address lifecycle and master data belong outside Customer Management. This context stores only the reference it needs. |
| GIS-backed address port | Registration needs an immediate serviceability answer, so the current boundary is synchronous. The adapter translates GIS response fields and protects the Customer Management model. |
| Registration handles existing Subscribers | One person may have several service accounts. A known identity continues through the same use case instead of being rejected. |
| Domain repository, Application integration ports | The aggregate defines its persistence needs; use cases define the external capabilities they consume. |
| Separate Domain and ORM models | The Domain remains independent of SQLAlchemy. Explicit mapping makes the boundary visible. |
| Unit of Work | Subscriber and account changes commit or roll back together. |
| Application check plus partial unique index | The Application returns a clear conflict; PostgreSQL still protects active-address uniqueness during races. |
| Lightweight CQRS with one database | Aggregate writes and projected reads stay clear without the cost of a bus or separate read store. |
| Constructor injection | Handler dependencies remain explicit and replaceable. FastAPI composition stays at the outer boundary. |
| Explicit termination endpoint | Termination changes business state and retains history; it is not deletion. |
| In-memory Domain Events only | Events express completed domain facts. No current integration requires a dispatcher, broker, or outbox. |
| Deterministic external mocks | The sample demonstrates integration boundaries without implementing Identity, GIS, Billing, or ServiceAddress systems. |

## Options intentionally not used

The project avoids a mediator, command bus, generic repository, specification framework, event sourcing, separate read database, external dependency injection container, and transactional outbox.

These patterns are not rejected in general. They are omitted because the current use cases do not justify their cost.
