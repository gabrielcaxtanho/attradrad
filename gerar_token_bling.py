import requests, base64, json, time

# ⚠️ Substitua pelos SEUS dados:
CLIENT_ID = "8e4a69ebc4af56dcea9a2efcb6746062a0d1eddd"
CLIENT_SECRET = "5d34ac1c0fc7103495212b262510984a74d729f0497502220c185406f5c9"
CODE = "f5fc1ea27383c34c807046c7709950bac2e28695"
REDIRECT_URI = "http://localhost:5000/callback"

TOKEN_URL = "https://www.bling.com.br/Api/v3/oauth/token"

# Monta o cabeçalho de autenticação em Base64
auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Corpo da requisição para trocar o code pelos tokens
data = {
    "grant_type": "authorization_code",
    "code": CODE,
    "redirect_uri": REDIRECT_URI
}

r = requests.post(TOKEN_URL, headers=headers, data=data)

print("Status:", r.status_code)
print("Resposta:", r.text)

if r.status_code == 200:
    tokens = r.json()
    tokens["timestamp"] = int(time.time())
    with open("bling_tokens.json", "w") as f:
        json.dump(tokens, f, indent=4)
    print("✅ Tokens salvos em bling_tokens.json")
else:
    print("❌ Erro ao gerar tokens:", r.text)
