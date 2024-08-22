import os
import requests
import boto3
from openai import OpenAI
import uuid
from datetime import datetime
import time
import json
from utils.messages import send_interactive_select_place_type
ASSISTANT_ID = "asst_TrrPdpY4LqlWHSOatjVaFvxr"
CONVERSATIONS_TABLE_NAME = os.getenv("DB_CONVERSATIONS_TABLE_NAME")
ENTRIES_TABLE_NAME = os.getenv("DB_PROCESSED_WEBHOOK_EVENTS_TABLE_NAME")

dynamodb = boto3.client('dynamodb', region_name='us-east-1')
client = OpenAI()


def say_hello(arguments):
    language = arguments['language']
    if language == 'español' or language == 'spanish' or language == 'es':
        return """Hola, soy Ozzio tu Asistente Virtual Personal para descubrir, organizar y reservar tus planes en Madrid. Cómo puedo ayudarte? 🤗
    🔍 ¿Quieres que te busque qué hacer?
    📖 ¿Necesitas que haga una reserva?
    ℹ️ ¿Buscas información sobre algún plan?
    📍 ¿Tienes que organizar varios planes?
    Recuerda que si tienes alguna necesidad (PMR, Celiaco, Vegano...) no hay ningún problema, escríbelo para saberlo y adaptarme a ti.
    ¿Te gustaría saber todo lo que puedo hacer por ti? 
    *🇬🇧 If you need an English version, type "English* 🇬🇧
    Si deseas continuar, debes estar al tanto que estas aceptando nuestros términos y condiciones: https://ozzio.es/terminos-y-condiciones
    """
    elif language == 'english' or language == 'en' or language == 'inglés':
        return """Hello, I'm Ozzio, your Personal Virtual Assistant to discover, organize and book your plans in Madrid. How can I help you? 🤗
    🔍 Do you want me to find out what to do for you?
    📖 Do you need me to make a reservation?
    ℹ️ Are you looking for information about a plan?
    📍 Do you have to organize several plans?
    Remember that if you have any needs (PMR, Celiac, Vegan...) there is no problem, write it so I know and adapt to you.
    Would you like to know everything I can do for you?
    *If you need a Spanish version, type "Spanish*
    If you wish to continue, you must be aware that you are accepting our terms and conditions: https://ozzio.es/terminos-y-condiciones
    """


def get_message_event(eventId):
    try:
        response = dynamodb.get_item(
            TableName=ENTRIES_TABLE_NAME,
            Key={'eventId': {'S': eventId}}
        )
        return response['Item']
    except Exception as e:
        print('Error getting entries: ', e)
        return None
    
def create_message_event(eventId, message):
    dynamodb.put_item(
        TableName=ENTRIES_TABLE_NAME,
        Item={
            'eventId': {'S': eventId},
            'message': {'S': str(message)}
        }
    )
    
def get_conversations(phone):
    try:
        response = dynamodb.query(
            TableName=CONVERSATIONS_TABLE_NAME,
            IndexName='userPhoneGSI-dev',
            KeyConditionExpression='userPhone = :phone',
            ExpressionAttributeValues={
                ':phone': {'S': phone}
            }
        )
        
        if len(response['Items']) == 0:
            Exception("No conversations found")
        
        return response['Items']
        
    except Exception as e:
        print('Error getting conversations: ', e)
        return []
    
def create_conversation(phone, thread):
    pk, createdAt = generate_pk()
    dynamodb.put_item(
        TableName=CONVERSATIONS_TABLE_NAME,
        Item={
            'conversationId': {'S': pk},
            'createdAt': {'S': createdAt},
            'thread': {'S': thread},
            'userPhone': {'S': phone}
        }
    )
        
def initiate_interaction(user_message):
    my_thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=my_thread.id,
        role="user",
        content=user_message
    )

    return my_thread

def retrieve_thread(conversation):
    thread_id = conversation['thread']['S']
    thread = client.beta.threads.retrieve(thread_id)
    return thread

def trigger_assistant(thread, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant_id
    )

    return run

def get_run(thread_id, run_id):
    run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
    return run
    

def run_asistant(thread):
    run = trigger_assistant(thread, ASSISTANT_ID)
    
    while run.status in ['queued', 'in_progress', 'cancelling']:
        print(f"Run status: {run.status}")
        time.sleep(1)
        run = get_run(thread.id, run.id)
    return run

def run_tool_actions(run, thread):
    actions = run.required_action.submit_tool_outputs.tool_calls
    tool_outputs = []
    for action in actions:
        print(f"Action: {action}")
        tool_outputs.append(call_tool(action))
    if tool_outputs:
        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )    
    return run
        
def call_tool(action):
    tool_name = action.function.name
    arguments = json.loads(action.function.arguments)
    output = {}
    if tool_name == 'say_hello':
        output = say_hello(arguments)
    elif tool_name == 'search_place':
        output = interact_with_buttons(arguments['label'])
    else:
        output = "I'm sorry, I don't know how to do that yet."
    return {
        "tool_call_id": action.id,
        "output": output
    }

def interact(thread):
    run = run_asistant(thread)
    if run.status == 'requires_action':
        run = run_tool_actions(run, thread)
    # hacer el while para esperar a que el run esté completado
    while run.status in ['queued', 'in_progress', 'cancelling']:
        print(f"Run status: {run.status}")
        time.sleep(1)
        run = get_run(thread.id, run.id)
    if run.status == 'completed':
        return list(client.beta.threads.messages.list(thread_id=thread.id))
    return []

def interact_with_buttons(label):
    if label == "type":
        return 'Debes retornar un JSON con exactamente este formato {"next_action": "search_place", "label": "type", "values": ["Restaurante","Cafetería","Bar","Discoteca","Museo","Parque"]}'

def get_last_message(messages):
    max_timestamp = 0
    for message in messages:
        if message.created_at > max_timestamp:
            max_timestamp = message.created_at
            last_message = message
    return last_message
    
def generate_pk():
    key = str(uuid.uuid4())
    createdAt = str(int(datetime.now().timestamp()))
    pk = key + '_' + createdAt
    return pk, createdAt