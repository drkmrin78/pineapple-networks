import boto3
import time

def create_containter(event, context):
        
    ec2Id = 'i-0496bbb980eb17cae' 
    
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[ec2Id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands':[
                        'docker run --name "{}" -p {}:8080 -d -t rahmanusta/cloudterm'.format(event['Id'], event['Port'])
                    ],
            },
            Comment=(event["User"]+": "+event["Id"] +","+ event["Port"]))
            
    commandId = response["Command"]['CommandId']
    time.sleep(2)
    output = ssm_client.get_command_invocation( 
                                        CommandId = commandId,
                                        InstanceId = ec2Id
                                    )
    
    return output['Status']

def remove_container(event, context):
        
    ec2Id = 'i-0496bbb980eb17cae' 
    
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[ec2Id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands':[
                        'docker kill {}'.format(event['Id']),
                        'docker rm {}'.format(event['Id'])
                    ],
            },
            Comment=("removing: "+event["Id"]))
            
    commandId = response["Command"]['CommandId']
    time.sleep(2)
    output = ssm_client.get_command_invocation( 
                                        CommandId = commandId,
                                        InstanceId = ec2Id
                                    )
    
    return output['Status']

def create_network(event, context):
        
    ec2Id = 'i-0496bbb980eb17cae' 
    
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[ec2Id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands':[
                        'docker network create -d bridge --subnet={0}.0/24 --gateway={0}.225 {1}'.format(event['Netmask'], event['Network'])
                    ],
            },
            Comment=("creating: "+event["Network"]+","+event["Netmask"]))
            
    commandId = response["Command"]['CommandId']
    time.sleep(5)
    output = ssm_client.get_command_invocation( 
                                        CommandId = commandId,
                                        InstanceId = ec2Id
                                    )
    
    return output['Status']

def remove_network(event, context):
        
    ec2Id = 'i-0496bbb980eb17cae' 
    
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[ec2Id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands':[
                        'docker network rm {}'.format(event['Network'])
                    ],
            },
            Comment=("removing: "+event["Network"]))
            
    commandId = response["Command"]['CommandId']
    time.sleep(3)
    output = ssm_client.get_command_invocation( 
                                        CommandId = commandId,
                                        InstanceId = ec2Id
                                    )
    
    return output['Status']

def add_container_to_network(event, context):
        
    ec2Id = 'i-0496bbb980eb17cae' 
    
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[ec2Id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands':[
                        'docker network connect {1} {0}'.format(event['Container'], event['Network'])
                    ],
            },
            Comment=("Adding "+event["Container"] +" to "+ event["Network"]))
            
    commandId = response["Command"]['CommandId']
    time.sleep(2)
    output = ssm_client.get_command_invocation( 
                                        CommandId = commandId,
                                        InstanceId = ec2Id
                                    )
    
    return output['Status']

def remove_container_from_network(event, context):
        
    ec2Id = 'i-0496bbb980eb17cae' 
    
    ssm_client = boto3.client('ssm')
    response = ssm_client.send_command(
        InstanceIds=[ec2Id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands':[
                        'docker network disconnect {1} {0}'.format(event['Container'], event['Network'])
                    ],
            },
            Comment=("Removing "+event["Container"] +" to "+ event["Network"]))
            
    commandId = response["Command"]['CommandId']
    time.sleep(2)
    output = ssm_client.get_command_invocation( 
                                        CommandId = commandId,
                                        InstanceId = ec2Id
                                    )
    
    return output['Status']
