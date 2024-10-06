import boto3
import json
import time
import random
import string
import os


def lambda_handler(event, context):
    try:
        dynamo = boto3.client("dynamodb")
        connectionId = event["requestContext"]["connectionId"]
        roomKey = json.loads(event["body"]).get("roomKey")
        if roomKey is None:
            roomKey = ""

        endpointUrl = os.environ["endpointurl"]
        tableName = os.environ["TableName"]
        api_resp = boto3.client("apigatewaymanagementapi", endpoint_url=endpointUrl)
        
        # ルームIDの生成
        timestamp = int(time.time())
        random_part = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        roomId = f"{random_part}-{timestamp}"
        
        chatAppTable = boto3.resource("dynamodb").Table(tableName)
        resp = chatAppTable.put_item(
            Item={
                "connectionId": connectionId,
                "roomId": roomId,
                "roomKey": roomKey,
            }
        )
        response = api_resp.post_to_connection(ConnectionId=connectionId, Data=json.dumps("Room created with ID : "+roomId).encode("utf-8"))
        print(f"Room is created with id {roomId} for {connectionId}")
        return {"statusCode": 200} 
    
    except Exception as e:
        print("Error: ", e)
        return {"statusCode": 500}