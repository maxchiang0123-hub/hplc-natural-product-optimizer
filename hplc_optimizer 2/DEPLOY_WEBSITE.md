# Publish the HPLC Optimizer as a website

The app is already a Streamlit web application. This package is ready to upload to a GitHub repository and deploy on Streamlit Community Cloud.

1. Create a GitHub account or sign in at https://github.com.
2. Create a new repository, e.g. `hplc-natural-product-optimizer`.
3. Upload `app.py`, `requirements.txt`, `README.md`, `.streamlit/config.toml` and optionally this guide to the repository root (preserve the `.streamlit` subfolder).
4. Visit https://share.streamlit.io and sign in using GitHub.
5. Select **Create app** / **Deploy an app**, choose the repository and branch, and enter `app.py` as the main file path.
6. Deploy and wait for the app to build. The hosting service will provide a shareable HTTPS URL.

If the app fails to build, check the deployment logs and confirm that `requirements.txt` is at the repository root.

## Privacy and validation

Streamlit Community Cloud hosting is not suitable for confidential or unpublished lab data unless the institution approves the hosting and access controls. Prefer synthetic/public data or a privately hosted approved environment. The software accepts CSV exports, not direct Agilent instrument control. Gradient suggestions are heuristic and require laboratory validation.
