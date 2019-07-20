
## Future Job Get SDDC ID dynamically
import requests,json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)



key = '0TGgFqjFYs6e'
baseurl = 'https://console.cloud.vmware.com/csp/gateway'
uri = '/am/api/auth/api-tokens/authorize'
headers = {'Content-Type':'application/json'}
payload = {'refresh_token': key}
r = requests.post(f'{baseurl}{uri}', headers = headers, params = payload)
if r.status_code != 200:
    print(f'Unsuccessful Login Attmept. Error code {r.status_code}')
else:
    print('Login successful. ')
    
auth_header = r.json()['access_token']
finalHeader = {'Content-Type':'application/json','csp-auth-token':auth_header}
print(auth_header)

def payload(service_name,d_port):
    payload1 = {'description': service_name, 'display_name': service_name, '_revision': 0,
                'service_entries':
                [
                {'resource_type': 'L4PortSetServiceEntry',
                'display_name': service_name,
                'destination_ports': d_port,
                'l4_protocol': 'TCP'}
                ]
                }
    return payload1

req = requests.get('https://vmc.vmware.com/vmc/api/orgs', headers = finalHeader)
orgID = req.json()[0]['id']


baseurl = f'https://nsx-3-9-59-86.rp.vmwarevmc.com/vmc/reverse-proxy/api/orgs/{orgID}/sddcs/9728b0cc-2b30-4715-9f26-42e94f55eb0d/'
uri =f'policy/api/v1/infra/services/'


with open('c:\\file/ports.txt') as f:
    file = f.readlines()


for item in file:
    x = item.split(',')
    service_name= x[0]
    url = baseurl+uri+service_name
    d_port = x[1:-1]
    payload11 = payload(service_name,d_port)
    payload2 = json.dumps(payload11)
    type(payload2)
    req = requests.put(url, data = payload2, headers = finalHeader)
    response = requests.get(url,headers=finalHeader)
    #print(response.json)
    x = response.json()
    print(json.dumps(x,indent=2))

##response = requests.delete(url,headers=finalHeader)
