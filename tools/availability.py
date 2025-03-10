
from langchain_core.tools import tool
from typing import Optional
import requests
import os
import json
from dotenv import load_dotenv


@tool
def availability(
    departure_airport: str = None,
    arrival_airport: str = None,
    start_time: str = None,
    round_trip: Optional[bool] = False, 
    end_time: Optional[ str] = None,
    adults: Optional[int] = 1,
    childs:  Optional[int] = 0,
    infants: Optional[int] = 0,
    
) -> dict:
    """Consult availability for a specif route.
    
    Mandatory Args: 
        departure_airport: String format with the IATA code of the airport
        arrival_airport: String format with the IATA code of the airport,
        start_time: String format (YYYY-MM-DD) Make sure this date is provided by the user,
    Optional Arguments: 
        round_trip: Optional[bool] = False, 
        end_time:  String format (YYYY-MM-DD),
        adults: Optional[int] = 1,
        childs:  Optional[int] = 0,
        infants: Optional[int] = 0,
        
    Returns:
        A dictionary with 'going' and 'goBack' flights.
        Fares as total price for all the passengers in the query
    """
    
    ENDPOINT = "/availability"

    # Cuerpo de la solicitud (payload)
    payload = {
        "departureLocation": departure_airport ,  # Código de ubicación de salida
        "arrivalLocation": arrival_airport,    # Código de ubicación de llegada
        "departureDate": start_time,  # Fecha de salida
        "isRoundTrip": round_trip,        # Si es ida y vuelta
        "returnDate": end_time,  # Fecha de regreso (si aplica) 
        "passengersType": [
            {"type": "ADT", "quantity": adults},  # Adultos
            {"type": "CHD", "quantity": childs},  # Niños
            {"type": "INF", "quantity": infants}   # Infantes
        ]
    }
    print(payload)

    BASE_URL = os.getenv("BASE_URL")
   
    try:
        
        response = requests.post(
            url=f"{BASE_URL}{ENDPOINT}",
            json=payload  # Enviar el cuerpo como JSON
        )
      
        
        if response.status_code == 200:

                print("¡Solicitud exitosa! Datos de disponibilidad:")
                print(json.dumps(response.json(), indent=4))  # Formatea la respuesta
        else:
            print(f"Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Ocurrió un error: {e}")
    return response.json()
