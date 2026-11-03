# Architecture

This document describes technical boundaries and dependency choices. Business rules live in [Domain](domain.md); HTTP details live in [API contract](api.md).

## Dependency rule

```text
FastAPI API  ──>  Application  ──>  Domain  ──>  Common
      │                 ▲
      └─ composition ───┤
Infrastructure ─────────┘
```

Dependencies point inward:

- Common contains reusable domain foundations and depends on no project layer.
- Domain contains the aggregate and repository abstraction.
- Application contains use cases, external ports, read models, and Unit of Work abstraction.
- Infrastructure implements persistence, queries, Unit of Work, and external ports.
- API maps HTTP contracts to Application inputs and composes concrete dependencies.

Domain and Application do not import FastAPI, Pydantic, or SQLAlchemy.

## Code organization

```text
src/customer_management/
├── common/
├── domain/subscriber/
│   ├── events/
│   ├── policies/
│   └── repositories/
├── application/
│   ├── abstractions/
│   ├── ports/
│   └── subscriber/
│       ├── commands/
│       └── queries/
├── infrastructure/
│   ├── integrations/
│   └── persistence/
├── api/
└── main.py
```

Each command or query has its own folder and handler. Handlers receive dependencies in their constructors. FastAPI `Depends` is used only at the API composition boundary.

No mediator, command bus, generic repository, or third-party dependency injection container is used.

## Domain and persistence

`Subscriber` is the only Aggregate Root. `SubscriberAccount` is stored in a separate table but remains part of the same aggregate.

Domain objects and SQLAlchemy models are separate. Infrastructure maps the complete aggregate in both directions.

The database contains:

- `subscribers` with a unique `(document_type, document_number)` constraint;
- `subscriber_accounts` with a foreign key to Subscriber;
- a unique SubscriberCode constraint;
- a PostgreSQL partial unique index on `service_address_id` where status is `ACTIVE`;
- status and termination-state check constraints.

The Application performs readable business checks first. Database constraints protect the same data under concurrent requests.

`SqlAlchemyUnitOfWork` owns a request-scoped session and transaction. Registration writes a new Subscriber and first account atomically. Rollback runs when a use case exits without a successful commit. Recorded Domain Events are cleared only after commit.

## Commands and queries

Command handlers load and change the aggregate through `SubscriberRepository`.

Query handlers use `SubscriberQueryPort`, implemented by direct SQLAlchemy projections. They do not load the aggregate for read-only responses. Commands and queries share one PostgreSQL database.

This is lightweight CQRS: there is no event sourcing, separate read database, or message bus.

## External boundaries

Application owns three outbound contracts:

- `IdentityVerificationPort`
- `AddressVerificationPort`
- `OutstandingDebtPort`

Infrastructure currently provides deterministic mock adapters.

### GIS adapter

`MockAddressVerificationAdapter` models a synchronous request to an external GIS bounded context. Its private GIS-shaped response contains address and service-area facts. The adapter translates those fields into the boolean expected by `AddressVerificationPort`.

This is an Anti-Corruption Layer: Customer Management does not depend on GIS response names or models. An unavailable GIS raises an external-service error; it is not treated as an invalid address.

The mock demonstrates the boundary only. It does not make a network call or implement GIS or ServiceAddress master data.

## API composition and errors

`api/dependencies.py` creates request-scoped handlers and Unit of Work instances. Stateless mock adapters and the SQLAlchemy engine/session factory are cached where appropriate.

Domain and Application errors contain no HTTP concerns. Central FastAPI handlers map them to stable status codes and error bodies. Raw database errors and traces are not returned to clients.

## Deliberately excluded

The current design does not include:

- real external-service clients;
- GIS, Identity, Billing, or ServiceAddress implementations;
- event publication, broker, or transactional outbox;
- authentication, authorization, or production observability;
- event sourcing or separate command/read databases.

These can be added behind the existing boundaries when a real requirement appears.
