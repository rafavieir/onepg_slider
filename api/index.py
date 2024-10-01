from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import os
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Necessário para o Flash messages

# Coloque as chaves que você obteve do Google reCAPTCHA
RECAPTCHA_SITE_KEY = '6LeXyFMqAAAAAFUw3xscVtTcUQcV6xaUBiMWIdGp'
RECAPTCHA_SECRET_KEY = '6LeXyFMqAAAAAK2GWd9phGzq9Lz5IckJOXPTKUkz'

# Limitação de tentativas
rate_limit = defaultdict(list)  # Armazena os timestamps dos envios por IP
RATE_LIMIT_WINDOW = timedelta(minutes=5)  # Janela de 5 minutos
RATE_LIMIT_MAX_ATTEMPTS = 5  # Número máximo de tentativas

def load_cards():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'cards_data.txt')
    
    cards = []
    with open(file_path, 'r') as file:
        for line in file:
            title, description, image = line.strip().split('|')
            cards.append({'title': title, 'description': description, 'image': image})
    return cards

def load_footer():
    base_path = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_path, 'footer_informations.txt')
    
    footer = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                if ':' in line:
                    key, value = line.split(':', 1)
                    footer[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"Arquivo {file_path} não encontrado.")
    
    return footer

@app.route('/')
def index():
    footer_info = load_footer()
    cards = load_cards()
    return render_template('index.html', cards=cards, footer_info=footer_info, recaptcha_site_key=RECAPTCHA_SITE_KEY)

@app.route('/send_message', methods=['POST'])
def send_message():
    client_ip = request.remote_addr
    current_time = datetime.now()

    # Verifica se o IP já está registrado
    if client_ip not in rate_limit:
        rate_limit[client_ip] = []
    
    # Limpa tentativas antigas
    rate_limit[client_ip] = [timestamp for timestamp in rate_limit[client_ip] if timestamp > current_time - RATE_LIMIT_WINDOW]
    
    # Verifica se o limite de tentativas foi atingido
    if len(rate_limit[client_ip]) >= RATE_LIMIT_MAX_ATTEMPTS:
        return "Limite de tentativas excedido. Tente novamente mais tarde.", 429

    recaptcha_token = request.form.get('g-recaptcha-response')

    # Valida o reCAPTCHA v3
    recaptcha_response = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
        'secret': RECAPTCHA_SECRET_KEY,
        'response': recaptcha_token
    })
    result = recaptcha_response.json()

    if result['success'] and result['score'] >= 0.5:
        # Processamento do formulário
        # (Por exemplo: enviar email ou salvar no banco de dados)

        # Registra a tentativa de envio
        rate_limit[client_ip].append(current_time)

        return "Mensagem enviada com sucesso!"
    else:
        return "Erro ao validar o reCAPTCHA. Tente novamente.", 400

if __name__ == '__main__':
    app.run(debug=True)
