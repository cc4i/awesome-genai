import os
from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import FastAPI, Depends, Request
from starlette.config import Config
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from urllib.parse import urlparse, urlunparse
# import uvicorn
import gradio as gr
from utils.acceptance import to_snake_case
from models.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, DEV_MODE


# Fast
app = FastAPI()

config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

app.add_middleware(SessionMiddleware, secret_key="is_not_a_secret")
    

# Dependency to get the current user
def get_user(request: Request):
    user = request.session.get('user')
    if user:
        return user['name']
    return None

@app.get('/')
def public(user: dict = Depends(get_user)):
    if user:
        return RedirectResponse(url='/gradio')
    else:
        return RedirectResponse(url='/main')

@app.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@app.route('/login')
async def login(request: Request):
    redirect_uri = request.url_for('auth')
    print(f"redirect_uri: {redirect_uri}")
    # If your app is running on https, you should ensure that the
    # `redirect_uri` is https, e.g. uncomment the following lines:
    #
    if SECRET_KEY is not None:
        redirect_uri = urlunparse(urlparse(str(redirect_uri))._replace(scheme='https'))
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.route('/auth')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url='/')
    request.session['user'] = dict(access_token)["userinfo"]
    return RedirectResponse(url='/')

with gr.Blocks(theme=gr.themes.Glass(), title="Creative GeN/Studio") as login_demo:
    gr.Markdown("## Welcome to Creative GeN/Studio", container=False)
    gr.Image("images/gemini-star.png", width=400, interactive=False)
    gr.Button("Login", link="/login")

app = gr.mount_gradio_app(app, login_demo, path="/main")

def greet(request: gr.Request):
    if DEV_MODE == "true":
        username = "default"
    else:
        username = request.username
    
    return f"""
        # Creative GeN/Studio
        Ignite the spark of <b>{username}</b>'s inner creator ... powered by <b>CC</b>
    """, to_snake_case(username)

