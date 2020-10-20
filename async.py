from kubernetes import watch
import boto3
import threading
import os

# Configs can be set in Configuration class directly or using helper utility
from kubernetes import config

KUBE_CONFIG_DEFAULT_LOCATION = os.environ.get('KUBECONFIG', '~/.kube/config')
# writing definition for getting k8s configuration
def k8s_configuration():
    try:
        configuration = config.load_kube_config()
    except Exception:
        configuration = config.load_incluster_config()
    return configuration
k8s_configuration() #declaration of k8s_configuration

from kubernetes import client
v1 = client.CoreV1Api()
w = watch.Watch()

# writing definition for watching all the pod events
def pod_events():
    for event in w.stream(v1.list_pod_for_all_namespaces):
        if(event['type']=='DELETED'):
            print("Event: %s %s %s" % (event['type'], event['object'].metadata.name, event['object'].status.pod_ip))
            sns_notification(event['object'].metadata.name,event['type'])
        elif (event['type']=='ADDED'):
            print("Event: %s %s %s" % (event['type'], event['object'].metadata.name, event['object'].status.pod_ip))
            sns_notification(event['object'].metadata.name,event['type'])
        elif (event['type']=='MODIFIED'):
            print("Event: %s %s %s" % (event['type'], event['object'].metadata.name, event['object'].status.pod_ip))
            sns_notification(event['object'].metadata.name,event['type'])
        else:
            None

# writing definition for watching all the node events
def node_events():
    for event in w.stream(v1.list_node):
        if(event['type']=='DELETED'):
            print("Event: %s %s" % (event['type'], event['object'].metadata.name))
            sns_notification(event['object'].metadata.name,event['type'])
        elif (event['type']=='ADDED'):
            print("Event: %s %s" % (event['type'], event['object'].metadata.name))
            sns_notification(event['object'].metadata.name,event['type'])
        elif (event['type']=='MODIFIED'):
            print("Event: %s %s" % (event['type'], event['object'].metadata.name))
            sns_notification(event['object'].metadata.name,event['type'])
        else:
            None

#add/subscribe the list of email addresses and mobile numbers to your SNS topic 
TopicArn = os.getenv('TopicArn', 'TopicArn')
region = os.getenv('region','region')
ACCESS_ID = os.getenv('ACCESS_ID','ACCESS_ID')
ACCESS_KEY = os.getenv('ACCESS_KEY','ACCESS_KEY')

# define region for your sns boto3 client
sns = boto3.client('sns', region_name=region, aws_access_key_id=ACCESS_ID, aws_secret_access_key= ACCESS_KEY)

def sns_notification(event,eventtype):
    if(eventtype=='ADDED'):
        response=sns.publish(
        TopicArn=TopicArn,  
        Message="Alert: resource "+ event +" added into your cluster",    
        )
    elif(eventtype=='DELETED'):
        response = sns.publish(
            TopicArn=TopicArn, 
            Message="Alert: resource "+ event +" deleted into your cluster",    
        )
    elif(eventtype=='MODIFIED'):
        response = sns.publish(
            TopicArn=TopicArn, 
            Message="Alert: resource "+ event +" modified into your cluster",    
        )
    else:
        response = sns.publish(
            TopicArn=TopicArn, 
            Message='Alert: unknown event occured in your cluster',    
        )

if __name__ == "__main__": 
    print("Printing the deleted pods or nodes")
    # creating threads 
    pod = threading.Thread(target=pod_events, name='pod') 
    node = threading.Thread(target=node_events, name='node')   
  
    # starting threads 
    pod.start() 
    node.start() 
  
    # wait until all threads finish 
    pod.join() 
    node.join() 
