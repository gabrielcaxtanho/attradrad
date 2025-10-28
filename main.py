import requests

url = "https://api.bling.com.br/Api/v3/produtos?pagina=1"

payload = {}
headers = {
  'Accept': 'application/json',
  'Authorization': 'Bearer 0030f7a320ff65ac513a48c4ec206410eb7f5484',
  'Cookie': 'PHPSESSID=vk068asu457pos0lo0f2tmvmhh'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
