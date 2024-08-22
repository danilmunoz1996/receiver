from flask import Flask, request, jsonify
app = Flask(__name__)

from utils.utils import get_message_event, create_message_event, get_conversations, create_conversation, initiate_interaction, interact, get_last_message, retrieve_thread
from utils.messages import send_menu_interactive_message, send_text_message
VERIFY_TOKEN = 'plane-old'

# Define health check endpoint /
@app.route('/')
def health_check():
    return jsonify({"status": "success", "message": "Server is up and running"}), 200


@app.route('/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == VERIFY_TOKEN:
                print('WEBHOOK_VERIFIED')
                return challenge, 200
            else:
                return jsonify({"status": "Forbidden"}), 403

    elif request.method == 'POST':
        
        print("Primera Data: ", data)
        
        
        if request.is_json:
            data = request.get_json()
            
            entry = get_message_event(data['entry'][0]['id'])
            
            
            if entry is not None:
                print("Message content: ", data)
                print("Existent Message content: ", entry)
                return jsonify({"status": "success"}), 200
            else:
                if 'messages' in data['entry'][0]['changes'][0]['value'].keys():
                    create_message_event(data['entry'][0]['id'], data)
                    # obtener el phone number
                    print("Data: ", data)
                    data = data['entry'][0]['changes'][0]['value']['messages'][0]
                    phone = data['from']
                    print("Phone number: ", phone)
                    
                    # obtener conversaciones asociadas al phone number
                    conversations = get_conversations(phone)
                    user_message = data['text']['body']
                    
                    
                    newConversation = len(conversations) == 0
                    if not newConversation:
                        print("Conversations: ", conversations)
                        # obtener thread
                        thread = retrieve_thread(conversations[0])
                    else:
                        # crear interaccion con bot
                        thread = initiate_interaction(user_message)
                        
                    messages = interact(thread)
                    if len(messages) > 0:
                        last_message = get_last_message(messages)
                        value = last_message.content[0].text.value
                        print("Last message: ", last_message)
                        # enviar mensaje
                        print(f"RESPUESTA BOT: {value}")
                        send_text_message(phone, value)
                        print("Message sent")
                        
                    # crear conversacion
                    if newConversation:
                        create_conversation(phone, thread.id)
                        print("Conversation created")
                        resp = send_menu_interactive_message(phone)
                        print("Menu sent, response: ", resp)
                    
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "failure", "message": "Invalid request"}), 400

    return jsonify({"status": "failure", "message": "Method not allowed"}), 405



        





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
