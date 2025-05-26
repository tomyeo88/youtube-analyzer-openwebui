# HAI-5014 Open WebUI demo

Repo for the Open WebUI demo in class HAI5014. Before installing the Open WebUI, make sure you have the following:

- A Google Gemini API key
- A Supabase account

## Supabase

- Create new project in Supabase called `openwebui` [https://supabase.com/dashboard/](https://supabase.com/dashboard/)
- Copy `Session pooled (Shared Pooler)` connection string

If you are using Codespaces:

- Save this connection string as `DATABASE_URL` and `PGVECTOR_DB_URL` environment variable (In Codespace settings, secrets & variables)

If you are running this locally:

- Rename `.env.example` to `.env` and fill in the required environment variables
- Save the connection string as `DATABASE_URL` and `PGVECTOR_DB_URL` environment variable in `.env` file

## Google Gemini API key

- Get your Google gemini API key [https://aistudio.google.com/app/apikeys](https://aistudio.google.com/app/apikeys)

If you are using Codespaces:

- Save this API key as `OPENAI_API_KEY` environment variable (In Codespace settings, secrets & variables)

If you are running this locally:

- Make sure that your file `.env.example` is renamed to `.env` and fill in the required environment variables
- Save the API key as `OPENAI_API_KEY` environment variable in `.env` file

## Codespace

- Open repo in Codespaces
- Check if the environment variables are set correctly by running `echo $DATABASE_URL` and `echo $PGVECTOR_DB_URL`
- Run OpenWebUI with the command `dotenv run open-webui serve`

A pop-up should indicate that a webserver has launched. If not, click the "ports" tab in the terminal window, and open the website.

Walk through the Open WebUI *get started* wizard and create an admin account. Make sure to remember your password :)

### Additional settings

#### Standard model:

In the Open WebUI **admin panel**, go to Settings -> Models

- Click the gear icon on the upper right
- Scroll down to 'Default Models' and select a model (e.g. `gemini-2.5-flash-preview`)  

#### Embeddings model

In the Open WebUI **admin panel**, go to Settings -> Documents -> Embedding and change the following

- Embedding Model Engine: `https://generativelanguage.googleapis.com/v1beta/openai`
- API Key: your Google API key
- Embedding Model: `text-embedding-004`


## Want to run this locally?

There are two options to run this locally:

1. Run open-webui in a Python *virtual environment* on your local machine
2. Install docker and open the repository in a *devcontainer* on your local machine

### Option 1: Python virtual environment

1. Make sure you have Python 3.10+ installed
2. Create a virtual environment

    ```bash
    python3 -m venv venv
    ```

3. Activate the virtual environment

    ```bash
    source venv/bin/activate
    ```

4. Install the requirements

    ```bash
    pip install -r requirements.txt
    ```

5. Rename `.env.example` to `.env` and fill in the required environment variables
6. Run the Open WebUI

    ```bash
    dotenv run open-webui serve
    ```

7. Open the web browser and go to [`http://localhost:8080`](http://localhost:8080)
8. Walk through the Open WebUI *get started* wizard and create an admin account. Make sure to remember your password :)

### Option 2: Docker

See the [Open WebUI documentation]()


## Troubleshooting

### Stop the server

If you want to stop the server, open the terminal and press `CTRL + C`. This will stop the server and close the web browser.

You can then run the server again with the command `dotenv run open-webui serve`.

### Resetting the database

If you want to reset the database, you can run the following SQL command in Supabase SQL editor:

```sql
DO $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
        EXECUTE 'DROP TABLE IF EXISTS "' || rec.tablename || '" CASCADE;';
    END LOOP;
END $$;
```

### Warning

⚠️ **CAUTION**: The SQL command above will delete ALL tables in your database. Only use this if you want to completely reset your OpenWebUI installation. Make sure you have backups of any important data before running this command.

Remember that API keys should be kept secure and never committed to version control. Using services like Google Gemini API and Supabase may incur costs depending on your usage.