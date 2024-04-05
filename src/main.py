import asyncio
import asyncpg
import numpy as np

from google.oauth2 import service_account
from google.cloud.sql.connector import Connector
from pgvector.asyncpg import register_vector

from gdrive.utils import (
    get_google_drive_api_service,
    get_drive_metadata_list,
    create_text_blocks
)

from gcloud.utils import (
    embedding_function,
    check_if_data_on_gcs,
    get_data_from_gcs,
    upload_dataframe_to_gcs
)

project_id = ""
location = ""

instance = "postgres-vectordb"

db_connection = f"{project_id}:{location}:{instance}"

database = "gdrive-db"

db_user = "default"
pwd = ""

service_account_json_path = """"""
client_secrets_file = """"""

credentials = service_account.Credentials.from_service_account_file(
    service_account_json_path)

print("Checking if file exists")

if not check_if_data_on_gcs(project_id, credentials):
    print("Creating file")
    service = get_google_drive_api_service(client_secrets_file)
    items = get_drive_metadata_list(service)
    text_blocks = create_text_blocks(service, items)

    df = embedding_function(project_id, location, credentials, text_blocks)
    upload_dataframe_to_gcs(project_id, credentials, df)

else:
    print("Loading file")
    df = get_data_from_gcs(service_account_json_path)

async def main():

    loop = asyncio.get_running_loop()
    async with Connector(loop=loop) as connector:
        conn: asyncpg.Connection = await connector.connect_async(
            db_connection,
            "asyncpg",
            user=db_user,
            password=pwd,
            db=database,
        )

        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await register_vector(conn)

        await conn.execute("DROP TABLE IF EXISTS gdrive_embeddings")
        await conn.execute(
            """CREATE TABLE gdrive_embeddings(
                                block_id VARCHAR(1024) NOT NULL,
                                text_block TEXT,
                                embedding vector(768))"""
        )

        for index, row in df.iterrows():
            await conn.execute(
                "INSERT INTO gdrive_embeddings (block_id, text_block, embedding) VALUES ($1, $2, $3)",
                row['block_id'],
                row['text_block'],
                np.fromstring(row['embedding'][1:-1], dtype=np.float64, sep=','),
                )

        await conn.close()

if __name__ == "__main__":
    #asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
