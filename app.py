from flask import Flask,request
from cloudpathlib import S3Path

from textract import DocumentProcessor
from config import config_by_name
import json
import datetime

import textract

app = Flask(__name__)
app.config.from_object(config_by_name['dev'])

def get_from_expenses(data, target):
    try:
        id_block = 0
        for page in data['document_expense_analysis_response']['ExpenseDocuments']:
            for summary_field in page['SummaryFields']:
                if summary_field['Type']['Text'] == target:
                    return summary_field['ValueDetection']['Text']
    except:
        return('')

def get_electric_quote(data, target):
    try:
        id_block = 0
        for block in data['document_analysis_response']['Blocks']:
            id_block = id_block + 1
            if block['BlockType'] == "WORD" and block['Text'].__contains__(target):
                return_string = data['document_analysis_response']['Blocks'][id_block]['Text'] + ' ' + data['document_analysis_response']['Blocks'][id_block + 1]['Text'] + ' ' + data['document_analysis_response']['Blocks'][id_block + 2]['Text'] + ' ' + data['document_analysis_response']['Blocks'][id_block + 3]['Text'] + ' ' + data['document_analysis_response']['Blocks'][id_block + 4]['Text'] + ' ' + data['document_analysis_response']['Blocks'][id_block + 5]['Text'] + ' ' + data['document_analysis_response']['Blocks'][id_block + 6]['Text'] + ' ' + data['document_analysis_response']['Blocks'][id_block + 7]['Text']
                return(return_string)
            else:
                continue
    except:
        return('')

def get_particular_data(data, target):

    try:
        # a.- and b.-
        id_block = 0
        for block in data['document_analysis_response']['Blocks']:
            id_block = id_block + 1
            if block['BlockType'] == "LINE" and block['Text'].__contains__(target):
                break
            else:
                continue

        # c.-
        id_target =data['document_analysis_response']['Blocks'][id_block-1]['Relationships'][0]['Ids'][0]

        # d.- and e.-
        id_block_2 = 0
        for block in data['document_analysis_response']['Blocks']:
            id_block_2 = id_block_2 + 1
            if block['BlockType'] == "KEY_VALUE_SET":
                try:
                    id_block_counter = 0
                    for id_block in block['Relationships']:
                        id_block_counter = id_block_counter + 1
                        for id_ in id_block['Ids']:
                            if id_ == id_target:
                                id_target_2 = id_
                                id_block_2_target = id_block_2
                                break
                except:
                    continue
            else:
                continue

        # f.-
        id_target_rel = data['document_analysis_response']['Blocks'][id_block_2_target - 1]['Relationships'][0]['Ids'][0]
        if data['document_analysis_response']['Blocks'][id_block_2_target]['Id'] == id_target_rel:
            this_is_true = True

        # g.-
        array_ids_rel = []
        for id_value in data['document_analysis_response']['Blocks'][id_block_2_target]['Relationships'][0]['Ids']:
            if this_is_true:
                array_ids_rel.append(id_value)

        # h.- and i.-
        text_string_to_return = ''
        for id_value in array_ids_rel:
            for block in data['document_analysis_response']['Blocks']:
                id_block_2 = id_block_2 + 1
                if block['BlockType'] == "WORD" and block['Id'] == id_value:
                    text_string_to_return = text_string_to_return + ' ' + block['Text']

        return(text_string_to_return)
    except:
        return('')

@app.route("/")
def index():
    return "<p>Hi there!</p>"

@app.route("/textract_analysis", methods=["POST"])
def textract_analysis():
    if request.method == 'POST':
        request_data = request.get_json()
        s3_url = S3Path(request_data['s3_url'])
        s3_bucket = s3_url.bucket
        s3_file = s3_url.key
        requested_analysis = {
            "get_document_analysis": 1,
            "get_document_text_detection": 1,
            "get_expense_analysis": 1
        }
        role_arn = app.config["ROLE_ARN"]
        region = app.config["REGION"]
        analyzer = DocumentProcessor(role_arn, s3_bucket, s3_file, region)
        analyzer.CreateTopicandQueue()
        jobs = analyzer.ProcessDocument(requested_analysis)
        analyzer.DeleteTopicandQueue()
        job_s = jobs["document_analysis_job_id"] + "-" + jobs["document_expense_analysis"]
        return {"s3_bucket": s3_bucket, "doc_name": s3_file, "job": job_s, "timestamp": datetime.datetime.now() }, 200
    
@app.route("/textract_analysis_results", methods=["POST"])
def fetch_results():
    if request.method == 'POST':

        request_data = request.get_json()
        analysis_job_id = request_data["JobId"]

        s3_bucket = ''
        s3_file = ''
        next_token = request_data["next_token"] if "next_token" in request_data else None
        role_arn = app.config["ROLE_ARN"]
        region = app.config["REGION"]

        job_id_1 = analysis_job_id.split('-')[0]
        job_id_2 = analysis_job_id.split('-')[1]


        # Expenses
        analyzer = DocumentProcessor(role_arn, s3_bucket, s3_file, region)
        analysis_results = analyzer.GetResults(jobId=job_id_2,analysis_type='get_expense_analysis', next_token=next_token)

        # Analysis
        analyzer_2 = DocumentProcessor(role_arn, s3_bucket, s3_file, region)
        analysis_results_2 = analyzer_2.GetResults(jobId=job_id_1,analysis_type='get_document_analysis', next_token=next_token)
        try:
            # Get all field values
            fields = { "electric_quote": get_electric_quote(analysis_results_2, '2.0TD').strip(),
                       "contract_power": get_particular_data(analysis_results_2, 'otencia Contratada').strip(),
                       "total_energy_consumed": get_particular_data(analysis_results_2, 'onsumida').strip(),
                       "counter_renting": get_particular_data(analysis_results_2, 'Alquiler').strip(),
                       "invoice_total": get_from_expenses(analysis_results, 'TOTAL').strip(),
                       "CUPS": get_particular_data(analysis_results_2, 'CUPS').strip(),
                       "owner": get_particular_data(analysis_results_2, 'Titular').strip(),
                       "CIF/NIF": get_particular_data(analysis_results_2, 'NIF').strip(),
                       "address": get_from_expenses(analysis_results, 'ADDRESS').strip(),
                       "installation_address": get_particular_data(analysis_results_2, 'suministro').strip()
                      }

            return {"JobId":analysis_job_id, "analysis_results": fields}, 200
        except:
            return({'Error': 'Not identified'})
