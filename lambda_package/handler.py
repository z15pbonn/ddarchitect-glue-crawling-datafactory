import botocore
import boto3
import json
import pandas as pd
import sys
import time

def convert(val):
    val = val.replace('` object', '` string')
    val = val.replace('` datetime64[ns]', '` timestamp')
    val = val.replace('` date-time', '` timestamp')
    val = val.replace('` int32', '` int')
    val = val.replace('` int64', '` int')
    val = val.replace('` Int32', '` int')
    val = val.replace('` Int64', '` int')
    val = val.replace('` integer', '` int')
    val = val.replace('` float64', '` double')
    val = val.replace('` long', '` bigint')
    val = val.replace('` category', '` string')
    return val


def wait_query(client, response):
    fin_requete = False
    while fin_requete == False:
        response_get_query_details = client.get_query_execution(
            QueryExecutionId=response['QueryExecutionId']
        )
        status = response_get_query_details['QueryExecution']['Status']['State']
        if status == 'QUEUED':
            time.sleep(1)
        else:
            fin_requete = True


def main(event, context):
    print('lecture des droits AWS cli')
    s3client = boto3.client('s3', region_name='eu-west-1')
    print(event)
    input = json.loads(event['body'])

    folder = input["s3_folder"]
    idcardsrc = input["idcard"]
    schema = input["glue_schema"]
    obj = ''
    cut = folder.split('/')
    table = cut[len(cut) - 1]

    print('Traitement de la table ' + table)
    delta = False

    if folder.find('_delta') > 0:
        delta = True

    bucket = 'ppd-dct-tech-datafactory'
    file = idcardsrc.replace('s3://ppd-dct-tech-datafactory/', '')
    try:
        print('Get idcard ' + file)
        obj = s3client.get_object(
            Bucket=bucket,
            Key=file
        )
    except botocore.exceptions.ClientError as error:
        response = error.response
        code = response['Error']['Code']
        message = response['Error']['Message']
        if code == 'NoSuchKey':
            print(f'No Such Key, {code}:\n{message}')
            raise error
        else:
            print(code + message)
            raise error
    print(obj)
    idcard = obj['Body'].read().decode('utf-8')
    data = json.loads(idcard)
    df = pd.DataFrame(data['fields'])

    request = ''
    partition = ''
    tblproperties = "'s3_path'='" + folder + "',"
    for index, row in df.iterrows():
        datatype = str(row['type'])
        if datatype == 'struct':
            struct = ''
            jsonstruct = row['struct']
            for champ in jsonstruct:
                struct += str(champ['name']) + ':'+str(champ['type']) + ','
            datatype = 'struct<' + struct[:-1] + '>'
        if len(str(row['description'])) > 0:
            request += '`' + str(row['name']) + '`' + ' ' + datatype + \
                ' COMMENT "' + str(row['description']) + '",'
        else:
            request += '`' + str(row['name']) + '`' + ' ' + datatype + ','
    request = convert(request)[:-1]

    part = df[df['partitionKey'] == True].sort_values(by='partitionOrder')
    if len(part) > 0:
        for index, row in part.iterrows():
            partition += '`' + str(row['name']) + \
                '_part`' + ' ' + str(row['type']) + ','
        partition = 'PARTITIONED BY ( ' + convert(partition)[:-1] + ')'
    if delta == True:
        folderfinal = folder + '/_symlink_format_manifest/'
    else:
        folderfinal = folder
    description = data['description']
    if delta == True:
        storageType = '''
        ROW FORMAT SERDE 
        'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
        STORED AS INPUTFORMAT 
        'org.apache.hadoop.hive.ql.io.SymlinkTextInputFormat'
        OUTPUTFORMAT 
        'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
        '''
        tblproperties += "'delta.compatibility.symlinkFormatManifest.enabled'='true',"
    else:
        storageType = '''
        ROW FORMAT SERDE 
        'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe' 
        STORED AS INPUTFORMAT 
        'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat' 
        OUTPUTFORMAT 
        'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat'
        '''
    formatted_file_list = []

    print('Start Athena process')
    client = boto3.client('athena', region_name='eu-west-1')
    try:
        print('Drop old table in Glue Catalog')
        response_drop = client.start_query_execution(
            QueryString='DROP TABLE `'+schema+'`.`'+table+'`', WorkGroup='dataarchitecture-nursery')
        wait_query(client, response_drop)
        print('Create table in Glue Catalog')
        response = client.start_query_execution(QueryString='CREATE EXTERNAL TABLE `'+schema+'`.`'+table+'`(' + request + ')' + partition + ' ' + storageType
                                                + '''LOCATION
            ''' + "'" + folderfinal + "'" + '''
            TBLPROPERTIES (
            ''' + tblproperties+'''
            'CrawlerSchemaDeserializerVersion'='1.0', 
            'CrawlerSchemaSerializerVersion'='1.0')''', WorkGroup='dataarchitecture-nursery')
        print('Update table partitions in Glue Catalog')
        wait_query(client, response)
        response_msck = client.start_query_execution(
            QueryString='MSCK REPAIR TABLE `'+schema+'`.`'+table+'`', WorkGroup='dataarchitecture-nursery')
        wait_query(client, response_msck)
    except (botocore.exceptions.ClientError, botocore.exceptions.WaiterError) as error:
        response = error.response
        code = response['Error']['Code']
        message = response['Error']['Message']
        if code == 'InvalidRequestException':
            print(f'Error in query, {code}:\n{message}')
            raise error
        elif code == 'InternalServerException':
            print(f'AWS {code}:\n{message}')
            raise error
        elif code == 'TooManyRequestsException':
            # Handle a wait, retry, etc here
            pass
        else:
            print(f'AWS {code}:\n{message}')
            raise error

    response = {
        "statusCode": 200,
        "statusDescription": "200 OK",
        "isBase64Encoded": False,
        "headers": {
            "Content-Type": "text/html; charset=utf-8"
        },
        "body": "{\"message\":\"Traitement réussi\"}"
	}
    return response