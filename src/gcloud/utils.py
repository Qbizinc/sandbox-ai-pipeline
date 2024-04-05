import gcsfs
import pandas as pd

from google.cloud import aiplatform
from google.cloud import storage
from vertexai.language_models import TextEmbeddingModel


def embedding_function(project_id, location, credentials, text_blocks):
    """
    Generates vector using vertex AI pretrained model and created pandas
    Dataframe with values

    Args:
    - project_id (str): Project ID from GCP.
    - location (str): Location of GCP
    - credentials: credentials object of service account
    - text_blocks: Blocks of text to vectorize

    Returns:
    - List: Vectors.
    """
    pd_dic = {"block_id": [],
              "text_block": [],
              "embedding": []
              }


    aiplatform.init(project=project_id, location=location,
                    credentials=credentials)

    model = TextEmbeddingModel.from_pretrained("textembedding-gecko@001")

    for block in text_blocks:
        embeddings = model.get_embeddings([block["text_block"]])
        pd_dic["block_id"].append(block["block_id"])
        pd_dic["text_block"].append(block["text_block"])
        pd_dic["embedding"].append(embeddings[0].values)

    return pd.DataFrame(pd_dic)


def check_if_data_on_gcs(project_id, credentials):
    """
    Check if data exists in bucket

    Args:
    - project_id (str): Project ID from GCP.
    - credentials: credentials object of service account

    Returns:
    - Bool
    """

    vector_csv = "data/gdrive_vectorized.csv"
    storage_client = storage.Client(project=project_id,
                                    credentials=credentials)
    bucket_name = "qbiz-gdrive-vectordata"
    bucket = storage_client.bucket(bucket_name)
    stats = storage.Blob(bucket=bucket, name=vector_csv).exists(storage_client)

    return stats


def get_data_from_gcs(credentials_json):
    """
    Get csv data from gcs

    Args:
    - credentials_json: path where credentials are stored

    Returns:
    - pd.DataFrame: Pandas dataframe with vector data
    """
    vector_csv = "gcs://qbiz-gdrive-vectordata/data/gdrive_vectorized.csv"
    df = pd.read_csv(vector_csv,
                     sep=",",
                     storage_options={"token": credentials_json})
    return df


def upload_dataframe_to_gcs(project_id, credentials, DataFrame):
    """
    Check if data exists in bucket

    Args:
    - project_id (str): Project ID from GCP.
    - credentials: credentials object of service account

    Returns:
    - Bool
    """

    vector_csv = "data/gdrive_vectorized.csv"
    storage_client = storage.Client(project=project_id,
                                    credentials=credentials)
    bucket_name = "qbiz-gdrive-vectordata"
    bucket = storage_client.bucket(bucket_name)

    bucket.blob(vector_csv).upload_from_string(DataFrame.to_csv(index=False),
                                               'text/csv')

