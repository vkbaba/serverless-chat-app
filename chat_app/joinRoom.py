import json
import boto3
import os
import random
import string

def lambda_handler(event,context):
    try:
        dynamo = boto3.client("dynamodb")
        connectionId = event["requestContext"]["connectionId"]
        roomId = json.loads(event["body"])["roomId"]
        endpointUrl = os.environ["endpointurl"]
        tableName = os.environ["TableName"]
        chatAppTable = boto3.resource("dynamodb").Table(tableName)
        apigw = boto3.client("apigatewaymanagementapi", endpoint_url = endpointUrl)

        # Room ID が未入力の場合、新規チャットルームを作成
        if roomId == "":
            # チャットルームを新規作成
            # Room ID として6桁のランダムな英語大文字と数字の組み合わせを生成
            roomId = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            chatAppTable.put_item(
                Item = {
                    "connectionId": connectionId,
                    "roomId": roomId,
                }
            )
            dataObj = {
                "type": "createRoom",
                "connectionId": connectionId,
                "roomId": roomId,
                "message": "Room created with ID : " + roomId
            }
            response = apigw.post_to_connection(ConnectionId = connectionId, Data = json.dumps(dataObj).encode("utf-8"))
            print(f"Room is created with id {roomId} for {connectionId}")
            return {"statusCode": 200} 
        else:
            queryParams = {
                "TableName": tableName,
                "IndexName": "roomId-index", 
                "KeyConditionExpression": "roomId = :room_id",
                "ExpressionAttributeValues": {
                    ":room_id": {"S": roomId}  
                }
            }
            # Room IDが一致するアイテムを取得
            queryResponse = dynamo.query(**queryParams)["Items"]
            # Room ID が入力されている場合、指定のチャットルームに参加
            if len(queryResponse) == 0:
                dataObj = {
                    "type": "error",
                    "connectionId": connectionId,
                    "roomId": "",
                    "message": "Room does not exist"
                }
                apigw.post_to_connection(ConnectionId = connectionId, Data = json.dumps(dataObj).encode("utf-8"))
                return {"statusCode":403}
            else:
                chatAppTable.put_item(
                    Item = {
                        "connectionId":connectionId,
                        "roomId":roomId,
                    }
                )
                dataObj = {
                    "type": "joinRoom",
                    "connectionId": connectionId,
                    "roomId": roomId,
                    "message": "Successfully joined the room"
                }
                apigw.post_to_connection(ConnectionId = connectionId, Data = json.dumps(dataObj).encode("utf-8"))
                print(f"User with {connectionId} joined the room {roomId}")
                return {"statusCode":200}
    except Exception as e:
        print("Error: ", e)
        return {"statusCode":500}
    
