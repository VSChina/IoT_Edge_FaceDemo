#!/bin/bash


##### install depency for CLI######
sudo apt-get update
sudo apt install -y git
sudo apt-get install -y curl
AZ_REPO=$(lsb_release -cs)
echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $AZ_REPO main" | \
    sudo tee /etc/apt/sources.list.d/azure-cli.list

curl -L https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add -


set -euo pipefail
IFS=$'\n\t'
sudo apt-get update
sudo apt-get install -y apt-transport-https azure-cli
result=$(az extension list)
if [[ $result =~ "azure-cli-iot-ext" ]];
then
    echo "extension exists"
else
    az extension add --name azure-cli-iot-ext
fi

az login
##### Azure CLI success######


# # -e: immediately exit if any command has a non-zero exit status
# # -o: prevents errors in a pipeline from being masked
# # IFS new value is less likely to cause confusing bugs when looping arrays or arguments (e.g. $@)

usage() { echo "Usage: $0 -i <subscriptionId> -g <resourceGroupName> -n <deploymentName> -l <resourceGroupLocation>" 1>&2; exit 1; }

declare subscriptionId="faab228d-df7a-4086-991e-e81c4659d41a"
declare resourceGroupName="20180926test"
declare deploymentName="autoinstall"
declare resourceGroupLocation="West US 2"

# # Load resources' names
functionName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['sites_autorecog_name']['value']")
eventhubSpaceName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['namespaces_autoresult_name']['value']")
eventhubName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['eventhub_autoresult_name']['value']")
leafDevice=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['leaf_device_name']['value']")
edgeDevice=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['edge_device_name']['value']")
embedDevice=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['edge_embedded_name']['value']")
iotName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['IotHubs_autoiot_name']['value']")
databaseName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['sql_database_name']['value']")
collectionName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['sql_collection_name']['value']")
sqlName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['databaseAccounts_autosql_name']['value']")
acrName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['registries_autoimagestore_name']['value']")
webappName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['web_app_name']['value']")
webplanName=$(python -c "import json; infile = open('parameters.json','rb'); print json.load(infile)['parameters']['web_plan_name']['value']")

# Initialize parameters specified from command line
while getopts ":i:g:n:l:" arg; do
	case "${arg}" in
		i)
			subscriptionId=${OPTARG}
			;;
		g)
			resourceGroupName=${OPTARG}
			;;
		n)
			deploymentName=${OPTARG}
			;;
		l)
			resourceGroupLocation=${OPTARG}
			;;
		esac
done
shift $((OPTIND-1))

#Prompt for parameters is some required parameters are missing
if [[ -z "$subscriptionId" ]]; then
	echo "Your subscription ID can be looked up with the CLI using: az account show --out json "
	echo "Enter your subscription ID:"
	read subscriptionId
	[[ "${subscriptionId:?}" ]]
fi

if [[ -z "$resourceGroupName" ]]; then
	echo "This script will look for an existing resource group, otherwise a new one will be created "
	echo "You can create new resource groups with the CLI using: az group create "
	echo "Enter a resource group name"
	read resourceGroupName
	[[ "${resourceGroupName:?}" ]]
fi

if [[ -z "$deploymentName" ]]; then
	echo "Enter a name for this deployment:"
	read deploymentName
fi

if [[ -z "$resourceGroupLocation" ]]; then
	echo "If creating a *new* resource group, you need to set a location "
	echo "You can lookup locations with the CLI using: az account list-locations "
	
	echo "Enter resource group location:"
	read resourceGroupLocation
fi

#templateFile Path - template file to be used
templateFilePath="template.json"

if [ ! -f "$templateFilePath" ]; then
	echo "$templateFilePath not found"
	exit 1
fi

#parameter file path
parametersFilePath="parameters.json"

if [ ! -f "$parametersFilePath" ]; then
	echo "$parametersFilePath not found"
	exit 1
fi

if [ -z "$subscriptionId" ] || [ -z "$resourceGroupName" ] || [ -z "$deploymentName" ]; then
	echo "Either one of subscriptionId, resourceGroupName, deploymentName is empty"
	usage
fi

#login to azure using your credentials
az account show 1> /dev/null

if [ $? != 0 ];
then
	az login
fi

#set the default subscription id
az account set --subscription $subscriptionId

set +e

#Check for existing RG
az group show --name $resourceGroupName 1> /dev/null

if [ $? != 0 ]; then
	echo "Resource group with name" $resourceGroupName "could not be found. Creating new resource group.."
	set -e
	(
		set -x
		az group create --name $resourceGroupName --location $resourceGroupLocation 1> /dev/null
	)
	else
	echo "Using existing resource group..."
fi

#Start deployment
echo "Starting deployment..."
(
	set -x
	az group deployment create --name "$deploymentName" --resource-group "$resourceGroupName" --template-file "$templateFilePath" --parameters "@${parametersFilePath}"
)

if [ $?  == 0 ];
 then
	echo "Template has been successfully deployed"
fi

# create function, eventhub, cosmosdb and 3 devices
storageName=$(az storage account list -g $resourceGroupName | python -c "import sys, json; print json.load(sys.stdin)[0][u'name']")
az functionapp create --name $functionName --resource-group $resourceGroupName --storage-account $storageName --consumption-plan-location westus2
az eventhubs eventhub create --resource-group $resourceGroupName --namespace-name $eventhubSpaceName --name $eventhubName --message-retention 1
az iot hub device-identity create --device-id $leafDevice --hub-name $iotName
az iot hub device-identity create --device-id $embedDevice --hub-name $iotName
az iot hub device-identity create --device-id $edgeDevice --hub-name $iotName --edge-enabled true
az cosmosdb database create --db-name $databaseName --name $sqlName --resource-group $resourceGroupName
az cosmosdb collection create --db-name $databaseName --collection-name $collectionName --resource-group $resourceGroupName --name $sqlName

# azure function deployment and integration
python functionConnection.py
cd ../src/azure/azure_function
zip -r function.zip ./*
cd ../../../script
az functionapp deployment source config-zip --resource-group $resourceGroupName --name $functionName --src ../src/azure/azure_function/function.zip
rm ../src/azure/azure_function/function.zip
az functionapp config appsettings list --name $functionName --resource-group $resourceGroupName
cosmosEndpoint=$(az cosmosdb show --name $sqlName --resource-group $resourceGroupName | python -c "import sys, json; print json.load(sys.stdin)[u'documentEndpoint']")
cosmosKey=$(az cosmosdb list-keys --name $sqlName --resource-group $resourceGroupName | python -c "import sys, json; print json.load(sys.stdin)[u'primaryMasterKey']")
functionDBConnection="AccountEndpoint="$cosmosEndpoint";AccountKey="$cosmosKey";"
echo $functionDBConnection
iotEventEndpoint=$(az iot hub show --name $iotName --resource-group $resourceGroupName | python -c "import sys, json; print json.load(sys.stdin)[u'properties'][u'eventHubEndpoints'][u'events'][u'endpoint']")
iotConnectionString=$(az iot hub show-connection-string --hub-name $iotName --resource-group $resourceGroupName | python -c "import sys, json; print json.load(sys.stdin)[u'cs']")
functionIoTConnection="Endpoint="$iotEventEndpoint";"$(echo $iotConnectionString | cut -d \; -f 2)";"$(echo $iotConnectionString | cut -d \; -f 3)";EntityPath="$iotName
echo $functionIoTConnection
eventConnection=$(az eventhubs namespace authorization-rule keys list --name RootManageSharedAccessKey --namespace-name $eventhubSpaceName --resource-group $resourceGroupName | python -c "import sys, json; print json.load(sys.stdin)[u'primaryConnectionString']")
functionEventConnection=$eventConnection";EntityPath="$eventhubName
echo $functionEventConnection
iotEventEndName=$iotName"_events_IOTHUB"
resultEndName=$eventhubSpaceName"_RootManageSharedAccessKey_EVENTHUB"
DBEndName=$sqlName"_DOCUMENTDB"
az functionapp config appsettings set --name $functionName --resource-group $resourceGroupName --settings $iotEventEndName="$functionIoTConnection"
az functionapp config appsettings set --name $functionName --resource-group $resourceGroupName --settings $resultEndName="$functionEventConnection"
az functionapp config appsettings set --name $functionName --resource-group $resourceGroupName --settings $DBEndName="$functionDBConnection"

# link to cosmosdb
sed -i "s|\"https://.*,|\"$cosmosEndpoint\",|" ../src/azure/cloud_service/Register_Module/main.py
sed -i "s|'masterKey': .*\"|'masterKey': \"$cosmosKey\"|" ../src/azure/cloud_service/Register_Module/main.py
sed -i "s|collection_link = .*$|collection_link = \"dbs/$databaseName/colls/$collectionName\"|" ../src/azure/cloud_service/Register_Module/main.py

# link to eventhub
eventHubAddress="amqps://"$eventhubSpaceName".servicebus.windows.net/"$eventhubName
eventHubKey=$(az eventhubs namespace authorization-rule keys list --name RootManageSharedAccessKey --namespace-name $eventhubSpaceName --resource-group $resourceGroupName | python -c "import sys, json; print json.load(sys.stdin)[u'primaryKey']")
sed -i.bak "s|ADDRESS = .*$|ADDRESS = \"$eventHubAddress\"|" ../src/leaf/client_with_detection_UI.py
sed -i.bak "s|KEY = .*$|KEY = \"$eventHubKey\"|" ../src/leaf/client_with_detection_UI.py

# link to devices
leafConnection=$(az iot hub device-identity show-connection-string --device-id $leafDevice --hub-name $iotName | python -c "import sys, json; print json.load(sys.stdin)[u'cs']")
edgeConnection=$(az iot hub device-identity show-connection-string --device-id $edgeDevice --hub-name $iotName | python -c "import sys, json; print json.load(sys.stdin)[u'cs']")
embedConnection=$(az iot hub device-identity show-connection-string --device-id $embedDevice --hub-name $iotName | python -c "import sys, json; print json.load(sys.stdin)[u'cs']")
edgeHostName=$(hostname)
leafConnection=$leafConnection";GatewayHostName="$edgeHostName
sed -i.bak "s|CONNECTION_STRING = .*$|CONNECTION_STRING = \"$leafConnection\"|" ../src/leaf/client_with_detection_UI.py
sed -i.bak "s|CONNECTION_STRING = .*$|CONNECTION_STRING = \"$embedConnection\"|" ../src/edge/modules/recognition/main.py

# # acr settings
acrLoginServer=$(az acr update -n $acrName --admin-enabled true | python -c "import sys, json; print json.load(sys.stdin)[u'loginServer']")
acrUserName=$(az acr credential show --name $acrName | python -c "import sys, json; print json.load(sys.stdin)[u'username']")
acrPassword=$(az acr credential show --name $acrName | python -c "import sys, json; print json.load(sys.stdin)[u'passwords'][0][u'value']")
sed -i.bak "s|\"username\": .*$|\"username\": \"$acrUserName\",|" ../src/edge/config/deployment.json
sed -i.bak "s|\"password\": .*$|\"password\": \"$acrPassword\",|" ../src/edge/config/deployment.json
sed -i.bak "s|\"address\": .*$|\"address\": \"$acrLoginServer\"|" ../src/edge/config/deployment.json
sed -i.bak "s|CONTAINER_REGISTRY_USERNAME_imagescontainer=.*$|CONTAINER_REGISTRY_USERNAME_imagescontainer=$acrUserName|" ../src/edge/.env
sed -i.bak "s|CONTAINER_REGISTRY_PASSWORD_imagescontainer=.*$|CONTAINER_REGISTRY_PASSWORD_imagescontainer=$acrPassword|" ../src/edge/.env
sed -i.bak "s|\"repository\": .*/|\"repository\": \"$acrLoginServer/|" ../src/edge/modules/recognition/module.json
sed -i.bak "s|\"address\": .*|\"address\": \"$acrLoginServer\"|" ../src/edge/deployment.template.json
sed -i.bak "s|\"image\": .*/recognition_service|\"image\": \"$acrLoginServer/recognition_service|" ../src/edge/deployment.template.json

# edge runtime installation
export DEBIAN_FRONTEND="noninteractive"
curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list > ./microsoft-prod.list
sudo cp ./microsoft-prod.list /etc/apt/sources.list.d/
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo cp ./microsoft.gpg /etc/apt/trusted.gpg.d/
sudo apt-get update
sudo apt-get install -y moby-engine
sudo apt-get install -y moby-cli

sudo apt-get install -y iotedge || true
sudo sed -i.bak "s|device_connection_string:.*$|device_connection_string: \"$edgeConnection\"|" /etc/iotedge/config.yaml
sudo systemctl restart iotedge || (sleep 5 && sudo systemctl restart iotedge)

# leaf runtime installation
sudo apt-get install -y python3-pip
sudo apt-get install -y build-essential
sudo apt-get install -y libboost-all-dev
sudo apt-get install -y cmake
sudo apt-get install -y python-pip python-dev libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev
sudo pip3 install -r leaf_requirements.txt
sudo apt-get install -y python3-pyqt4

# edge gateway settings(CA)
git clone https://github.com/Azure/azure-iot-sdk-c.git
mkdir CACertificateGateway
cd CACertificateGateway
cp ../azure-iot-sdk-c/tools/CACertificates/*.cnf .
cp ../azure-iot-sdk-c/tools/CACertificates/certGen.sh .
chmod 700 certGen.sh
./certGen.sh create_root_and_intermediate
./certGen.sh create_edge_device_certificate "demo"
cat ./certs/new-edge-device.cert.pem ./certs/azure-iot-test-only.intermediate.cert.pem ./certs/azure-iot-test-only.root.ca.cert.pem > ./certs/new-edge-device-full-chain.cert.pem
sudo sed -i.bak "s|# certificates:.*$|certificates: |" /etc/iotedge/config.yaml
sudo sed -i.bak "s|#   device_ca_cert:.*$|  device_ca_cert: \"$PWD/certs/new-edge-device-full-chain.cert.pem\"|" /etc/iotedge/config.yaml
sudo sed -i.bak "s|#   device_ca_pk:.*$|  device_ca_pk: \"$PWD/private/new-edge-device.key.pem\"|" /etc/iotedge/config.yaml
sudo sed -i.bak "s|#   trusted_ca_certs:.*$|  trusted_ca_certs: \"$PWD/certs/azure-iot-test-only.root.ca.cert.pem\"|" /etc/iotedge/config.yaml
sudo rm /var/lib/iotedge/hsm/cert_keys/*
sudo rm /var/lib/iotedge/hsm/certs/*
sudo systemctl restart iotedge || (sleep 5 && sudo systemctl restart iotedge)
sudo cp $PWD/certs/azure-iot-test-only.root.ca.cert.pem  /usr/local/share/ca-certificates/azure-iot-test-only.root.ca.cert.pem.crt
sudo update-ca-certificates

# build images
sudo docker login -u $acrName -p $acrPassword $acrLoginServer
cd ../../src/edge/modules/recognition/

imageName=$(python -c "import json; infile = open('module.json','rb'); print json.load(infile)['image']['repository']")
imageTag=$(python -c "import json; infile = open('module.json','rb'); content = json.load(infile); print content['image']['tag']['version']+'-amd64'")
dockerFile=$(python -c "import json; infile = open('module.json','rb'); print json.load(infile)['image']['tag']['platforms']['amd64']")
sudo docker build -f $dockerFile -t $imageName":"$imageTag .
sudo docker push $imageName":"$imageTag

cd ../../../azure/cloud_service
cd Detection_Module
sudo docker build -t $acrLoginServer"/detection_service" .
sudo docker push $acrLoginServer"/detection_service"

cd ../Recognition_Module_CPU
sudo docker build -t $acrLoginServer"/recognition_service:cpu" .
sudo docker push $acrLoginServer"/recognition_service:cpu"

cd ../Recognition_Module_GPU
sudo docker build -t $acrLoginServer"/recognition_service:gpu" .
sudo docker push $acrLoginServer"/recognition_service:gpu"

cd ../Register_Module
sudo docker build -t $acrLoginServer"/cloud_business" .
sudo docker push $acrLoginServer"/cloud_business"

cd ..
sed -i.bak "s|image: .*/|image: $acrLoginServer/|" ./docker-compose.yml

cd ../../../

az iot edge set-modules --device-id $edgeDevice --hub-name $iotName --content ./src/edge/config/deployment.json

# registration deployment
az appservice plan create --name $webplanName --resource-group $resourceGroupName --is-linux --sku B1
az webapp create --name $webappName --plan $webplanName --resource-group $resourceGroupName --multicontainer-config-file ./src/azure/cloud_service/docker-compose.yml --multicontainer-config-type COMPOSE 
az webapp config appsettings set --name $webappName --resource-group $resourceGroupName --settings DOCKER_REGISTRY_SERVER_PASSWORD="$acrPassword"
az webapp config appsettings set --name $webappName --resource-group $resourceGroupName --settings DOCKER_REGISTRY_SERVER_URL="https://$acrLoginServer"
az webapp config appsettings set --name $webappName --resource-group $resourceGroupName --settings DOCKER_REGISTRY_SERVER_USERNAME="$acrName"
