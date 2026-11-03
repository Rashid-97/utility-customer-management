# Utility Customer Management

A portfolio implementation of a utility provider's **Customer Management** bounded context. It demonstrates Domain-Driven Design, Clean Architecture, Ports & Adapters, and lightweight CQRS without expanding into a complete utility platform.

## What the project does

The API supports five operations:

- register a Subscriber with a first service account;
- add an account to an existing Subscriber;
- read a Subscriber and their accounts;
- read one SubscriberAccount;
- terminate an account.

`Subscriber` is the only Aggregate Root. `SubscriberAccount` belongs to it and can be created or terminated only through the aggregate.

```mermaid
flowchart TD
    A[Application submitted] --> B[Verify identity]
    B --> C[Find existing Subscriber]
    C --> D[Verify address through GIS boundary]
    D --> E[Check age and active address]
    E --> F{Existing Subscriber?}
    F -->|No| G[Create Subscriber and first account]
    F -->|Yes| H[Check Billing debt]
    H --> I[Add account]
    G --> J[Commit transaction]
    I --> J
```

The complete language and business rules are in [Domain](docs/domain.md).

## Architecture at a glance

```mermaid
flowchart LR
    API[FastAPI] --> APP[Application]
    APP --> DOMAIN[Domain]
    DOMAIN --> COMMON[Common foundations]
    API --> INFRA[Infrastructure composition]
    INFRA -. implements .-> APP
    INFRA -. implements .-> DOMAIN
    INFRA --> DB[(PostgreSQL)]
    INFRA --> EXT[Identity / GIS / Billing mocks]
```

Dependencies point inward. Domain code has no FastAPI, Pydantic, SQLAlchemy, or Infrastructure imports. Application handlers receive ports and a Unit of Work through constructor injection. Infrastructure provides SQLAlchemy persistence, query projections, and deterministic external-service adapters.

Writes use the `Subscriber` aggregate. Reads use direct SQLAlchemy projections against the same PostgreSQL database. Domain objects and ORM models are separate and mapped explicitly.

### GIS address verification

`AddressVerificationPort` belongs to Customer Management and asks only whether a `ServiceAddressId` is valid and serviceable. `MockAddressVerificationAdapter` simulates a synchronous response from an external GIS bounded context.

The adapter translates GIS-specific fields into the boolean required by the use case. It acts as an Anti-Corruption Layer: GIS terminology does not enter Customer Management handlers or Domain objects. A real GIS service is not implemented.

GIS verification and account uniqueness are different checks:

- GIS determines whether the address exists and is within the service area.
- Customer Management determines whether an active account already uses that address.

The detailed design is in [Architecture](docs/architecture.md). Design trade-offs are in [Architecture decisions](docs/decisions/README.md).

## Technology

| Concern | Choice |
|---|---|
| API | FastAPI and Pydantic 2 |
| Database | PostgreSQL 16 |
| Persistence | SQLAlchemy 2.x and Alembic |
| Driver | Psycopg 3 |
| Tests | pytest |
| Local runtime | Docker Compose or Python 3.11+ |

## Project structure

```text
src/customer_management/
├── common/           # Typed IDs, Entity, AggregateRoot, events, errors
├── domain/           # Subscriber aggregate, values, policies, repository port
├── application/      # Commands, queries, integration ports, Unit of Work
├── infrastructure/   # SQLAlchemy and deterministic mock adapters
├── api/              # FastAPI routes, schemas, composition, error mapping
└── main.py

migrations/           # Alembic migration
tests/unit/           # Domain and Application unit tests
docs/                 # Focused project documentation
```

## Run with Docker Compose

```sh
cp .env.example .env
docker compose up --build --detach
```

For PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build --detach
```

The API is available at `http://localhost:8000`; Swagger UI is at `http://localhost:8000/docs`.

Useful commands:

```sh
docker compose ps --all
docker compose logs migrate
docker compose down
```

`docker compose down` keeps the database volume. Adding `--volumes` deletes the Compose-managed database.

## Run with native Python

Python 3.11+ and PostgreSQL are required.

```sh
python -m venv .venv
```

Activate it with `. .venv/bin/activate` on Linux/macOS or `.venv\Scripts\Activate.ps1` in PowerShell. Then install and run:

```sh
python -m pip install --upgrade pip
python -m pip install -e ".[test]"
python -m alembic upgrade head
python -m uvicorn customer_management.main:app --reload
```

Set `DATABASE_URL` before running migrations or the API:

```text
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

## API

| Method | Path | Result |
|---|---|---|
| `POST` | `/subscribers` | Register a Subscriber and account |
| `GET` | `/subscribers/{subscriber_id}` | Read a Subscriber with accounts |
| `POST` | `/subscribers/{subscriber_id}/accounts` | Add an account |
| `GET` | `/subscribers/{subscriber_id}/accounts/{account_id}` | Read one account |
| `POST` | `/subscribers/{subscriber_id}/accounts/{account_id}/termination` | Terminate an account |

Example registration:

```sh
curl --request POST http://localhost:8000/subscribers \
  --header "Content-Type: application/json" \
  --data '{
    "document_number": "AZE-ADULT-001",
    "document_type": "NATIONAL_ID",
    "service_address_id": "SERVICE-ADDRESS-001",
    "city_code": "10",
    "street_code": "20",
    "building_code": "30",
    "apartment_code": "40"
  }'
```

New registration returns `201`. Registering the same verified identity with another valid address adds an account to the existing Subscriber and returns `200`.

Errors have one stable shape:

```json
{
  "code": "ACTIVE_ACCOUNT_ALREADY_EXISTS",
  "message": "A safe client-facing explanation."
}
```

See [API contract](docs/api.md) for request fields, status codes, and error semantics.

## Deterministic external scenarios

| Boundary | Input | Outcome |
|---|---|---|
| Identity | `NATIONAL_ID` / `AZE-ADULT-001` | Verified adult citizen |
| Identity | `PASSPORT` / `FOREIGN-ADULT-001` | Verified adult non-citizen |
| Identity | `NATIONAL_ID` / `AZE-MINOR-001` | Verified identity; age rule rejects application |
| Identity | Unknown type/number | Verification rejection |
| Identity | `IDENTITY-SERVICE-UNAVAILABLE` | External-service failure |
| GIS | `SERVICE-ADDRESS-001` to `SERVICE-ADDRESS-003` | Address found and serviceable |
| GIS | Unknown address ID | Address verification rejection |
| GIS | `ADDRESS-SERVICE-UNAVAILABLE` | External-service failure |

The Billing adapter is debt-free by default. In isolated tests it can be configured with account IDs that should report debt or as unavailable.

## Verification

Run unit tests with:

```sh
python -m pytest
```

After starting Compose, check the migration and API with:

```sh
docker compose ps --all
docker compose logs migrate
curl --fail http://localhost:8000/openapi.json
```

## Scope

Included:

- the Customer Management aggregate and business rules;
- PostgreSQL persistence and one Alembic migration;
- five HTTP operations;
- deterministic Identity, GIS, and Billing adapters;
- focused Domain and Application unit tests.

Not included:

- actual Identity, GIS, Billing, or ServiceAddress bounded contexts;
- real external-service clients;
- authentication and authorization;
- event dispatching, a broker, or a transactional outbox;
- event sourcing, separate read storage, production observability, or deployment automation.

Domain Events are recorded in memory for successful aggregate changes. They are not published outside the process.

## Documentation

- [Domain](docs/domain.md) — language, aggregate boundaries, and business rules
- [Architecture](docs/architecture.md) — layers, dependencies, persistence, and integrations
- [API contract](docs/api.md) — HTTP inputs, outputs, statuses, and errors
- [Architecture decisions](docs/decisions/README.md) — rationale and trade-offs
- [Unit testing guide](docs/testing/unit-testing.md) — conventions for contributors

The Event Storming model is available as an [image](assets/images/event-storming.png) and an [interactive Miro board](https://miro.com/app/board/uXjVHidNvYc=/?share_link_id=795842628547).
