import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from key import *
import time


def login():
        
    key = token
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
    #print(auth_header)
    return finalHeader


## Getting Org ID
def sddc_baseurl(finalHeader):
    req = requests.get('https://vmc.vmware.com/vmc/api/orgs', headers = finalHeader)
    orgID = req.json()[0]['id']

    ##Getting Organization ID and asking user to Enter SDDC ID
    sddcReq = requests.get('https://vmc.vmware.com/vmc/api/orgs/'+orgID+'/sddcs', headers=finalHeader)
    x = sddcReq.json()
    for item in x: print(item['id'].rjust(30)+'============',item['name'].ljust(50))
    sddc_ID = input("Kindly copy the SDDC ID shown above in alphanumeric ID:")
    #print (sddc_ID)
    sddc_baseurl = f'https://nsx-3-9-59-86.rp.vmwarevmc.com/vmc/reverse-proxy/api/orgs/{orgID}/sddcs/{sddc_ID}/'
    return sddc_baseurl

#print(sddc_baseurl)



def section_dict(sddc_baseurl):
    section_map_dict = {}
    communication_maps_uri ='policy/api/v1/infra/domains/cgw/communication-maps'
    section_map_url = sddc_baseurl+communication_maps_uri
    response = requests.get(url=section_map_url,headers=finalHeader)
    section_resp = response.json()  ## This brings all the communication-maps data
    #Creating two list to build one dictionary , Keys will be display_name and value will be ID.
    section_name_list = []
    section_id_list = []
    for item in section_resp['results']:
        section_map_dict[item['display_name'].upper()] = item['id']
        section_name_list.append(item['display_name'].upper())
        #section_id_list.append(item['id'])
    #section_map_dict  = dict(zip(section_name_list,section_id_list))
    return section_map_dict,section_name_list


### Getting IP_Groups Details for Src and Destination

def ip_group_services(sddc_baseurl):
        
    ip_groups_uri = 'policy/api/v1/infra/domains/cgw/groups'
    ip_groups_url = sddc_baseurl+ip_groups_uri
    ip_groups_data = requests.get(url=ip_groups_url,headers=finalHeader)
    ip_groups_data = ip_groups_data.json()
    ip_groups_id_list = []
    ip_groups_name_list = []
    for item in ip_groups_data['results']:
        ip_groups_id_list.append(item['id'])
        ip_groups_name_list.append(item['display_name'])

    ip_groups_dict = dict(zip(ip_groups_id_list,ip_groups_name_list))

    ## Getting Services Details and Creating Services Dictionary..
    services_uri = 'policy/api/v1/infra/services'
    services_url = sddc_baseurl+services_uri
    services_response = requests.get(url=services_url,headers=finalHeader)
    services_data = services_response.json()

    ## Creating Service port Dictory
    services_dict = {}
    for item in services_data['results']:
        try:
            services_name = item['display_name']
            services_id = item['id']
            services_port = item['service_entries'][0]['destination_ports']
            services_dict[services_id] = [services_name,services_port]
            #services_dict
        except:
            #print (f'There is no port for this service {services_name}')
            services_dict[id] = [services_name]
    return ip_groups_dict,services_dict



######################
# function provides Source/Dstination/port details from rule_data. This is mainly for parsing data.
#Rule Data is nothing but all the Specific Section Data..

def rule_parse(rule_data,ip_groups_dict,services_dict,rule_source_name = 'ANY',rule_dest_name= 'ANY',rule_service_name='ANY'):
    #Total_Rule = len(rule_data['results'])
    for n,item in enumerate(rule_data['results']):
        try:
            rule_name = item['display_name']
            #print (rule_name)
            rule_source = item['source_groups'][0].split('/')
            rule_source = (rule_source[-1])
            #print(rule_source)
            rule_dest = item['destination_groups'][0].split('/')
            rule_dest = (rule_dest[-1])
            rule_source_name = ip_groups_dict[rule_source]
            #print(f'print rule_source_name {rule_source_name}')
            rule_dest_name = ip_groups_dict[rule_dest]
            #print(f'print rule_destination_name {rule_dest_name}')
            #print(rule_dest_name)
            rule_service = item['services'][0].split('/')
            rule_service = (rule_service[-1])
            rule_service_name = services_dict[rule_service]
            #print(rule_service_name)
            print (f'\nprinting rule number {n+1}::')
            
            print (f'RuleName=={rule_name} || RuleSource=={rule_source_name} || RuleDestination=={rule_dest_name} || RuleService=={rule_service_name}')
            with open ('c://Users/ardo/VMC_Rules_Output.txt','a') as f:
                f.write(f'RuleName=={rule_name},RuleSource=={rule_source_name},RuleDestination=={rule_dest_name},RuleService=={rule_service_name}\n')
        except:
            print (f'\nprinting rule number {n+1}::')
            print (f'RuleName=={rule_name} || RuleSource=={rule_source_name} || RuleDestination=={rule_dest_name} || RuleService== "ANY"\n')
            with open ('c://Users/ardfdfawat/DeMC_Rules_Output.txt','a') as f:
                f.write(f'RuleName=={rule_name},RuleSource=={rule_source_name},RuleDestination=={rule_dest_name},RuleService=={rule_service_name}\n')

#rule_parse(rule_source_name = 'ANY',rule_dest_name= 'ANY',rule_service_name='ANY')


## Function to gather Section Specific Data. Section name is provide in the form of choice. section_map_dict is required to work which basically map
## section name to section id

def rule_data (section_name,section_map_dict,sddc_baseurl):
    section_name= section_name.upper() 
    section_id = section_map_dict[section_name]
    ### Getting Section specific rules 
    section_entry = f'policy/api/v1/infra/domains/cgw/communication-maps/{section_id}/communication-entries'
    url = sddc_baseurl+section_entry
    rule_response = requests.get(url,headers=finalHeader)
    rule_data = rule_response.json()
    return rule_data

## Executing Real Code in While Loop, User will type exit or quit to come out.
def main():
        
    try:
        while True :
            print(('\n\n\n'),("="*100))
            print("\nType exit or quit from the script or enter the section name again to get rule details from below list: \n")
            print(section_name_list)
            print("="*100)
            choice = input('\nEnter your choice here : ')
            #print(choice)
            #print(type(choice))
            if choice.lower()=='exit' or choice.lower()=='quit' or choice=='\n':
                print("Thank you using the the script. Signing off....")
                break
            elif choice == 'ALL' or choice == 'all':
                for item in section_name_list:
                    rule_entries = rule_data(item,section_map_dict,sddc_baseurl)
                    print(('\n\n'),('='*100))
                    print(f'\n..................printing rule details from the section {item}.................')
                    print('='*100)
                    #print(f'Total Number of Rules are : {len(rule_entries['results'])}\n')
                    with open ('c://Users/adfdfrawat/Desktop/Da/VMC_Rules_Output.txt','a') as f:
                        f.write(f"\n\n******************** Printing FW rule for Section {item}***************\n\n")
                        f.write(f"Total Number of Rules are : {len(rule_entries['results'])}\n")
                    rule_parse(rule_entries,ip_groups_dict=ip_groups_dict,services_dict=services_dict,rule_source_name = 'ANY',rule_dest_name= 'ANY',rule_service_name='ANY')
            else:
                print('Executing code block for print rules')
                #section_map_dict = section_dict(sddc_baseurl)
                rule_entries = rule_data(choice,section_map_dict,sddc_baseurl)
                #len(rule_entries)
                print(f'\n..................printing rule details from the section {choice}...............')
                with open ('c://Users/aradfdsfwat/Desmo/VMC_Rules_Output.txt','a') as f:
                    f.write(f"\n\n******************** Printing FW rule for Section {choice}***************\n\n")
                    f.write(f"Total Number of Rules are : {len(rule_entries['results'])}\n")
                rule_parse(rule_entries,ip_groups_dict=ip_groups_dict,services_dict=services_dict,rule_source_name = 'ANY',rule_dest_name= 'ANY',rule_service_name='ANY')
    except KeyError as KE:
        print(KE)
        print("Enter Correct Choice from the List. Wrong Input Entered or it's not case sensitive. Check below ")
        print (choice)

if __name__=='__main__':
    ##Generating finalHeader for all the request
    finalHeader = login()
    #print('final header function executed')
    sddc_baseurl = sddc_baseurl(finalHeader)
    #print('sddc baseurl function executed')
    
    ## Calling ip_group_services function to generate ip_groups and services dictionary
    ip_groups_dict,services_dict = ip_group_services(sddc_baseurl)
    #print('ip group_services executed')

    ##Generating Section Map Dict which is used to select Section ID.
    section_map_dict,section_name_list = section_dict(sddc_baseurl)

    ## Main function mainly asking for user input like section name or quit exit. This calls another function to parse the data
    main()

    
          



