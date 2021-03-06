from kubernetes import client, config, watch
import smtplib
import boto3
import os
import subprocess
import threading 

# Configs can be set in Configuration class directly or using helper utility
config.load_kube_config()

v1 = client.CoreV1Api()
w = watch.Watch()

# writing definition for watching all the pod events
def pod_events():
    for event in w.stream(v1.list_pod_for_all_namespaces):
        if(event['type']=='DELETED'):
            print("Event: %s %s %s" % (event['type'], event['object'].metadata.name, event['object'].status.pod_ip))
            #send_email(event['object'].metadata.name)
            sns_notification(event['object'].metadata.name)
        else:
            None

# writing definition for watching all the node events
def node_events():
    for event in w.stream(v1.list_node):
        if(event['type']=='DELETED'):
            print("Event: %s %s" % (event['type'], event['object'].metadata.name))
            #send_email(event['object'].metadata.name)
            sns_notification(event['object'].metadata.name)
        else:
            None

# writing definition to send notifications to email or mobile messages
emaillist = ["example@gmail.com"]

def send_email(event):
    for member in emaillist:
        sender = smtplib.SMTP('smtp.gmail.com', 587)
        sender.starttls()
        sender.login("sender_email_id", "sender_email_id_password")
        message = "Node-Pod alerting mechanism:" + event
        sender.sendmail("sender_email_id", dest, message)
        sender.quit()

def sns_notification(event):
    sns = boto3.client('sns')
    response = sns.publish(
        TopicArn='arn:aws:sns:us-west-2:03167990xxxx:newproject-NewprojectTopic2D161F5E-7N7IKAK5xxx',   #add the topic arn 
        Message='Alert: pod or node broken',    
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
