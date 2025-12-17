from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

def extract_text_from_document(file_bytes, endpoint, key):
    client = DocumentAnalysisClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key)
    )

    poller = client.begin_analyze_document(
        "prebuilt-layout",
        file_bytes
    )
    result = poller.result()

    text_blocks = []
    for page in result.pages:
        for line in page.lines:
            text_blocks.append(line.content)

    return "\n".join(text_blocks)
