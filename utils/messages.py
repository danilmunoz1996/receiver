import requests
import os


TOKEN = os.getenv("WHATSAPP_API_TOKEN")
URL = "https://graph.facebook.com/v20.0/304457169419514/messages"

headers = {
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json"
}

def base_interactive_message_content(to, header, body, footer):
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "+" + to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": header
            },
            "body": {
                "text": body
            },
            "footer": {
                "text": footer
            },
            "action": {
                "buttons": []
            }
        }
    }
        
def button_message(data):
    return {
        "type": "reply",
        "reply": {
            "id": data['id'],
            "title": data['label']
        }
    }
    
def whatsapp_interactive_message(to, header, body, footer, buttons):
    payload = base_interactive_message_content(to, header, body, footer)
    for button in buttons:
        payload["interactive"]["action"]["buttons"].append(button_message(button))
    return payload
        
def send_menu_interactive_message(to):
    header = "Bienvenido"
    body = "Te puedo ayudar con las siguientes opciones. ¿Cuál prefieres?"
    footer = "Prometo ser tu mejor asistente de viajes"
    
    buttons = [
        {
            "label": "🔎 BUSCAR",
            "id": "search-button",
        },
        {
            "label": "📍 CREAR ITINERARIO",
            "id": "itinerary-button"
        },
        {
            "label": "📅 RESERVAR",
            "id": "view-itineraries-button"
        }
    ]
    
    send_message(whatsapp_interactive_message(to, header, body, footer, buttons))
    
def send_interactive_select_place_type(to):
    header = "Selecciona el tipo de lugar"
    body = "¿Qué tipo de lugar quieres buscar?"
    footer = "Selecciona una opción"
    
    buttons = [
        {
            "label": "🍽️ Restaurante",
            "id": "restaurant-button"
        },
        {
            "label": "☕ Cafetería",
            "id": "cafe-button"
        },
        {
            "label": "🍺 Bar",
            "id": "bar-button"
        },
        {
            "label": "🎶 Discoteca",
            "id": "nightclub-button"
        },
        {
            "label": "🏛️ Museo",
            "id": "museum-button"
        },
        {
            "label": "🌳 Parque",
            "id": "park-button"
        }
    ]
    
    send_message(whatsapp_interactive_message(to, header, body, footer, buttons))

def send_text_message(to, message):
    
    content = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": message
        }
    }
    
    send_message(content)

def send_message(message):
    response = requests.post(URL, headers=headers, json=message)
    return response.json()