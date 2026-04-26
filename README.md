# Smart Parking Management System

**Master Research Project — Thesis · Embedded Systems Engineering**
**Student:** Swathi Chandrashekaraiah (7218877)
**Supervisor:** Prof. Dr.-Ing. Björn Schäfer, Fachhochschule Dortmund
**Reference Location:** Klinikum Dortmund, Hohe Straße 33, Dortmund

### Languages
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![HTML](https://img.shields.io/badge/HTML-E34F26?style=flat&logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS-1572B6?style=flat&logo=css3&logoColor=white)
![YAML](https://img.shields.io/badge/YAML-CB171E?style=flat&logoColor=white)
![JSON](https://img.shields.io/badge/JSON%20%2F%20NGSI--LD-000000?style=flat&logoColor=white)

### Frameworks & Tools
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
![FIWARE](https://img.shields.io/badge/FIWARE%20Orion--LD-4CB8C4?style=flat&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat&logo=mongodb&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare%20Tunnel-F38020?style=flat&logo=cloudflare&logoColor=white)
![Postman](https://img.shields.io/badge/Postman-FF6C37?style=flat&logo=postman&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-06B6D4?style=flat&logo=tailwindcss&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=flat&logo=pydantic&logoColor=white)
---

## Overview

This project implements a **Smart Parking Management System** as a Digital Twin using the FIWARE platform and the Smart Data Model specification. It enables real-time tracking of parking space availability, smart spot allocation based on user needs, and exposes a REST + WebSocket API for integration with external navigation systems.

The system manages the parking garage of **Klinikum Dortmund** and is designed to act as the **data and management backend** for a broader Smart Parking solution. The vehicle navigation and mission routing component (Autoware-based) is handled separately by a colleague and consumes this system's API output.

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│              Smart Parking Management System         │
│                                                     │
│  ┌──────────────┐    ┌───────────────────────────┐  │
│  │  FastAPI     │    │  FIWARE Orion Context     │  │
│  │  Backend     │◄──►│  Broker (NGSI-LD)         │  │
│  │  (main.py)   │    │  Digital Twin             │  │
│  └──────┬───────┘    └───────────────────────────┘  │
│         │                                           │
│  ┌──────▼───────┐    ┌───────────────────────────┐  │
│  │  Web UI      │    │  WebSocket Interface       │  │
│  │  (index.html)│    │  → Navigation System       │  │
│  └──────────────┘    │    (colleague's component) │  │
│                      └───────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Key Technologies

| Component | Technology |
|---|---|
| Backend API | Python, FastAPI |
| Context Broker | FIWARE Orion-LD (NGSI-LD) |
| Data Model | Smart Data Models — `SmartIndoorParkingSpot` |
| Frontend UI | HTML, Tailwind CSS, Lucide Icons |
| Deployment | Docker Compose |
| Package Manager | `uv` (Python) |
| Public Tunnel | Cloudflare Tunnel (`cloudflared`) |
| API Testing & Entity Registration | Postman |

---

## Features

- **Digital Twin** of the Klinikum Dortmund parking garage modelled via FIWARE Orion-LD
- **Smart spot allocation** based on user preferences (disabled access, female priority, EV charging)
- **Real-time status updates** — spots are marked `occupied` in the Digital Twin upon booking
- **WebSocket push** — assigned spot coordinates are broadcast to connected navigation clients the moment a booking is confirmed
- **REST API** for full CRUD management of parking entities
- **Web UI** — a mission control dashboard to find and lock a spot in one click
- **Cloudflare Tunnel** — exposes the local server publicly so Postman and external systems can reach it from anywhere

---

## Project Structure

```
Smart-Parking-Management-System/
├── main.py                    # FastAPI application — all API endpoints
├── index.html                 # Mission Control web UI
├── docker-compose-fiware.yaml # FIWARE stack (Orion-LD + MongoDB)
├── entities/                  # NGSI-LD entity definitions (parking spots & garage)
├── pyproject.toml             # Python project metadata and dependencies
├── uv.lock                    # Locked dependency versions
└── .python-version            # Python version pin
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Python 3.x](https://www.python.org/) (see `.python-version`)
- [`uv`](https://github.com/astral-sh/uv) — fast Python package manager

Install `uv` if not already available:
```bash
curl -Lf https://astral.sh/uv/install.sh | sh
```

---

## Getting Started

### 1. Start the FIWARE Stack

```bash
docker compose -f docker-compose-fiware.yaml up -d
```

This starts:
- **Orion-LD** Context Broker on `http://localhost:1026`
- **MongoDB** as the persistence backend for the context broker

Verify Orion is running:
```bash
curl http://localhost:1026/version
```

### 2. Install Python Dependencies

```bash
uv sync
```

### 3. Expose the API Publicly via Cloudflare Tunnel

To make the system accessible from anywhere (e.g. for Postman testing from a different machine, or for your colleague's navigation system to connect remotely), a **Cloudflare Tunnel** is used to expose the local FastAPI server to the internet without needing to open firewall ports or configure a static IP.

**Install `cloudflared`:**
```bash
# macOS
brew install cloudflare/cloudflare/cloudflared

# Linux (Debian/Ubuntu)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

**Start a quick tunnel** (no login required for temporary URLs):
```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Cloudflare will print a temporary public URL, for example:
```
https://your-tunnel-name.trycloudflare.com
```

Use this URL in Postman instead of `localhost`. The tunnel stays active as long as the terminal is running.

> **Note:** The public URL changes every time you restart the tunnel. For a persistent URL, you can set up a named tunnel with a Cloudflare account and a custom domain.

---

### 4. Register Parking Entities via Postman

Entity definitions for the parking garage and individual spots are located in the `entities/` folder. These are loaded into the FIWARE Digital Twin using **Postman**.

**Step-by-step:**

1. Open Postman and create a new **POST** request
2. Set the URL to your Cloudflare tunnel URL (or `http://127.0.0.1:8000` if running locally):
   ```
   https://your-tunnel-name.trycloudflare.com/parking-garage
   ```
3. Under the **Body** tab, select **raw** and set the type to **JSON**
4. Paste the contents of the relevant entity file from the `entities/` folder
5. Click **Send** — a `200 OK` response confirms the entity was registered in the Digital Twin

Repeat this for each parking spot entity in the `entities/` folder.

**Example request in Postman:**

| Field | Value |
|---|---|
| Method | `POST` |
| URL | `https://<your-tunnel>.trycloudflare.com/parking-garage` |
| Body type | `raw` → `JSON` |
| Body content | Contents of the entity JSON file |

> The `/parking-garage` endpoint forwards the entity payload directly to the FIWARE Orion-LD Context Broker running locally on port `1026`.

---

### 5. Start the Application

```bash
uv run uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
The web UI can be accessed at `http://127.0.0.1:8000/`.
Interactive API docs (Swagger) are at `http://127.0.0.1:8000/docs`.

When the Cloudflare Tunnel is running, all of the above are also reachable via the public tunnel URL.

---

## API Reference

### Parking Spot Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/find-spot` | Find the best available spot based on preferences |
| `POST` | `/book-spot` | Mark a spot as `occupied` in the Digital Twin |
| `POST` | `/clear-spot/{spot_id}` | Reset a specific spot to `free` |
| `POST` | `/clear-all-spots` | Reset all spots to `free` |
| `POST` | `/parking-garage` | Register a new parking garage entity |
| `DELETE` | `/delete-garage/{garage_id}` | Delete a garage and all its associated spots |

### WebSocket

| Endpoint | Description |
|---|---|
| `WS /ws/machine` | Real-time channel — broadcasts assigned spot ID and coordinates to connected navigation clients upon every successful booking |

---

### `POST /find-spot`

Finds the optimal available parking spot based on the user's requirements. Standard spots (no special categories) are preferred by default; special spots are only returned when explicitly requested.

**Request body:**
```json
{
  "requires_disabled": false,
  "requires_female": false,
  "requires_ev": false
}
```

**Response (success):**
```json
{
  "status": "success",
  "assigned_spot_id": "urn:ngsi-ld:SmartIndoorParkingSpot:KlinikumDortmund:A01",
  "spot_number": "A01",
  "coordinates": [51.5050, 7.4900],
  "message": "Spot reserved successfully."
}
```

---

### `POST /book-spot`

Locks the previously identified spot by updating its status to `occupied` in the Digital Twin, then broadcasts the coordinates over the WebSocket to any connected navigation client.

**Request body:**
```json
{
  "spot_id": "urn:ngsi-ld:SmartIndoorParkingSpot:KlinikumDortmund:A01"
}
```

---

### WebSocket — `/ws/machine`

Connect from the navigation system to receive real-time booking events:

```json
{
  "event": "NEW_BOOKING",
  "spot_id": "urn:ngsi-ld:SmartIndoorParkingSpot:KlinikumDortmund:A01",
  "coordinates": [51.5050, 7.4900],
  "timestamp": "2025-03-07T10:30:00.000000"
}
```

The navigation component (handled separately) connects here and uses the `coordinates` field as its navigation target.

---

## Smart Data Model

Parking spots are modelled using the **FIWARE Smart Data Model** `SmartIndoorParkingSpot`. Each spot entity holds:

| Attribute | Type | Description |
|---|---|---|
| `id` | URN | Unique NGSI-LD identifier |
| `status` | Property | `free` or `occupied` |
| `category` | Property | List: `forDisabled`, `forWomen`, `forElectricCharging`, or empty |
| `spotNumber` | Property | Human-readable spot label (e.g. `A01`) |
| `location` | GeoProperty | GeoJSON `Point` with spot coordinates |
| `refParkingGarage` | Relationship | Link to the parent parking garage entity |
| `occupancyModified` | Property | Timestamp of the last status change |

---

## Web UI — Mission Control

The frontend (`index.html`) provides a mission control dashboard:

- Toggle preferences (Disabled Access, Female Priority, EV Charging)
- Click **Find & Lock Spot** to automatically find the best spot and book it
- A live mission log displays all API events
- On success, the assigned spot number and coordinates are displayed
- Coordinates are simultaneously pushed over WebSocket to the navigation system

The UI communicates with the FastAPI backend at `http://127.0.0.1:8000`.

---

## Integration with Navigation System

This system serves as the **parking management and data layer**. The navigation component (Autoware-based, developed by a project colleague) integrates as follows:

1. The navigation client connects to `ws://localhost:8000/ws/machine`
2. When a user books a spot via the UI or API, this system pushes a `NEW_BOOKING` event with the target spot's coordinates
3. The navigation system uses these coordinates as the goal pose for route planning within the parking garage

This clean interface decouples parking management from vehicle routing.

---

## Scope & Limitations

> **Note:** The vehicle mission control and route planning component (Autoware integration) described in the project assignment is **outside the scope of this repository**. This system provides the parking data backend and the WebSocket interface that the navigation system consumes. The navigation part is handled by a project colleague.

---

## References

- [FIWARE Orion-LD Context Broker](https://github.com/FIWARE/context.Orion-LD)
- [Smart Data Models — Parking](https://smartdatamodels.org/)
- [Autoware Framework](https://autoware.org/autoware-overview/)
- [NGSI-LD API Specification](https://www.etsi.org/deliver/etsi_gs/CIM/001_099/009/01.08.01_60/gs_CIM009v010801p.pdf)
- [Cloudflare Tunnel (`cloudflared`)](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Postman](https://www.postman.com/)
