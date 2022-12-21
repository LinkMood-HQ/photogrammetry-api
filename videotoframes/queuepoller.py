from videotoframe import videotoframe
from framedownloader import framedownloader
import boto3
import os
from objectuploader import uploader
import requests
import sys

from imagedetect import imagedetect

sqs = boto3.client('sqs')
s3_client = boto3.client('s3', region_name='us-east-1')
output_directory = './frames'
queue_url = 'https://sqs.us-east-1.amazonaws.com/099829585053/scan-queue'
api_url = 'https://quickscan.live/finalobject'

# Send message to SQS queue
# Receive message from SQS queue
def queuepolling():
    response = {}
    i = 0
    while('Messages' not in response):

        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'collection_id',
                'number_of_images',
                's3_bucket_links',
                'uuid'
            ],
            VisibilityTimeout=1000,
            WaitTimeSeconds=10
        )


        i += 1
        print( "Polled",i, response)

    message = response['Messages'][0]
    # print(message['MessageAttributes']['s3_bucket_links']['BinaryValue'])

    
    framedownloader(message)

    print('Completed video to frame processing, generating model now...')

    Uploaded = uploader(message)

    tagarray = imagedetect()
    
    objectinfo = {
        "uuid": message['MessageAttributes']['uuid']['StringValue'],
        "collection_id": message['MessageAttributes']['collection_id']['StringValue'],
        "Uploaded": Uploaded,
        "tag_array": tagarray
    }
    x = requests.post(api_url, data=objectinfo)  
        
    print('Completed Model')



    # print(message)
    receipt_handle = message['ReceiptHandle']


    # Do all that needs to be done within 10 minutes
    # download frames using s3 link or google drive link 
    #Delete received message from queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    print('Received and deleted message: %s' % message)




if __name__ == '__main__': 

    while True:
        queuepolling()
