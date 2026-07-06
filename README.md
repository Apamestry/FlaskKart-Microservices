# FlaskKart Microservices

A microservices decomposition of the FlaskKart monolith, built for a cloud computing course
to demonstrate independent scaling, deployment, and fault isolation.

## Architecture

| Service | Port | Owns | Database |
|---|---|---|---|
| **API Gateway** | 5000 | Users, JWT auth, request routing | `gateway-db` (3308) |
| **View Service** | 5001 | Products (catalog, stock) | `view-db` (3309) |
| **Search Service** | 5002 | Nothing (stateless) — calls View Service | none |
| **Cart Service** | 5003 | Cart items | `cart-db` (3310) |
| **Buy Service** | 5004 | Orders, checkout, payment simulation | `buy-db` (3311) |
| **Frontend** | 5005 | UI only — talks to the Gateway, never to services directly | none |

The Gateway is the only entry point external clients (the frontend) ever talk to. It
authenticates requests and proxies them to the right internal service. Internal services
talk to each other directly over the Docker network by service name (e.g.
`http://view-service:5001`) and verify a shared-secret JWT independently rather than
blindly trusting the Gateway.

## Status

🚧 **Stage 1 complete**: folder structure, skeleton Flask app per service (health-check
only), and `docker-compose.yml` wiring all 9 containers (5 services + 4 databases) onto a
shared network.

Still to build: Gateway auth + routing, View Service product catalog, Search Service,
Cart Service, Buy Service, and the Frontend.

## Running it

```bash
docker compose up --build
```

Then check each service is alive:
```bash
curl http://localhost:5000/health   # api-gateway
curl http://localhost:5001/health   # view-service
curl http://localhost:5002/health   # search-service
curl http://localhost:5003/health   # cart-service
curl http://localhost:5004/health   # buy-service
```

Each should return `{"service": "<name>", "status": "ok"}`.

## Environment files

Each service has its own `.env` (gitignored) and `.env.example` (tracked). The root
`.env` configures the database containers themselves (used by `docker-compose.yml`'s
variable substitution). All services share the same `JWT_SECRET` so they can
independently verify tokens issued by the Gateway.
