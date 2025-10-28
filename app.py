# Bibliotecas necessarias serao Importadas Abaixo
# Necessario instalação
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import requests
import pymysql
import mercadopago
import json
import base64
import threading
import time
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Inicio APP
app = Flask(__name__)
app.secret_key = 'gabriel'

# -------------------------------
# 🔐 Configuração do Bling com atualização automática de token
# -------------------------------
CLIENT_ID = "8e4a69ebc4af56dcea9a2efcb6746062a0d1eddd"
CLIENT_SECRET = "5d34ac1c0fc7103495212b262510984a74d729f0497502220c185406f5c9"
REFRESH_URL = "https://www.bling.com.br/Api/v3/oauth/token"
TOKEN_FILE = "bling_tokens.json"
BASE_API_URL = "https://www.bling.com.br/Api/v3/produtos"

import os, json, time, requests

def carregar_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            return json.load(f)
    return None

def salvar_tokens(tokens):
    tokens['timestamp'] = int(time.time())  # segundos corretos
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=4)
    print("💾 Tokens atualizados e salvos com sucesso.")

def gerar_novo_token(refresh_token):
    print("🔄 Renovando token do Bling...")

    # Gera cabeçalho de autenticação Basic Base64(client_id:client_secret)
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # Corpo da requisição
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    resposta = requests.post(REFRESH_URL, headers=headers, data=data)

    if resposta.status_code == 200:
        tokens = resposta.json()
        salvar_tokens(tokens)
        print("✅ Novo token de acesso gerado e salvo com sucesso.")
        return tokens
    else:
        print("❌ Erro ao renovar token:", resposta.status_code, resposta.text)
        raise Exception("Falha ao renovar token do Bling")

def obter_access_token():
    tokens = carregar_tokens()
    if not tokens:
        raise Exception("⚠️ Nenhum token salvo. Gere o primeiro manualmente.")

    # Se o token expirou (1 hora = 3600 segundos)
    if int(time.time()) - tokens.get("timestamp", 0) > 3600:
        tokens = gerar_novo_token(tokens["refresh_token"])

    return tokens["access_token"]

def verificar_token_periodicamente():
    while True:
        try:
            # 🔁 sempre lê o token atualizado do arquivo
            tokens = carregar_tokens()
            if not tokens:
                print("⚠️ Nenhum token salvo, aguardando configuração inicial.")
                time.sleep(3300)
                continue

            tempo_decorrido = int(time.time()) - tokens.get("timestamp", 0)

            # verifica se passou 55 minutos (3300 segundos)
            if tempo_decorrido > 3300:
                print("⏰ Tempo expirado, tentando renovar token...")
                # sempre recarrega o refresh_token mais recente
                tokens = carregar_tokens()
                gerar_novo_token(tokens["refresh_token"])
        except Exception as e:
            print(f"⚠️ Erro ao renovar token automaticamente: {e}")
        time.sleep(3300)  # verifica a cada 55 minutos



# -------------------------------
# Configuração de e-mail
# -------------------------------
EMAIL_REMETENTE = "castanhogabriel639@gmail.com"
SENHA_EMAIL = "hvch nwoc klwn qsyv"

# Mercado Pago SDK com TOKEN de TESTE
sdk = mercadopago.SDK("APP_USR-6020544812998995-051312-d1d6d3580d0d57524411a722c6287ddf-2435196279")

def enviar_email(destinatario, assunto, mensagem_html):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem_html, 'html'))
        with smtplib.SMTP('smtp.gmail.com', 587) as servidor:
            servidor.starttls()
            servidor.login(EMAIL_REMETENTE, SENHA_EMAIL)
            servidor.send_message(msg)
    except Exception as e:
        print(f"Erro ao enviar e-mail: {str(e)}")

def conectar_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='flask_loja',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def home_redirect():
    return render_template('index.html')

@app.route('/ajuda')
def ajuda():
    return render_template('ajuda.html')

@app.route('/adicionar_carrinho', methods=['POST'])
def adicionar_carrinho():
    produto_id = request.form.get('produto_id')
    nome = request.form.get('nome')
    preco_raw = request.form.get('preco', '0')
    preco_str = str(preco_raw).replace(',', '.')
    try:
        preco = float(preco_str)
    except ValueError:
        flash('❌ Preço inválido para o produto.')
        return redirect(url_for('listar_produtos'))
    imagem_url = request.form.get('imagem_url', '')
    descricao = request.form.get('descricao', '')
    if 'carrinho' not in session:
        session['carrinho'] = []
    session['carrinho'].append({
        'id': produto_id,
        'nome': nome,
        'preco': preco,
        'imagem_url': imagem_url,
        'descricao': descricao,
        'quantidade': 1
    })
    session.modified = True
    flash(f'✅ "{nome}" foi adicionado ao carrinho.')
    return redirect(url_for('listar_produtos'))

@app.route('/remover_item/<produto_id>')
def remover_item(produto_id):
    if 'carrinho' in session:
        for i, item in enumerate(session['carrinho']):
            if item['id'] == produto_id:
                del session['carrinho'][i]
                break
        session.modified = True
    return redirect(url_for('carrinho'))

@app.route('/atualizar_frete', methods=['POST'])
def atualizar_frete():
    data = request.get_json()
    session['frete'] = {
        'valor': data['valor'],
        'prazo': data['prazo'],
        'cidade': data['cidade'],
        'uf': data['uf']
    }
    return jsonify({'ok': True})

@app.route('/carrinho')
def carrinho():
    carrinho = session.get('carrinho', [])
    subtotal = sum(item['preco'] * item.get('quantidade', 1) for item in carrinho)
    frete_info = session.get('frete')
    frete_valor = frete_info['valor'] if frete_info else 0.0
    total = subtotal + frete_valor
    return render_template('carrinho.html', carrinho=carrinho, subtotal=subtotal, total=total, frete=frete_info)

@app.route('/admin/excluir_pedido/<int:pedido_id>', methods=['POST'])
def excluir_pedido(pedido_id):
    try:
        conn = conectar_db()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM itens_pedido WHERE pedido_id = %s", (pedido_id,))
            cursor.execute("DELETE FROM pedidos WHERE id = %s", (pedido_id,))
            conn.commit()
        conn.close()
        flash("Pedido excluído com sucesso.")
    except Exception as e:
        flash(f"Erro ao excluir pedido: {str(e)}")
    return redirect(url_for('admin_pedidos'))

@app.route('/admin/marcar_entregue/<int:pedido_id>', methods=['POST'])
def marcar_entregue(pedido_id):
    try:
        conn = conectar_db()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE pedidos SET entregue = NOT COALESCE(entregue, 0) WHERE id = %s", (pedido_id,))
            conn.commit()
        conn.close()
        flash("Status do pedido atualizado.")
    except Exception as e:
        flash(f"Erro ao atualizar status: {str(e)}")
    return redirect(url_for('admin_pedidos'))

@app.route('/limpar_carrinho')
def limpar_carrinho():
    session.pop('carrinho', None)
    return redirect(url_for('carrinho'))

# ✅ Agora o token é sempre renovado automaticamente
@app.route('/produtos')
def listar_produtos():
    pagina = request.args.get('pagina', default=1, type=int)
    id_categoria = request.args.get('idCategoria')
    params = {'pagina': pagina}
    if id_categoria:
        params['idCategoria'] = id_categoria

    try:
        token = obter_access_token()
        headers = {'Accept': 'application/json', 'Authorization': f'Bearer {token}'}
        response = requests.get(BASE_API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        produtos = data.get("data", [])
        for produto in produtos:
            produto['descricaoCurta'] = produto.get("descricaoCurta", "Descrição não disponível")
        return render_template("produtos.html", produtos=produtos)
    except requests.exceptions.RequestException as e:
        return f"Erro ao acessar a API: {str(e)}<br>Resposta: {response.text if response else 'Sem resposta'}"

@app.route('/checkout')
def checkout():
    carrinho = session.get('carrinho', [])
    if not carrinho:
        return "Carrinho vazio."
    items = []
    for item in carrinho:
        preco_str = str(item['preco']).replace(',', '.')
        preco = round(float(preco_str), 2)
        quantidade = int(item.get('quantidade', 1))
        items.append({"title": item['nome'], "quantity": quantidade, "unit_price": preco, "currency_id": "BRL"})
    frete_info = session.get('frete')
    if frete_info:
        frete_valor = float(frete_info.get('valor', 0))
        if frete_valor > 0:
            items.append({
                "title": f"Frete - {frete_info.get('cidade', '')}/{frete_info.get('uf', '')}",
                "quantity": 1,
                "unit_price": round(frete_valor, 2),
                "currency_id": "BRL"
            })
    preference_data = {
        "items": items,
        "back_urls": {
            "success": "https://49f1e1aba724.ngrok-free.app/sucesso",
            "failure": "https://www.google.com",
            "pending": "https://www.google.com"
        },
        "auto_return": "approved"
    }
    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response.get("response", {})
        if "init_point" not in preference:
            return f"Erro: preferência inválida:<br><pre>{preference}</pre>"
        return redirect(preference["init_point"])
    except Exception as e:
        return f"Erro ao criar preferência:<br><pre>{str(e)}</pre>"

@app.route('/sucesso')
def sucesso_pagamento():
    carrinho = session.get('carrinho', [])
    if not carrinho:
        return redirect(url_for('listar_produtos'))
    return render_template('formulario_entrega.html')

@app.route('/admin/pedidos')
def admin_pedidos():
    try:
        conn = conectar_db()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM pedidos ORDER BY id DESC")
            pedidos = cursor.fetchall()
            total = len(pedidos)
            entregues = sum(1 for p in pedidos if p.get("entregue") == 1)
            pendentes = sum(1 for p in pedidos if not p.get("entregue"))
        conn.close()
        return render_template('admin_pedidos.html', pedidos=pedidos, total=total, entregues=entregues, pendentes=pendentes)
    except Exception as e:
        return f"Erro ao buscar pedidos: {str(e)}"

@app.route('/calcular_frete')
def calcular_frete():
    cep = request.args.get('cep', '').strip()
    if len(cep) != 8 or not cep.isdigit():
        return jsonify({'erro': True, 'mensagem': 'CEP inválido.'})
    viacep_url = f'https://viacep.com.br/ws/{cep}/json/'
    try:
        r = requests.get(viacep_url)
        dados = r.json()
        if 'erro' in dados:
            return jsonify({'erro': True, 'mensagem': 'CEP não encontrado.'})
        estados_com_frete = {'SP': 10.00, 'RJ': 12.00, 'MG': 14.00, 'RS': 15.00}
        valor_frete = estados_com_frete.get(dados['uf'], 20.00)
        prazo = 5 if dados['uf'] == 'SP' else 7
        session['frete'] = {'valor': valor_frete, 'prazo': prazo, 'cidade': dados['localidade'], 'uf': dados['uf']}
        return jsonify({'erro': False, 'valor': valor_frete, 'prazo': prazo, 'cidade': dados['localidade'], 'uf': dados['uf']})
    except Exception:
        return jsonify({'erro': True, 'mensagem': 'Erro ao calcular frete.'})

@app.route('/finalizar_pedido', methods=['POST'])
def finalizar_pedido():
    nome_cliente = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    endereco = request.form.get('endereco')
    carrinho = session.get('carrinho', [])
    data_pedido = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = conectar_db()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO pedidos (nome_cliente, email, telefone, endereco, data_pedido)
                VALUES (%s, %s, %s, %s, %s)
            """, (nome_cliente, email, telefone, endereco, data_pedido))
            pedido_id = cursor.lastrowid
            for item in carrinho:
                cursor.execute("""
                    INSERT INTO itens_pedido (pedido_id, nome_produto, preco)
                    VALUES (%s, %s, %s)
                """, (pedido_id, item['nome'], item['preco']))
            conn.commit()
        conn.close()
        session.pop('carrinho', None)
        mensagem_html = f"""
        <h2>Olá, {nome_cliente}!</h2>
        <p>Seu pedido #{pedido_id} foi recebido com sucesso.</p>
        <p>Seu endereço: {endereco}</p>
        <p>Data do pedido: {data_pedido}</p>
        <p>Obrigado por comprar conosco!</p>
        """
        enviar_email(email, "Confirmação do Pedido - Inture", mensagem_html)
        return render_template('sucesso.html', pedido_id=pedido_id)
    except Exception as e:
        enviar_email(EMAIL_REMETENTE, "Erro ao processar pedido", str(e))
        return f"Erro ao salvar pedido: {str(e)}"

if __name__ == '__main__':
    import os
    # 🧠 Inicia o verificador automático do token
    threading.Thread(target=verificar_token_periodicamente, daemon=True).start()

    # 🚀 Inicia o servidor Flask
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)