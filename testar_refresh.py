import requests, base64

REFRESH_URL = "https://www.bling.com.br/Api/v3/oauth/token"
CLIENT_ID = "8e4a69ebc4af56dcea9a2efcb6746062a0d1eddd"
CLIENT_SECRET = "5d34ac1c0fc7103495212b262510984a74d729f0497502220c185406f5c9"
REFRESH_TOKEN = "SEU_REFRESH_TOKEN_AQUI"

auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
headers = {
    "Authorization": f"Basic {auth_header}",
    "Content-Type": "application/x-www-form-urlencoded"
}

data = {
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN
}

r = requests.post(REFRESH_URL, headers=headers, data=data)
print("Status:", r.status_code)
print("Resposta:", r.text)
