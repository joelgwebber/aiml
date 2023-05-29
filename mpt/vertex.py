from google.cloud import aiplatform
from google.cloud.aiplatform.private_preview.language_models import ChatModel, InputOutputTextPair

aiplatform.init(
    # your Google Cloud Project ID or number
    # environment default used is not set
    project='fs-dsa-prod',

    # the Vertex AI region you will use
    # defaults to us-central1
    location='us-central1',

    # Google Cloud Storage bucket in same region as location
    # used to stage artifacts
    staging_bucket='gs://fs-dsa-prod-llm-tool',

    # custom google.auth.credentials.Credentials
    # environment default creds used if not set
    # credentials=my_credentials,

    # customer managed encryption key resource name
    # will be applied to all Vertex AI resources if set
    # encryption_spec_key_name=my_encryption_key_name,

    # the name of the experiment to use to track
    # logged metrics and parameters
    experiment='my-experiment',

    # description of the experiment above
    experiment_description='my experiment decsription'
)

chat_model = ChatModel.from_pretrained("chat-bison-001")

chat = chat_model.start_chat(
    context="My name is Ned. You are my personal assistant. My favorite movies are Lord of the Rings and Hobbit.",
    examples=[
        InputOutputTextPair(input_text="Who do you work for?",
                            output_text="I work for Ned.", ),
        InputOutputTextPair(input_text="What do I like?",
                            output_text="Ned likes watching movies.", ),
    ],
    temperature=0.3, )

rsp = chat.send_message("Do you know any cool events this weekend?")
print(rsp)
