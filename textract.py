import boto3
import json
import sys
import time

class DocumentProcessor:
    jobId = ''
    region_name = ''

    roleArn = ''
    bucket = ''
    document = ''

    sqsQueueUrl = ''
    snsTopicArn = ''

    def __init__(self, role, bucket, document, region):
        self.roleArn = role
        self.bucket = bucket
        self.document = document
        self.region_name = region

        self.textract = boto3.client('textract', region_name=self.region_name)
        self.sqs = boto3.client('sqs', region_name=self.region_name)
        self.sns = boto3.client('sns', region_name=self.region_name)
        self.s3 = boto3.client('s3', region_name=self.region_name)

    def ProcessDocument(self, type):

        jobs = {}

        # Determine which type of processing to perform
        if type["get_document_text_detection"] == 1:
            document_text_detection_response = self.textract.start_document_text_detection(
                DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn},
                OutputConfig={'S3Bucket': self.bucket}
                )
            print('Processing type: Detection')
            jobs["document_text_detection_job_id"] = document_text_detection_response["JobId"]

        # For document analysis, select which features you want to obtain with the FeatureTypes argument
        if type["get_document_analysis"] == 1:
            document_analysis_response = self.textract.start_document_analysis(
                DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                FeatureTypes=["TABLES", "FORMS"],
                NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn},
                OutputConfig={'S3Bucket': self.bucket}
                )
            print('Processing type: Analysis')
            jobs["document_analysis_job_id"]= document_analysis_response["JobId"]

        # Determine which type of processing to perform
        if type["get_expense_analysis"] == 1:
            expense_analysis_response = self.textract.start_expense_analysis(
                DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': self.document}},
                NotificationChannel={'RoleArn': self.roleArn, 'SNSTopicArn': self.snsTopicArn},
                OutputConfig={'S3Bucket': self.bucket}
                )
            print('Processing type: Expense Analysis')
            jobs["document_expense_analysis"]= expense_analysis_response["JobId"]

        return jobs

    def CreateTopicandQueue(self):

        millis = str(int(round(time.time() * 1000)))

        # Create SNS topic
        snsTopicName = "AmazonTextractTopic" + millis

        topicResponse = self.sns.create_topic(Name=snsTopicName)
        self.snsTopicArn = topicResponse['TopicArn']

        # create SQS queue
        sqsQueueName = "AmazonTextractQueue" + millis
        self.sqs.create_queue(QueueName=sqsQueueName)
        self.sqsQueueUrl = self.sqs.get_queue_url(QueueName=sqsQueueName)['QueueUrl']

        attribs = self.sqs.get_queue_attributes(QueueUrl=self.sqsQueueUrl,
                                                AttributeNames=['QueueArn'])['Attributes']

        sqsQueueArn = attribs['QueueArn']

        # Subscribe SQS queue to SNS topic
        self.sns.subscribe(
            TopicArn=self.snsTopicArn,
            Protocol='sqs',
            Endpoint=sqsQueueArn)

        # Authorize SNS to write SQS queue
        policy = """{{
            "Version":"2012-10-17",
            "Statement":[
                {{
                    "Sid":"MyPolicy",
                    "Effect":"Allow",
                    "Principal" : {{"AWS" : "*"}},
                    "Action":"SQS:SendMessage",
                    "Resource": "{}",
                    "Condition":{{
                        "ArnEquals":{{
                            "aws:SourceArn": "{}"
                        }}
                    }}
                }}
            ]
        }}""".format(sqsQueueArn, self.snsTopicArn)

        response = self.sqs.set_queue_attributes(
            QueueUrl=self.sqsQueueUrl,
            Attributes={
                'Policy': policy
            })

    def DeleteTopicandQueue(self):
        self.sqs.delete_queue(QueueUrl=self.sqsQueueUrl)
        self.sns.delete_topic(TopicArn=self.snsTopicArn)

                
    def GetResults(self, jobId, analysis_type, next_token):
        maxResults = 1000
        paginationToken = next_token
        
        analysis_results = {}
        if analysis_type == "get_document_analysis":
            if paginationToken == None:
                analysis_results["document_analysis_response"] = self.textract.get_document_analysis(JobId=jobId,
                                                                MaxResults=maxResults)
            else:
                analysis_results["document_analysis_response"] = self.textract.get_document_analysis(JobId=jobId,
                                                                MaxResults=maxResults,
                                                                NextToken=paginationToken)

        if analysis_type == "get_document_text_detection":
            if paginationToken == None:
                analysis_results["document_text_detection_response"] = self.textract.get_document_text_detection(JobId=jobId,
                                                                        MaxResults=maxResults)
            else:
                analysis_results["document_text_detection_response"] = self.textract.get_document_text_detection(JobId=jobId,
                                                                        MaxResults=maxResults,
                                                                        NextToken=paginationToken)

        if analysis_type == "get_expense_analysis":
            if paginationToken == None:
                analysis_results["document_expense_analysis_response"] = self.textract.get_expense_analysis(JobId=jobId,
                                                                        MaxResults=maxResults)
            else:
                analysis_results["document_expense_analysis_response"] = self.textract.get_expense_analysis(JobId=jobId,
                                                                        MaxResults=maxResults,
                                                                        NextToken=paginationToken)

        return analysis_results
