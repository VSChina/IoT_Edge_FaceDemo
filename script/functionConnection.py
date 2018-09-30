import json
infile = open('parameters.json','rb')
params = json.load(infile)
infile.close()
infile = open('../src/azure/azure_function/recog/function.json','r')
configFile = json.load(infile)
infile.close()
outfile = open('../src/azure/azure_function/recog/function.json','wb')

eventHubConnection = params["parameters"]["namespaces_autoresult_name"]["value"] + "_RootManageSharedAccessKey_EVENTHUB"
configFile["bindings"][0]["connection"] = eventHubConnection
eventHubPath = params["parameters"]["eventhub_autoresult_name"]["value"]
configFile["bindings"][0]["path"] = eventHubPath


sqlConnection = params["parameters"]["databaseAccounts_autosql_name"]["value"] + "_DOCUMENTDB"
configFile["bindings"][1]["connection"] = sqlConnection
sqlDatabaseName = params["parameters"]["sql_database_name"]["value"]
configFile["bindings"][1]["databaseName"] = sqlDatabaseName
sqlCollectionName = params["parameters"]["sql_collection_name"]["value"]
configFile["bindings"][1]["collectionName"] = sqlCollectionName

iotHubConnection = params["parameters"]["IotHubs_autoiot_name"]["value"] + "_events_IOTHUB"
configFile["bindings"][2]["connection"] = iotHubConnection
iotHubPath = params["parameters"]["IotHubs_autoiot_name"]["value"]
configFile["bindings"][2]["path"] = iotHubPath

outfile.write(json.dumps(configFile))
outfile.close()