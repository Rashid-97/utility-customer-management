# Utility Customer Management

A Python/FastAPI portfolio implementation of the **Customer Management bounded context** for a utility provider. It demonstrates Domain-Driven Design, Clean Architecture, Ports & Adapters, and lightweight CQRS without expanding into a generic CRM or a complete utility platform.

## Table of Contents

- [Overview / Business Context](#overview--business-context)
- [Business Workflow](#business-workflow)
- [Event Storming](#event-storming)
- [Domain Model and Business Rules](#domain-model-and-business-rules)
- [Architecture and Approach](#architecture-and-approach)
- [Design and Architectural Patterns](#design-and-architectural-patterns)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Deterministic Mock Scenarios](#deterministic-mock-scenarios)
- [API Usage](#api-usage)
- [Verification](#verification)
- [Scope and Limitations](#scope-and-limitations)
- [Further Documentation](#further-documentation)

## Overview / Business Context

A person applies for utility service at a verified address. Customer Management verifies identity and minimum age, recognizes an existing Subscriber, prevents multiple active accounts at the same service address, checks the external Billing boundary for outstanding debt, and creates or terminates accounts through the Subscriber Aggregate Root.

The bounded context owns these concepts:

- **Subscriber:** a person recognized by the utility provider and the sole Aggregate Root.
- **SubscriberAccount:** an Entity owned by a Subscriber that represents utility service at one address.
- **SubscriberCode:** a business identifier composed from city, street, building, and apartment codes.
- **IdentityDocument:** verified identity data received from the external Identity boundary.

ServiceAddress master data, identity registries, and billing records remain outside this bounded context. Customer Management communicates with those boundaries through replaceable application ports and currently uses deterministic mock adapters. For address verification, the mock adapter models a synchronous request to an external GIS bounded context; the GIS implementation itself remains outside this repository.

## Business Workflow

The application supports registering a Subscriber, adding an account to an existing Subscriber, and terminating an account.

```mermaid
flowchart TD
    A[Application submitted] --> B[Verify identity]
    B -->|Rejected| R1[Return business rejection]
    B -->|Verified| C[Find Subscriber by document type and number]
    C --> D[Verify service address]
    D -->|Invalid| R2[Return business rejection]
    D -->|Valid| E[Check minimum age]
    E -->|Under 18| R3[Reject application]
    E --> F[Check active account at address]
    F -->|Already active| R4[Reject duplicate active address]
    F -->|Available| G{Existing Subscriber?}
    G -->|No| H[Create Subscriber and first account]
    G -->|Yes| I[Check debt on existing accounts]
    I -->|Debt exists| R5[Reject account creation]
    I -->|Debt-free| J[Add account through Subscriber]
    H --> K[Commit atomically]
    J --> K
```

Account termination loads the Subscriber and target account, checks the account for outstanding debt, transitions it from `ACTIVE` to `TERMINATED`, and commits. It retains the account and historical SubscriberCode rather than deleting the record.

## Event Storming

The Event Storming model captures application submission and verification, Subscriber recognition, account creation, debt checks, and account termination.

![Utility Customer Management Event Storming diagram](assets/images/event-storming.png)

[Open the interactive Event Storming board in Miro](https://miro.com/app/board/uXjVHidNvYc=/?share_link_id=795842628547)

`ApplicationSubmitted` and `ApplicationVerified` describe the discovery-level business flow, but they are not tactical Domain Event classes in the current implementation. The Aggregate records only successful state changes: `SubscriberCreated`, `SubscriberAccountCreated`, and `SubscriberAccountTerminated`.

## Domain Model and Business Rules

```mermaid
classDiagram
    class Entity
    class AggregateRoot
    class Subscriber
    class SubscriberAccount
    class IdentityDocument
    class SubscriberCode
    class ServiceAddressId
    class DomainEvent

    Entity <|-- AggregateRoot
    Entity <|-- SubscriberAccount
    AggregateRoot <|-- Subscriber
    Subscriber "1" *-- "1..*" SubscriberAccount : owns
    Subscriber --> IdentityDocument : created from
    SubscriberAccount --> SubscriberCode
    SubscriberAccount --> ServiceAddressId
    AggregateRoot o-- DomainEvent : records
```

`Subscriber` is the only Aggregate Root. `SubscriberAccount` is an Entity inside that aggregate, so account creation and termination always go through `Subscriber`. Domain objects use typed UUID-backed identities, while HTTP and PostgreSQL expose regular UUID representations.

Core invariants:

- A Subscriber may own multiple accounts, but each account belongs to exactly one Subscriber.
- At most one `ACTIVE` account may exist for a ServiceAddressId across all Subscribers.
- A verified identity uses the composite `(document_type, document_number)` key; registration must not create a duplicate Subscriber.
- A new Subscriber and the first account are persisted in the same transaction.
- Adding an account for an existing Subscriber requires all existing accounts to be debt-free.
- Terminating an account requires that account to be debt-free.
- A terminated account cannot be terminated again and is retained rather than physically deleted.
- SubscriberCode is unique and is built from typed CityCode, StreetCode, BuildingCode, and ApartmentCode values.
- Identity verification, address verification, and internal address uniqueness are separate rules.

Value Objects are frozen dataclasses without a shared ValueObject base class. Domain code does not import FastAPI, Pydantic, SQLAlchemy, or Infrastructure.

## Architecture and Approach

The project combines DDD tactical modeling with Clean Architecture and Ports & Adapters. Lightweight CQRS separates state-changing handlers from read projections while both sides share one PostgreSQL database.

```mermaid
flowchart LR
    API[FastAPI / API] --> APP[Application]
    APP --> DOMAIN[Domain]
    DOMAIN --> COMMON[Common foundations]
    API --> INFRA[Infrastructure composition]
    INFRA -. implements ports .-> APP
    INFRA -. implements repository .-> DOMAIN
    INFRA --> DB[(PostgreSQL)]
    INFRA --> EXT[Identity / GIS / Billing mocks]
```

The dependency rule points inward: Domain is independent of Application, API, persistence, and external services. API maps Pydantic contracts to application commands and queries. Infrastructure implements repository, Unit of Work, query, and integration abstractions.

```mermaid
sequenceDiagram
    participant Client
    participant API as FastAPI route
    participant Handler as RegisterSubscriberHandler
    participant Ports as Identity / Address / Billing ports
    participant Domain as Subscriber aggregate
    participant UoW as Repository / Unit of Work
    participant DB as PostgreSQL

    Client->>API: POST /subscribers
    API->>Handler: RegisterSubscriberCommand
    Handler->>Ports: Verify identity and address
    Handler->>UoW: Find Subscriber and check address
    UoW->>DB: Query persisted state
    Handler->>Ports: Check debt when Subscriber exists
    Handler->>Domain: Create Subscriber or add account
    Handler->>UoW: Save aggregate and commit
    UoW->>DB: Atomic transaction
    Handler-->>API: Registration result
    API-->>Client: 201 Created or 200 OK
```

Command handlers mutate the Aggregate through a Unit of Work. Query handlers use a dedicated read port backed by direct SQLAlchemy projections. Domain exceptions remain HTTP-agnostic and are translated centrally into stable API errors.

### GIS address-verification boundary

`AddressVerificationPort` belongs to the Customer Management Application layer and expresses only the fact needed by its use cases: whether a `ServiceAddressId` is valid and serviceable. Its current `MockAddressVerificationAdapter` simulates a synchronous response from an external GIS bounded context and translates the GIS-shaped response into the port's `bool` result.

This translation acts as an Anti-Corruption Layer: GIS-specific response fields and terminology remain inside the Infrastructure adapter and do not leak into Customer Management handlers or Domain objects. Returning a boolean does not weaken that boundary; it is the complete decision currently required by the consuming use case. An unavailable GIS is represented separately as an external-service failure rather than as an invalid address.

GIS verification and internal address uniqueness are separate concerns. GIS answers whether an address exists and is within the service area; Customer Management checks its own persistence boundary to ensure that no active SubscriberAccount already uses that address.

## Design and Architectural Patterns

| Pattern | Where it is used | Purpose |
|---|---|---|
| Repository | Domain `SubscriberRepository`; SQLAlchemy implementation in Infrastructure | Keep persistence concerns outside the Domain |
| Unit of Work | Application `UnitOfWork`; `SqlAlchemyUnitOfWork` in Infrastructure | Make commit/rollback explicit and related changes atomic |
| Ports & Adapters | Identity, Address, Billing, repository, and query ports with Infrastructure adapters | Replace external services and persistence mechanisms without changing use cases |
| CQRS | Per-use-case command and query handlers sharing one database | Use the Aggregate for writes and efficient projections for reads |
| Adapter | Mock Identity, Address, and Billing adapters, plus SQLAlchemy persistence adapters, implement inward-facing port contracts | Translate infrastructure-specific behavior into interfaces understood by the Application and Domain layers |
| Strategy | Command handlers receive interchangeable verification, debt-checking, persistence, and query implementations through abstract ports | Let a use case vary its external behavior without changing its orchestration logic |
| Named Factory Methods | `Subscriber.create()`, `SubscriberAccount._create()`, and `SubscriberCode.create()` | Centralize valid object construction and make creation intent explicit |

The implementation intentionally avoids a mediator, command bus, generic repository, event sourcing, event dispatcher, and transactional outbox because the current use cases do not require them.

## Technology Stack

| Concern | Technology |
|---|---|
| Language | Python 3.11+ |
| HTTP API | FastAPI |
| API schemas | Pydantic 2 |
| Database | PostgreSQL 16 in Compose |
| ORM | SQLAlchemy 2.x with synchronous sessions |
| PostgreSQL driver | Psycopg 3 |
| Migrations | Alembic |
| Application server | Uvicorn |
| Local orchestration | Docker Compose |
| Unit testing | pytest |

## Project Structure

```text
src/customer_management/
├── common/                     # Typed IDs, Entity, AggregateRoot, events, errors
├── domain/
│   └── subscriber/             # Aggregate, Entity, Value Objects, policy, events
│       ├── events/
│       ├── policies/
│       └── repositories/       # Domain repository abstraction
├── application/
│   ├── abstractions/           # Unit of Work contract
│   ├── ports/                  # Integration and read-side contracts
│   └── subscriber/
│       ├── commands/           # Register, create account, terminate account
│       └── queries/            # Get Subscriber and account
├── infrastructure/
│   ├── integrations/           # Deterministic mock adapters
│   └── persistence/            # ORM, mappers, repository, UoW, queries
├── api/
│   ├── routers/                # FastAPI endpoints
│   ├── schemas/                # Pydantic contracts
│   ├── dependencies.py         # Composition root
│   └── exception_handlers.py   # HTTP error translation
└── main.py                     # FastAPI entry point

migrations/                     # Alembic schema revisions
tests/unit/                      # Focused unit tests
docs/                            # Specifications and decisions
compose.yaml                    # PostgreSQL, migration, and API services
```

Each command or query has its own folder. The Application organization is use-case oriented within Clean Architecture; it is not a full vertical-slice architecture.

## Getting Started

### Docker Compose

Docker Compose is the shortest path to PostgreSQL, applied migrations, and a running API.

```sh
cp .env.example .env
docker compose up --build --detach
```

In PowerShell, use `Copy-Item .env.example .env` if the `cp` alias is unavailable. The API is exposed at `http://localhost:8000`, with interactive documentation at `http://localhost:8000/docs`.

```sh
docker compose ps --all
docker compose logs migrate
docker compose run --rm migrate
docker compose down
```

`docker compose down` retains the PostgreSQL volume. Adding `--volumes` permanently deletes the Compose-managed development database.

### Native Python

Python 3.11+ and a reachable PostgreSQL instance are required.

```sh
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e .
```

Activate the environment with `. .venv/bin/activate` on Linux/macOS or `.venv\Scripts\Activate.ps1` in PowerShell. Set `DATABASE_URL` from `.env.example` to a synchronous Psycopg URL:

```text
postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE
```

Alembic and the application read `DATABASE_URL` from the process environment; `.env` is not loaded implicitly in native mode.

```sh
python -m alembic upgrade head
python -m uvicorn customer_management.main:app --reload
```

## Deterministic Mock Scenarios

| Boundary | Input | Mock data | Outcome |
|---|---|---|---|
| Identity | `NATIONAL_ID` / `AZE-ADULT-001` | John Doe, born `1990-05-15`, citizenship `AZ` | Verified adult citizen |
| Identity | `PASSPORT` / `FOREIGN-ADULT-001` | Jane Smith, born `1985-09-20`, citizenship `GE` | Verified adult non-citizen |
| Identity | `NATIONAL_ID` / `AZE-MINOR-001` | Michael Brown, born `2012-03-10`, citizenship `AZ` | Verified identity; rejected as underage |
| Identity | Unknown type/number pair | — | Business verification rejection |
| Identity | `IDENTITY-SERVICE-UNAVAILABLE` | — | External service unavailable |
| GIS / Address verification | `SERVICE-ADDRESS-001` through `SERVICE-ADDRESS-003` | Simulated GIS response: address found and within service area | Serviceable |
| GIS / Address verification | Unknown address ID | Simulated GIS response: address not found and outside service area | Business verification rejection |
| GIS / Address verification | `ADDRESS-SERVICE-UNAVAILABLE` | — | External service unavailable |

The Billing mock is debt-free by default. Direct adapter tests can pass account IDs to `MockOutstandingDebtAdapter(outstanding_account_ids=...)` or set `unavailable=True` to simulate an outage.

## API Usage

Base resource: `/subscribers`

| Method | Path | Use case | Success response |
|---|---|---|---|
| `POST` | `/subscribers` | Register a Subscriber and account | `201`; `200` for an existing Subscriber |
| `GET` | `/subscribers/{subscriber_id}` | Get a Subscriber with accounts | `200` |
| `POST` | `/subscribers/{subscriber_id}/accounts` | Add an account | `201` |
| `GET` | `/subscribers/{subscriber_id}/accounts/{account_id}` | Get one account | `200` |
| `POST` | `/subscribers/{subscriber_id}/accounts/{account_id}/termination` | Terminate an account | `204` |

New resource UUIDs are generated by the server. Authoritative name, birth date, and citizenship values come from the Identity boundary.

### Register a Subscriber

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

A successful new registration returns `201 Created`:

```json
{
  "subscriber_id": "00000000-0000-0000-0000-000000000000",
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-05-15",
  "citizenship": "AZ",
  "accounts": [
    {
      "account_id": "00000000-0000-0000-0000-000000000000",
      "subscriber_code": "10203040",
      "service_address_id": "SERVICE-ADDRESS-001",
      "status": "ACTIVE"
    }
  ]
}
```

Repeat registration with the same verified identity and another serviceable address to add an account to the existing Subscriber; that branch returns `200 OK`.

### Work with created resources

Replace placeholders with UUIDs returned by the API:

```sh
curl http://localhost:8000/subscribers/{subscriber_id}

curl --request POST http://localhost:8000/subscribers/{subscriber_id}/accounts \
  --header "Content-Type: application/json" \
  --data '{
    "service_address_id": "SERVICE-ADDRESS-002",
    "city_code": "10",
    "street_code": "20",
    "building_code": "30",
    "apartment_code": "41"
  }'

curl http://localhost:8000/subscribers/{subscriber_id}/accounts/{account_id}

curl --request POST \
  http://localhost:8000/subscribers/{subscriber_id}/accounts/{account_id}/termination
```

Failures use a stable response shape:

```json
{
  "code": "ACTIVE_ACCOUNT_ALREADY_EXISTS",
  "message": "A safe client-facing explanation."
}
```

Typical status codes are `404` for missing resources, `409` for state or uniqueness conflicts, `422` for rejected/invalid business input, and `503` for external service outages.

## Verification

After starting Compose, verify PostgreSQL health, the Alembic revision, and API availability:

```sh
docker compose ps --all
docker compose logs migrate
docker compose exec db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version_num FROM alembic_version;"'
curl --fail http://localhost:8000/openapi.json
```

Run focused unit tests with:

```sh
python -m pytest
```

The representative HTTP flow should return `201`, `200`, `201`, `200`, and `204`. Also verify:

- `AZE-MINOR-001` returns `422` with `APPLICANT_UNDERAGE`.
- An unknown identity returns `422` with `IDENTITY_VERIFICATION_REJECTED`.
- Reusing an active service address returns `409` with `ACTIVE_ACCOUNT_ALREADY_EXISTS`.
- Terminating an already terminated account returns `409` with `SUBSCRIBER_ACCOUNT_ALREADY_TERMINATED`.
- Identity or Address outage sentinel values return `503` with `EXTERNAL_SERVICE_UNAVAILABLE`.

```sh
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, document_type, document_number FROM subscribers;"'
docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT id, subscriber_id, service_address_id, status FROM subscriber_accounts;"'
```

## Scope and Limitations

The repository contains the Customer Management vertical slice: domain model, PostgreSQL persistence, application commands and queries, deterministic external-service mocks, five HTTP operations, centralized error mapping, migrations, and focused unit tests.

Intentionally outside the current scope:

- Meter readings, invoices, payments, and an actual Billing bounded context
- An actual GIS bounded context, ServiceAddress master-data management, and real GIS integration
- Real identity, address, or billing integrations
- Event dispatching, a broker, and a transactional outbox
- Event sourcing or separate command/read databases
- Production authentication, authorization, observability, and deployment configuration
- A comprehensive integration and end-to-end test suite

Domain Events are recorded as in-memory domain facts, but no reliable publication or consumer behavior is implied. Mock adapters are demonstration and testing boundaries, not production integrations.

## Further Documentation

- [Domain specification](docs/domain.md)
- [Architecture specification](docs/architecture.md)
- [HTTP API contract](docs/api.md)
- [Architecture decision log](docs/decisions/README.md)
- [Unit testing standards](docs/testing/unit-testing.md)
