import json
import boto3
import os

def lambda_handler(event, context):
    try:
        dynamo = boto3.client("dynamodb")
        connectionId = event["requestContext"]["connectionId"]
        tableName = os.environ["TableName"]
        queryParams ={
            "TableName": tableName,
            "KeyConditionExpression": "connectionId = :connId",
            "ExpressionAttributeValues": {
                ":connId": {"S": connectionId}  
            },
            "ProjectionExpression":"roomId"
        }
        queryResponse = dynamo.query(**queryParams)["Items"]
        roomId = queryResponse[0]["roomId"]["S"]
        dynamo.delete_item(
            TableName = tableName,
            Key = {
                    "connectionId":{"S": connectionId},
                    "roomId":{"S": roomId}
                }
        )
        print(f"User {connectionId} disconnected from room {roomId}")
        return {"statusCode":200}

    except Exception as e:
        print("Error occures: ",e)
        return {"statusCode":500}