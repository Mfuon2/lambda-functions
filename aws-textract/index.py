
"""
Purpose
An AWS lambda function that analyzes documents with Amazon Textract.
"""
import json
import base64
import logging
import boto3

from collections import defaultdict
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
textract_client = boto3.client('textract')
s3 = boto3.client('s3')


def get_key_value_map(blocks):
    key_map = {}
    value_map = {}
    block_map = {}
    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map, value_map, block_map

def get_kv_relationship(key_map, value_map, block_map):
    kvs = defaultdict(list)
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key.lower().replace('\'', '').replace('.', '').replace(':', '').strip().replace(' ', '_')].append(val.strip())
    return kvs

def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block

def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X'
    return text

def format_findings(original_json):
    formatted_json = {
        key: [value.strip() for value in values]
        for key, values in original_json.items()
    }
    result = {key: values[0] for key, values in formatted_json.items()}
    return result

def get_s3_object(bucket_name_event, object_key_event):
    bucket_name = bucket_name_event
    object_key = object_key_event
    s3_object_url = f"s3://{bucket_name}/{object_key}"
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    content = response['Body'].read()
    return content

def extract_business_info(response):
    blocks = response['Blocks']
    python_object = json.loads(json.dumps(blocks))
    line_texts = []
    for block in python_object:
        if block["BlockType"] == "LINE":
            line_texts.append(block["Text"])

    business_no = None
    for item in line_texts:
        if item.startswith("BUSINESS NO."):
            business_no = item.split("BUSINESS NO. ")[1]
            break

    agency_name = line_texts[6]

    registration_date = None
    for item in line_texts:
        if "Given under my hand at NAIROBI on" in item:
            registration_date = item.split("Given under my hand at NAIROBI on ")[1]
            break

    business_info = {
        "business_no": business_no,
        "business_name": agency_name,
        "registration_date": registration_date
    }
    res = json.loads(json.dumps(business_info, indent=4))
    return res

def extract_certificate_of_incorporation_info(response):
    blocks = response['Blocks']
    python_object = json.loads(json.dumps(blocks))
    line_texts = []
    for block in python_object:
        if block["BlockType"] == "LINE":
            line_texts.append(block["Text"])
    company_name = line_texts[3]
    business_info = {
        "company_name": company_name,
    }
    res = json.loads(json.dumps(business_info, indent=4))
    return res

def lambda_handler(event, context):
    """
    Lambda handler function
    param: event: The event object for the Lambda function.
    param: context: The context object for the lambda function.
    return: The list of Block objects recognized in the document
    passed in the event object.
    """

    try:

        # Determine document source.
        if 'image' in event:
            logger.info(event['image'])
            # Decode the image
            image_bytes = event['image'].encode('utf-8')
            img_b64decoded = base64.b64decode(image_bytes)
            image = {'Bytes': img_b64decoded}


        elif 's3_object' in event:
            image = get_s3_object(event['s3_object']['Bucket'], event['s3_object']['Name'])
            image = {'Bytes': image}

        else:
            raise ValueError(
                'Invalid source. Only image base 64 encoded image bytes or S3Object are supported.')
        response = textract_client.analyze_document(Document=image, FeatureTypes=['FORMS'])
        blocks = response['Blocks']
        key_map, value_map, block_map = get_key_value_map(blocks)
        kvs = get_kv_relationship(key_map, value_map, block_map)
        type = event['document_type']
        lambda_y = None

        if type == 'BUSINESS_REGISTRATION':
            lambda_y = extract_business_info(response)
        elif type == 'CERTIFICATE_OF_INCORPORATION':
            lambda_y = extract_certificate_of_incorporation_info(response)
        else:
            lambda_y = format_findings(kvs)



        lambda_response = {
            "code":200,
            "msg":"Successful",
            "data": lambda_y
            # "meta":blocks
        }

    except ClientError as err:
        error_message = "Couldn't analyze image. " + \
                        err.response['Error']['Message']

        lambda_response = {
            'code': 400,
            'data': {
                "Error": err.response['Error']['Code'],
                "ErrorMessage": error_message
            }
        }
        logger.error("Error function %s: %s",
                     context.invoked_function_arn, error_message)

    except ValueError as val_error:
        lambda_response = {
            'code': 400,
            'data': {
                "Error": "ValueError",
                "ErrorMessage": format(val_error)
            }
        }
        logger.error("Error function %s: %s",
                     context.invoked_function_arn, format(val_error))

    return lambda_response
