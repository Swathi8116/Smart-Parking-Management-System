from fastapi import FastAPI, HTTPException, Body, WebSocket
from fastapi.responses import HTMLResponse
from starlette.responses import FileResponse
from pydantic import BaseModel
import requests
from datetime import datetime
import json


app = FastAPI(title="Smart Parking Mission Control")

ORION_URL = "http://127.0.0.1:1026/ngsi-ld/v1/entities"

class BookingRequest(BaseModel):
    requires_disabled: bool = False
    requires_female: bool = False
    requires_ev: bool = False

def get_clean_value(attribute):
    """Helper function to extract the actual value from NGSI-LD format"""
    if not attribute:
        return None
    
    if isinstance(attribute, dict) and 'value' in attribute:
        return attribute['value']
    
    return attribute

class ConnectionManager:
    def __init__(self):
        # Store active machine connections
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print("Machine connected to Mission Control")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_coordinates(self, spot_id: str, coordinates: list):
        """Sends the target coordinates to all connected machines"""
        payload = {
            "event": "NEW_BOOKING",
            "spot_id": spot_id,
            "coordinates": coordinates,
            "timestamp": datetime.now().isoformat()
        }
        for connection in self.active_connections:
            await connection.send_json(payload)

manager = ConnectionManager()

@app.get("/")
async def home():
    return FileResponse('index.html')

@app.websocket("/ws/machine")
async def machine_socket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection open and listen for heartbeats/logs from machine
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Machine disconnected")

@app.post("/find-spot")
def find_parking_spot(preferences: BookingRequest):
    """
    Finds the best parking spot based on user preferences.
    """
    
    try:
        response = requests.get(
            f"{ORION_URL}?type=SmartIndoorParkingSpot",
            headers={"Accept": "application/ld+json"}
        )
        response.raise_for_status()
        all_spots = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not connect to FIWARE: {str(e)}")


    suitable_spots = []
    
    for spot in all_spots:
        
        spot_id = spot.get("id")
        
        status = get_clean_value(spot.get("status"))
        categories = get_clean_value(spot.get("category"))
        
        if status != "free":
            continue

        spot_weight = 0
        is_match = True
        
        if "forElectricCharging" in categories:
            spot_weight += 1

        if "forDisabled" in categories:
            spot_weight += 1

        if "forWomen" in categories:
            spot_weight += 1

        if preferences.requires_ev:
            if "forElectricCharging" not in categories:
                is_match = False
        
        if preferences.requires_disabled:
            if "forDisabled" not in categories:
                is_match = False
        
        if preferences.requires_female:
            if "forWomen" not in categories:
                is_match = False
           
       
        if not preferences.requires_disabled and not preferences.requires_female:
            if "forDisabled" in categories or "forWomen" in categories:
                is_match = False

        if is_match:
            suitable_spots.append((spot, spot_weight))

    
    if not suitable_spots:
        return {"status": "failure", "message": "No suitable spots available."}
    
    
    best_spot = None
    min_weight = float("inf")

    for spot, weight in suitable_spots:
        if weight < min_weight:
            min_weight = weight
            best_spot = spot
   
    
    location_data = get_clean_value(best_spot.get("location"))
    coordinates = location_data.get("coordinates") if location_data else [0,0]

    return {
        "status": "success",
        "assigned_spot_id": best_spot.get("id"),
        "spot_number": get_clean_value(best_spot.get("spotNumber")),
        "coordinates": coordinates,
        "message": "Spot reserved successfully."
    }
    
class BookingConfirmation(BaseModel):
    spot_id: str

@app.post("/book-spot")
async def book_parking_spot(booking: BookingConfirmation):
    """
    Updates the Digital Twin status to 'occupied' so no one else can take it.
    """
    spot_id = booking.spot_id
    
    try:
        response = requests.get(
            f"{ORION_URL}/{spot_id}",
            headers={"Accept": "application/ld+json"}
        )
        response.raise_for_status()
        response = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not connect to FIWARE: {str(e)}")

    coords = response['location']['value']['coordinates']

    update_payload = {
        "status": {
            "type": "Property",
            "value": "occupied"
        },
        
        "occupancyModified": {
            "type": "Property",
            "value": {
                "@type": "DateTime",
                "@value": "2023-10-27T12:00:00Z" 
            }
        }
    }
    
    url = f"http://localhost:1026/ngsi-ld/v1/entities/{spot_id}/attrs"
    
    try:
        response = requests.patch(
            url,
            json=update_payload,
            headers={
                "Content-Type": "application/json",
                
            }
        )
        response.raise_for_status() 
        
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to update FIWARE: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection Error: {str(e)}")

    await manager.send_coordinates(spot_id, coords)

    return {
        "status": "success", 
        "message": f"Spot {spot_id} is now locked. Other users will not see it."
    }

@app.post("/parking-garage")
def create_parking_garage(garage_data: dict = Body(...)):
    """
    Registers a new Parking Garage entity in the FIWARE Context Broker.
    """
    try:
        response = requests.post(
            ORION_URL,
            json=garage_data,
            headers={
                "Content-Type": "application/json",
                # Note: NGSI-LD usually requires a Link header for context, 
                # but for a local test, application/json often suffices.
            }
        )

        if response.status_code == 201:
            return {"status": "success", "message": "Parking Garage registered successfully."}
        else:
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Orion Error: {response.text}"
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection Error: {str(e)}")

@app.post("/clear-all-spots")
def clear_parking_spot():
    """
    Finds the best parking spot based on user preferences.
    """
    
    try:
        response = requests.get(
            f"{ORION_URL}?type=SmartIndoorParkingSpot",
            headers={"Accept": "application/ld+json"}
        )
        response.raise_for_status()
        all_spots = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not connect to FIWARE: {str(e)}")

    
    for spot in all_spots:
        
        spot_id = spot.get("id")
        
        status = get_clean_value(spot.get("status"))
        categories = get_clean_value(spot.get("category"))
        
        if status != "free":
            update_payload = {
                    "status": {
                        "type": "Property",
                        "value": "free"
                    },
                    
                    "occupancyModified": {
                        "type": "Property",
                        "value": {
                            "@type": "DateTime",
                            "@value": "2023-10-27T12:00:00Z" 
                        }
                    }
                }

    
            url = f"http://localhost:1026/ngsi-ld/v1/entities/{spot_id}/attrs"
    
            try:
                response = requests.patch(
                    url,
                    json=update_payload,
                    headers={
                        "Content-Type": "application/json",
                        
                    }
                )
                response.raise_for_status() 
                
            except requests.exceptions.HTTPError as e:
                raise HTTPException(status_code=400, detail=f"Failed to update FIWARE: {response.text}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Connection Error: {str(e)}")

    return {
        "status": "success", 
        "message": f"{len(all_spots)} Spots are now free."
    }

@app.post("/clear-spot/{spot_id}")
def clear_single_parking_spot(spot_id: str):
    """
    Resets a specific parking spot status to 'free' in the Digital Twin.
    """
    
    update_payload = {
        "status": {
            "type": "Property",
            "value": "free"
        },
        "occupancyModified": {
            "type": "Property",
            "value": {
                "@type": "DateTime",
                "@value": "2023-10-27T12:00:00Z" 
            }
        }
    }

    url = f"http://localhost:1026/ngsi-ld/v1/entities/{spot_id}/attrs"
    
    try:
        response = requests.patch(
            url,
            json=update_payload,
            headers={
                "Content-Type": "application/json",
            }
        )
        # Check if the spot actually exists before trying to update
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Spot {spot_id} not found in FIWARE.")
            
        response.raise_for_status() 
        
    except requests.exceptions.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to update FIWARE: {response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection Error: {str(e)}")

    return {
        "status": "success", 
        "message": f"Spot {spot_id} is now free and available for new bookings."
    }


@app.delete("/delete-garage/{garage_id:path}")
def delete_garage(garage_id: str):
    HEADERS = {
    "Accept": "application/ld+json"
    }
    try:
        # 1. Query spots linked to the garage
        query_url = f"{ORION_URL}/entities"
        params = {
            "type": "SmartIndoorParkingSpot",
            "q": f"refParkingGarage=={garage_id}"
        }

        resp = requests.get(query_url, headers=HEADERS, params=params)
        resp.raise_for_status()
        spots = resp.json()

        deleted_spots = []

        # 2. Delete each spot
        for spot in spots:
            spot_id = spot["id"]
            del_resp = requests.delete(f"{ORION_URL}/entities/{spot_id}")
            if del_resp.status_code == 204:
                deleted_spots.append(spot_id)

        # 3. Delete the garage
        garage_resp = requests.delete(f"{ORION_URL}/entities/{garage_id}")
        if garage_resp.status_code != 204:
            raise HTTPException(
                status_code=garage_resp.status_code,
                detail="Failed to delete ParkingGarage"
            )

        return {
            "message": "Garage and related spots deleted successfully",
            "garageId": garage_id,
            "deletedSpots": deleted_spots,
            "spotsDeletedCount": len(deleted_spots)
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))
