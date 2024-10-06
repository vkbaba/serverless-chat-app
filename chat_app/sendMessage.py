import json
import boto3
import os
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    try:
        dynamo = boto3.client("dynamodb")
        connectionId = event["requestContext"]["connectionId"]
        endpointUrl = os.environ["endpointurl"]
        tableName = os.environ["TableName"]
        chatAppTable = boto3.resource("dynamodb").Table(tableName)
        apigw = boto3.client("apigatewaymanagementapi", endpoint_url = endpointUrl)

        # ユーザーのルームIDを取得
        queryParams = {
            "TableName": tableName,
            "KeyConditionExpression": "connectionId = :connId",
            "ExpressionAttributeValues": {":connId": {"S": connectionId}},
            "ProjectionExpression": "roomId"
        }
        queryResponse = dynamo.query(**queryParams)["Items"]

        # チャットルームに参加していない
        if not queryResponse:
            dataObj = {
                "type": "error",
                "connectionId": connectionId,
                "roomId": "",
                "message": "Please join a room before sending a message"
            }
            apigw.post_to_connection(
                ConnectionId = connectionId,
                Data = json.dumps(dataObj).encode("utf-8")
            )
            print(f"User {connectionId} tried to send a message without joining a room")
            return {"statusCode": 403}

        # チャットルームに参加している
        roomId = queryResponse[0]["roomId"]["S"]
        # ルームに参加しているユーザーのconnectionIdを取得
        queryParams = {
            "TableName": tableName,
            "IndexName": "roomId-index",
            "KeyConditionExpression": "roomId = :room_id_val",
            "ExpressionAttributeValues": {":room_id_val": {"S": roomId}},
            "ProjectionExpression": "connectionId"
        }

        users = dynamo.query(**queryParams)["Items"]
        for user in users:
            userConnectionId = user["connectionId"]["S"]
            # 自分以外のユーザーにメッセージを送信
            if userConnectionId != connectionId:
                dataObj = {
                    "type": "sendMessage",
                    "connectionId": connectionId,
                    "roomId": roomId,
                    "message": json.loads(event["body"])["message"]
                }
                apigw.post_to_connection(
                    ConnectionId = userConnectionId,
                    Data = json.dumps(dataObj).encode("utf-8")
                ) 
        print(f"Message sent to users in room {roomId} by {connectionId}")
        return {"statusCode": 200}

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}