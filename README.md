# dps-serverless-lambda-example
## Aim of this lambda project
<img src="https://user-images.githubusercontent.com/59567008/159286760-a61731d0-32d4-4f61-ab30-882169693ff9.png" width="150" height="75" /> <img src="https://user-images.githubusercontent.com/59567008/159286689-3e098568-614d-44e6-b659-55438b314dc5.png" width="75" height="75" /> <img src="https://user-images.githubusercontent.com/59567008/159286614-93884de4-eb43-474d-9e65-285e8a9c4746.png" width="150" height="75" />

This project allows to deploy with serverless and github action, a simple lambda aws.

## What is Serverless framework
SLS is an open source web framework written in node.js. Serverless is develop for building application on AWS Lambda

## What is AWS Lambda 
AWS Lambda is a computing service that runs code in reponse to events and automaticaly maneges the computing resources required by that code    

## What is github action 
Github action is a continuous integrations and continuous delivery platform that allows you to automate your build, test and deployement pipeline

## Tree structure of the project
```sh
dps-serverless-lambda-example      
|
+--.github                              # Folder in which the github actions are stored
|  |
|  +---workflows                    
|  |   |
|  |   |--check_pr.yml                  # This github action to check the serverless.yml file on each pull request
|  |   |--deploy-preprod-on-push.yml    # This github action allows us to deploy our lambda on preprod using github push
|  |   \--deploy-prod-on-release.yml    # This github action allows us to deploy our lambda on prod using github release
|
+--serverless_config                
|  |
|  |--preprod.yml                       # File containing all the variables necessary for the deployment with serverless in preproduction
|  \--prod.yml                          # File containing all the variables necessary for the deployment with serverless in production
|   
+--serverless_lambda_exemple              
|  |
|  |--_init_.py                         # This is used to mark directories as pasckage in python
|  \--handler.py                        # The code ouf our lambda
|          
|--.gitignore                           # Used to ignore certain non-essential file types 
|--package.json                         # File used to manage the project dependencies like version etc..
|--package-lock.json                    # File to keep track of the exact version of every package
|--README.md                            # Documentation about the code
|--requirements.txt                     # File that contains all libraries and packages we need  
\--serverless.yml                       # File that define your AWS Lambda Functions, like events or aws infrastructure resources they require   
```

## Github branching
Here we will see some basic of github branching action. You only need one main branch. If you want to deploy your 
lambda in preprod you need to push your code to the main branch. In case you want to deploy it on prod then use 
the github release 

## Init
Serverless framework install
```sh
npm install -g serverless
```

Init new project
```sh
serverless create --template aws-python --path dps-serverless-lambda-example
```

serverless.yml reference doc : https://www.serverless.com/framework/docs/providers/aws/guide/serverless.yml/

## Develop
**Prerequisite:** a working serverless cli install

Import dependencies
```sh
npm install
```

Deploy stack to AWS
```sh
serverless deploy --stage preprod
```

## Plugins
### How to install a plugin ?
```sh
sls plugin install --name PLUGIN_NAME
```
### serverless-python-requirements
Add python dependencies to the deployed package using *requirements.txt* file.

https://www.serverless.com/plugins/serverless-python-requirements

### serverless-stage-manager
Manage variables for multiple environments, useful for handling prod/preprod vars.

https://www.serverless.com/plugins/serverless-stage-manager

## 

