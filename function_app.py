import logging
import os
from datetime import datetime

from azure.storage.blob import BlobServiceClient
import azure.functions as func
import azure.durable_functions as df
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
import openai

my_app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Create BlobServiceClient using the connection string from settings
blob_service_client = BlobServiceClient.from_connection_string(os.environ.get("BLOB_STORAGE_ENDPOINT"))

@my_app.blob_trigger(arg_name="myblob", path="input", connection="BLOB_STORAGE_ENDPOINT")
@my_app.durable_client_input(client_name="client")
async def blob_trigger(myblob: func.InputStream, client):
    logging.info(f"Processed blob: {myblob.name}, Size: {myblob.length} bytes")
    blobName = myblob.name.split("/")[1]
    await client.start_new("process_document", client_input=blobName)

@my_app.orchestration_trigger(context_name="context")
def process_document(context):
    blobName: str = context.get_input()
    retry_options = df.RetryOptions(first_retry_interval_in_milliseconds=5000, max_number_of_attempts=3)
    result = yield context.call_activity_with_retry("analyze_pdf", retry_options, blobName)
    result2 = yield context.call_activity_with_retry("summarize_text", retry_options, result)
    result3 = yield context.call_activity_with_retry("write_doc", retry_options, {"blobName": blobName, "summary": result2})
    logging.info(f"Summary written: {result3}")
    return f"Summary written as: {result3}"

@my_app.activity_trigger(input_name='blobName')
def analyze_pdf(blobName):
    logging.info("Starting analyze_pdf activity")
    container_client = blob_service_client.get_container_client("input")
    blob_client = container_client.get_blob_client(blobName)
    blob = blob_client.download_blob().read()
    logging.info(f"Downloaded blob size: {len(blob)} bytes")
    
    endpoint = os.environ["COGNITIVE_SERVICES_ENDPOINT"]
    key = os.environ["COGNITIVE_SERVICES_KEY"]
    
    document_analysis_client = DocumentAnalysisClient(endpoint, AzureKeyCredential(key))
    poller = document_analysis_client.begin_analyze_document("prebuilt-layout", document=blob)
    result_pages = poller.result().pages
    
    doc = ""
    for page in result_pages:
        for line in page.lines:
            doc += line.content + "\n"
    
    logging.info("Completed analyze_pdf activity")
    return doc

@my_app.activity_trigger(input_name='results')
def summarize_text(results):
    logging.info("Starting summarize_text activity")
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    prompt = f"Can you explain what the following text is about?\n\n{results}"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=200
    )
    
    summary = response.choices[0].message.get('content', '').strip()
    logging.info(f"OpenAI API returned: {summary}")
    return {"content": summary}

@my_app.activity_trigger(input_name='results')
def write_doc(results):
    logging.info("Starting write_doc activity")
    container_client = blob_service_client.get_container_client("output")
    
    summary_filename = results['blobName'] + "-" + datetime.now().strftime("%Y%m%d%H%M%S")
    sanitized_filename = summary_filename.replace(".", "-")
    fileName = sanitized_filename + ".txt"
    
    summary_content = results['summary']['content']
    logging.info("Uploading summary: " + summary_content)
    container_client.upload_blob(name=fileName, data=summary_content)
    return fileName