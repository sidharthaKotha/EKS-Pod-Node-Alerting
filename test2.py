import json
import base64
import boto3
import re
import os
import subprocess
import shlex
import sys
import smtplib
import datetime
from botocore.signers import RequestSigner
from contextlib import redirect_stdout

def alertingfunc(cluster_id, region):

    # define variables
    initialtime = ""

    STS_TOKEN_EXPIRES_IN = 60
    session = boto3.session.Session(profile_name='default')

    client = session.client('sts', region_name=region)
    c = client.get_caller_identity()

    service_id = client.meta.service_model.service_id

    signer = RequestSigner(
        service_id,
        region,
        'sts',
        'v4',
        session.get_credentials(),
        session.events
    )

    params = {
        'method': 'GET',
        'url': 'https://sts.{}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15'.format(region),
        'body': {},
        'headers': {
            'x-k8s-aws-id': cluster_id
        },
        'context': {}
    }

    signed_url = signer.generate_presigned_url(
        params,
        region_name=region,
        expires_in=STS_TOKEN_EXPIRES_IN,
        operation_name=''
    )

    base64_url = base64.urlsafe_b64encode(
        signed_url.encode('utf-8')).decode('utf-8')

    output = subprocess.check_output(
        "kubectl get event -A -o custom-columns=NAME:.metadata.name,REASON:.reason", shell=True)
    events = output.decode('utf-8').split()
    print(events)

    # alerting or notifications to email or SNS

    emaillist = ["sidhartha.kotha@gmail.com"]

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
            TopicArn='arn:aws:sns:us-west-2:031679903962:newproject-NewprojectTopic2D161F5E-7N7IKAK5GFU',   #add the topic arn 
            Message='Alert: pod or node broken',    
        )
        #print(response)

    if os.path.getsize("events.txt") == 0:
        print("No previous data related to kubectl events recorded")
        initialoutput = subprocess.check_output(
            "kubectl get events -o custom-columns=Firstseen:.firstTimestamp --sort-by='.firstTimestamp'", shell=True)
        newevents = initialoutput.decode('utf-8').split()
        newevents.reverse()
        initialtime = str(newevents[0])
        with open('events.txt', 'w') as f:
            with redirect_stdout(f):
                print(newevents[0])
        f.close()
    else:
        files = open("events.txt", "r+")
        prevtime = str(files.read()).split()
        newtime = prevtime[0]
        #print(prevtime)

    newoutput = subprocess.check_output(
        "kubectl get events -o custom-columns=Firstseen:.firstTimestamp --sort-by='.firstTimestamp'", shell=True)
    newevents = newoutput.decode('utf-8').split()
    newevents.reverse()
    currenttime = str(newevents[0])
    #print(type(currenttime))
    #print(currenttime)
    if(initialtime == currenttime):
        with open('events.txt', 'w') as f:
            with redirect_stdout(f):
                print(newevents[0])
        f.close()
    elif(newtime == currenttime):
        sys.exit()
    else:
        with open('events.txt', 'w') as f:
            with redirect_stdout(f):
                print(newevents[0])
        f.close()

    for previous, current in zip(events, events[1:]):
        if current == "RemovingNode":
            event = "Alert: A node is getting removed from cluster:" + previous
            print(event)
            send_email(event)
            sns_notification(event)
            continue
        elif current == "NotNotReady":
            event = "Alert: One of the node is in Not Ready state:" + previous
            print(event)
            send_email(event)
            sns_notification(event)
            continue
        elif current == "FailedScheduling":
            event = "Alert: Pod is failed to schedule:" + previous
            print(event)
            #send_email(event)
            sns_notification(event)
            continue
        elif current == "Failed":
            event = "Alert: FailedToCreateContainer or FailedToStartContainer or FailedToPullImage:" + previous
            print(event)
            send_email(event)
            sns_notification(event)
            continue
        elif current == "Killing":
            event = "Alert: KillingContainer:" + previous
            print(event)
            send_email(event)
            sns_notification(event)
            continue
        elif current == "NodeNotSchedulable":
            event = "Alert: NodeNotSchedulable:" + previous
            print(event)
            send_email(event)
            sns_notification(event)
            continue
        else:
            None
    return 0


# change cluster name and region
alertingfunc("attractive-gopher", "us-west-2")
