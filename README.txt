J.A.R.V.I.S. v2.5.3 — RENDER BDFD BRIDGE EDITION
=================================================

WHAT THIS DEPLOYMENT DOES
-------------------------
- Gives BDFD a public HTTPS host on Render (your-service.onrender.com).
- Runs the JARVIS BDFD chat engine in the cloud, so the phone does not need
  to stay online after deployment.
- Exposes only authenticated BDFD API routes and /healthz.
- Does NOT publish the JARVIS dashboard, Omni Router endpoints, settings,
  gateway management, file tools, self-upgrade UI or admin routes.
- Reads the bridge token and AI provider credentials from Render secrets.

IMPORTANT: This is a cloud BDFD API service. It is separate from the full
JARVIS dashboard you run locally in Pydroid 3. The cloud service has its own
AI provider configuration set through Render Environment variables.

DEPLOY WITH RENDER BLUEPRINT (EASIEST)
-------------------------------------
1. Extract this ZIP.
2. Create a NEW private GitHub repository, for example JARVIS-Render-Bridge.
3. Upload the extracted project files to the repository root. Do not upload
   a ZIP as a single file; Render needs render.yaml and source files at root.
4. In Render, choose New > Blueprint and connect that GitHub repository.
5. Render reads render.yaml. Choose the Free plan if it is offered.
6. Enter the required environment values when Render prompts you, then deploy.

REQUIRED RENDER ENVIRONMENT VARIABLES
--------------------------------------
JARVIS_BDFD_TOKEN
  Generate a private token by running `python generate_token.py` in a
  Python terminal, or generate one with Python:
    import secrets; print("jbf_" + secrets.token_urlsafe(48))
  Paste the generated value into Render's JARVIS_BDFD_TOKEN field. Keep
  it private. Do not put it in GitHub and do not send it in chat.

JARVIS_PROVIDER_API_KEY
  API key for the cloud model provider. Add it only in Render's Environment
  page as a secret. Never commit it to GitHub or put it in BDFD source code.

JARVIS_PROVIDER_MODEL
  The exact model ID supported by that provider. It must support tool
  calling for JARVIS's full agent/tool behavior. Use the model ID from the
  provider's own model list or dashboard.

JARVIS_PROVIDER_BASE_URL
  Defaults to https://openrouter.ai/api/v1. Change this only if you use a
  different OpenAI-compatible provider endpoint.

JARVIS_PROVIDER_NAME / JARVIS_PROVIDER_ID / JARVIS_PROVIDER_KIND
  Optional labels/settings. Defaults are OpenRouter / openrouter / openai.

MANUAL RENDER WEB SERVICE SETTINGS
----------------------------------
Runtime: Python 3
Build command: pip install -r requirements.txt
Start command: gunicorn render_service:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 180 --access-logfile -
Health check path: /healthz
Plan: Free for testing

CONNECT BDFD
------------
After Render says the service is Live, your host is:
  https://YOUR-SERVICE-NAME.onrender.com

Test this in a browser:
  https://YOUR-SERVICE-NAME.onrender.com/healthz
Expected response is JSON with `"ok": true`.

In your BDFD custom command, use the host and the same JARVIS_BDFD_TOKEN:

  $nomention
  $httpAddHeader[Authorization;Bearer YOUR_RENDER_BDFD_TOKEN]
  $httpAddHeader[Content-Type;application/x-www-form-urlencoded]
  $httpPost[https://YOUR-SERVICE-NAME.onrender.com/api/bdfd/chat;message=$url[encode;$message]&author_id=$authorID&author_name=$url[encode;$username]&channel_id=$channelID&guild_id=$guildID&session_id=$authorID&persona=J.A.R.V.I.S.]
  $onlyIf[$httpStatus==200;JARVIS connection error. HTTP $httpStatus]
  $sendMessage[$httpResult[reply];false]

Replace both placeholders. The bridge token belongs only in BDFD's private
command configuration and Render Environment. Do not share screenshots that
reveal the token.

FREE PLAN LIMITATIONS
---------------------
- Render Free web services spin down after 15 minutes without traffic. The
  next request can take about a minute to wake the service.
- The free filesystem is ephemeral. BDFD conversation history and the
  outbound queue can be cleared after spin-down, restart or redeploy.
- The provider key and bridge token remain in Render Environment variables,
  not in the filesystem or repository.
- For persistent local files, Render requires a paid web service with a
  persistent disk. The free PostgreSQL option is temporary and expires.

SECURITY
--------
- Keep the GitHub repository private if preferred; never commit secrets.
- Do not share the bridge token.
- The Render service allow-lists only BDFD routes. Unlisted paths return 404.
- Rotate the token by changing JARVIS_BDFD_TOKEN in Render Environment and
  updating the token in BDFD, then redeploy.
