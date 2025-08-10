import gradio as gr
import uuid

from agent.rrd_agent import graph
from agent.tools.utilities import _print_event

thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
    }
}
_printed = set()
def do_what(what):
    events = graph.stream(
            {"messages": ("user", what)}, config, stream_mode="values"
        )
    for event in events:
        x=_print_event(event, _printed)
        
    print(f"x > {x}")
    return x


with gr.Blocks(title=f"RRD Bot", theme=gr.themes.Default()) as demo:
    gr.Markdown("# Realtime Reputation Defender Bot")
    chatbot = gr.Chatbot(
        type="messages", 
        # avatar_images=['user.png', 'gemini.png'], 
        render_markdown=True, 
        show_copy_all_button=True,
        height=600)
    msg = gr.Textbox(label="Ask me anything about reputation...")
    clear = gr.Button("Clear")

    def user(user_message, history: list):
        return "", history + [{"role": "user", "content": user_message}]

    def bot(history: list):
        bot_message = do_what(history[-1]['content'])
        print(bot_message)
        history.append({"role": "assistant", "content": bot_message})
        # for character in bot_message:
        #     history[-1]['content'] += character
            # time.sleep(0.05)
        yield history

    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch()