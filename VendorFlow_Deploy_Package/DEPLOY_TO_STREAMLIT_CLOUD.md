# Publish VendorFlow as a public URL (Streamlit Community Cloud)

This project is already a Streamlit app. You do not convert `app.py` into HTML; Streamlit hosts the Python application and gives it a public `*.streamlit.app` URL.

## 1. Create a GitHub repository

1. Sign in to GitHub and create a new repository named `vendorflow-demo`.
2. Set the repository to **Public** if the reviewer must open the app without being invited. A public repository also makes the source code public.
3. Extract `VendorFlow_Deploy_Package.zip` on your computer.
4. Open the new GitHub repository, choose **Add file → Upload files**, and upload the *contents* of the extracted folder (not the ZIP file itself). Keep `app.py` at the repository root and retain the `vendorflow/`, `demo/`, `.streamlit/`, and `tests/` folders.
5. Commit the files to the `main` branch.

## 2. Deploy on Streamlit Community Cloud

1. Open https://share.streamlit.io/ and sign in with the same GitHub account.
2. Choose **Create app**.
3. Select repository `vendorflow-demo`, branch `main`, and main file path `app.py`.
4. Set a memorable app URL/subdomain, such as `vendorflow-demo-sai` (if available).
5. Click **Deploy**. When deployment completes, copy the generated `https://<your-subdomain>.streamlit.app` URL and test it in an incognito/private browser window.

Official deployment guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app

## Important demo-data note

The local SQLite database is intentionally not included in this deployment package. On first launch, the app creates a fresh database and seeds the synthetic demo vendor. Use synthetic records only. Hosted local-file storage is not durable; run history and uploaded files may be cleared when the hosted app restarts or is redeployed. Do not upload real PAN, GSTIN, banking details, or vendor documents.

## Optional: Render

A `render.yaml` Blueprint is included for Render deployment. Connect the same GitHub repository in Render and deploy the Blueprint. The free Render service can spin down after inactivity and loses changes to its local filesystem on restart/redeploy, so treat its SQLite history as disposable demo data.
