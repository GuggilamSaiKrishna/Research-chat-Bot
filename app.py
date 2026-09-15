import os
import gradio as gr
from server import app as fastapi_app

# Mount FastAPI web application on Gradio for Hugging Face Free Spaces
app = gr.mount_gradio_app(fastapi_app, gr.Blocks(title="Vignan Research Matching Chatbot"), path="/")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7860))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
