import requests
import json
import sys

def merge_dicts(dict1, dict2):
    
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                merge_dicts(dict1[key], dict2[key])
            elif isinstance(dict1[key], list) and isinstance(dict2[key], list):
                dict1[key] = merge_lists(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]  # Overwrite conflict by default
        else:
            dict1[key] = dict2[key]
   
    return dict1

def merge_lists(list1, list2):
    """
    Merges two lists, avoiding duplicates while preserving order.
    """
    merged_list = list1[:]
    for item in list2:
        if item not in merged_list:
            merged_list.append(item)
    return merged_list


def createmodel(auth , domain , name,qu):

   modelplace="/api/v1/models"
   url=domain + modelplace    

   newbody={'description':'string','tags':[],'publicTags':['wf','ab2'],'settings':{'openLineageExplorer':'false','preventForking':'true','issueSettings':{'Basic':{'minimumApprovalsRequired':0,'canAutomaticallyMerge':'true','conflictPreference':'TakeMine','disabled':'true'},'Task':{'minimumApprovalsRequired':0,'canAutomaticallyMerge':'true','conflictPreference':'TakeMine','disabled':'true'},'PullRequest':{'minimumApprovalsRequired':0,'canAutomaticallyMerge':'true','conflictPreference':'TakeMine','enabled':'true'},'ImportUpdate':{'minimumApprovalsRequired':0,'canAutomaticallyMerge':'true','conflictPreference':'TakeMine','disabled':'false'},'ParentChanges':{'minimumApprovalsRequired':0,'canAutomaticallyMerge':'true','conflictPreference':'TakeMine','disabled':'true'}},'automaticallyCreatePullRequests':'true'},'referenceModelType':'DataDictionary','type':'LineageModel'}
   newbody['name']=name
  

   headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' +  auth
   }

   createModelResponse = requests.post(url , data=str(newbody), headers=headers)
   if createModelResponse.status_code != 200:
        print('ERROR: Failed to create model !')
        print(createModelResponse.status_code)
        print(url)
        exit(1)
   else:
        print("INFO : Added model : " + name)
        #print((createModelResponse.content))
        json2 = json.loads(createModelResponse.content)
        newmodelId = json2['id']
        print("INFO : New modelid is : "+ newmodelId)

        return newmodelId

def replacemodel(auth , domain ,modelId, jsoncontent,qu):

   print("INFO : Replacing Solidatus model :"+ modelId)
   

   modelplace="api/v1/models/"+ modelId + "/update"
   url=domain + "/" + modelplace    

   print("INFO :     Solidatus API call : "+ url )
   
   jsoncontent_str = json.dumps(jsoncontent)

   cmd='{ "cmd": "ReplaceModel", "model": ' + jsoncontent_str + ' , "comparator" : {"PATH": true} } '
   newbody=' { "cmds": [ ' + cmd + ' ], "commit": true, "commitMessage": "'+ qu +'" , "preview": false, "includeChangeset": true, "expectDraft": false }'
   
   #print(newbody)

   headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' +  auth
   }


   print(url)


   
   print("INFO :     Writing Solidatus API command file : temp/tosolidatus.json")
   f = open("tosolidatus-"+modelId+".json", "w")
   f.write(newbody)
   f.close()
   

  
   createModelResponse = requests.post(url , data=newbody, headers=headers)
   if createModelResponse.status_code != 200:
        print('ERROR:     Failed to replace model !')
        print(createModelResponse)
        return "model failed"
   else:
        print("INFO :     Solidatus Model Replaced : " + modelId)
        return "model replaced"



def get_sol_config(configfile):

    global recoverymode

    f = open(configfile, "r")
    configtext=f.read()
    configjson=json.loads(configtext)
    f.close()

    auth=configjson["auth"]
    domain=configjson["domain"]
    modelId=configjson["modelId"]
    alation_nodes=configjson["alation_nodes"]
    alation_edges=configjson["alation_edges"]
    alation_auth= configjson["alation_auth"] 
    alation_edgetype=configjson["alation_edgetype"]
    use_cached_json=configjson["use_cached_json"]

    
    sol_config = [ auth , domain , modelId ,alation_nodes,alation_edges,alation_auth,alation_edgetype,use_cached_json]

    return sol_config

def get_edges(url,auth):


    headers = {
        "accept": "application/json",
        "TOKEN": auth
    }

    response = requests.get(url, headers=headers)

    print(response.text)

    print("INFO :     Writing raw file  : temp/edges.json")
    f = open("temp/edges.json", "w")
    f.write(response.text)
    f.close()


def get_nodes(url,auth):
    
    headers = {
        "accept": "application/json",
        "TOKEN": auth
    }

    response = requests.get(url, headers=headers)

    print(response.text)

    print("INFO :     Writing raw file  : temp/nodes.json")
    f = open("temp/nodes.json", "w")
    f.write(response.text)
    f.close()

def get_nodes_from_file():

    with open('temp/nodes.json', 'r') as file:
        data = json.load(file)

   
    return data

def get_edges_from_file():

    with open('temp/edges.json', 'r') as file:
        data = json.load(file)

   
    return data


def process_edges(paths,solidatus_json,alation_edgetype):
    tid=1    
    for path  in paths['paths']:
        source_target=[]
        for pathunit in path:
             key=process_an_edge(solidatus_json,pathunit,alation_edgetype)
             if key != 0 :
                source_target.append(key)

             if len(source_target) == 2:
                 print("add a transition")
                 tid=tid+1
                 str_tid=str(tid)
                 solidatus_json["transitions"][str_tid] = {
                        "source": source_target[0],
                        "target": source_target[1] ,
                        "properties": {
                            }}

                 source_target=[]
              

    return solidatus_json


        

def process_an_edge(solidatus_json,edge,alation_edgetype):
    # [{'otype': 'dataflow', 'key': 'sql/1_6581555692189717024'}]
    print(edge[0])
    otype = edge[0].get('otype')
    key = edge[0].get('key')
    
   
    if otype == alation_edgetype:
       try:
           key="/"+key.replace(".","/")
       except : return 0
       if key  in solidatus_json["entities"]:
            return key
    return 0




#######################
####### main ##########
#######################

configfile="config.json"
# global var 
auth , domain , modelId ,alation_nodes,alation_edges,alation_auth,alation_edgetype,use_cached_json = get_sol_config(configfile)

### tempcomment out


if use_cached_json == "False":
    print("info : Collecting data from Alation")
    get_nodes(alation_nodes,alation_auth)
    get_edges(alation_edges,alation_auth)

    
nodes=get_nodes_from_file()
# 
edges=get_edges_from_file()

solidatus_json= { "entities": { "Alation" : { "name" : "Alation" , "properties": {}, "children":[] 
                                             }
                                    },
                        "transitions": {},
                        "roots": [ "Alation" ]
                        }


for row in nodes:
    print(row)
    path=(row['key'])
    """for key, value in row.items():
        print(f"{key}: {value}")
    print()  # Print an empty line between each row
    """

    pathentities = path.split('.')

    # Loop through the split items
    parententity=""
    pathentity=""
    for currententity in pathentities:

      
        pathentity=pathentity+"/"+currententity

        
        latest  = { "name": currententity,
                    "properties": {},
                    "children" : []
                    }
        if pathentity in solidatus_json["entities"]:
            solidatus_json["entities"][pathentity] = merge_dicts(solidatus_json["entities"][pathentity],latest)
        else:
            solidatus_json["entities"][pathentity]=latest

        if parententity == "":

            if pathentity not in solidatus_json["entities"]["Alation"]["children"]:
                    solidatus_json["entities"]["Alation"]["children"].append(pathentity)

        else:

            if pathentity not in solidatus_json["entities"][parententity]["children"]:
                    solidatus_json["entities"][parententity]["children"].append(pathentity)

        parententity = pathentity

    pathentity=""
    for currententity in pathentities:

      
        pathentity=pathentity+"/"+currententity
        
        if  solidatus_json["entities"][pathentity]["children"] == []:
            print(pathentity)
            print(solidatus_json["entities"][pathentity]["children"])
            
            for key, value in row.items():
                
                value2=json.dumps(value)
                value2=value2.replace('"','')
                value2=value2.replace("'","")
                solidatus_json["entities"][pathentity]["properties"][key] = value2
       

        parententity = pathentity



print("Entities : " + str(len(solidatus_json['entities'])))
print("Transitions : " + str(len(solidatus_json['transitions'])))


print(edges)
solidatus_json= process_edges(edges, solidatus_json,alation_edgetype)

modelstatus=replacemodel(auth , domain ,modelId, solidatus_json,"load alation data")
print(modelstatus)




