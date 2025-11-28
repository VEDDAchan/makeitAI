# app.py - makeitAI by veddAI with FULL WebContainers.io Live Previews
import streamlit as st
import openai
import google.generativeai as genai
import requests
import os
import json
import zipfile
from dotenv import load_dotenv
from io import BytesIO
import tempfile
import streamlit.components.v1 as components

load_dotenv()

# API Setup
openai.api_key = os.getenv("OPENAI_API_KEY")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
GROK_API_KEY = os.getenv("XAI_API_KEY")

st.set_page_config(page_title="makeitAI by veddAI", layout="wide")

st.markdown("""
<h1 style='text-align: center;'>
    makeitAI <span style='color: #00D4FF;'>by veddAI</span>
</h1>
<p style='text-align: center; font-size: 1.3rem; color: #aaa;'>
    Speak or type → Generate websites & apps → <strong>Live preview with WebContainers.io</strong>
</p>
""", unsafe_allow_html=True)

# Input Section
col1, col2 = st.columns([4, 1])
with col1:
    prompt = st.text_area("What do you want to build?", height=160,
                          placeholder="Examples:\n• A portfolio website with dark mode\n• A todo mobile app with login")
with col2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    audio_bytes = st.audio_input("Speak your idea")

# Voice Transcription
if audio_bytes:
    with st.spinner("Transcribing..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes.getvalue())
            path = f.name
        with open(path, "rb") as af:
            transcript = openai.audio.transcriptions.create(model="whisper-1", file=af)
        prompt = transcript.text
        st.success(f"Transcribed: **{prompt}**")
        os.unlink(path)

if prompt.strip():
    st.info(f"Ready to generate → **{prompt}**")

# Sidebar
with st.sidebar:
    st.markdown("# Choose Your AI")
    ai_choice = st.radio("AI Model", ["ChatGPT (gpt-4o-mini)", "Gemini 1.5 Flash", "Grok Beta"])
    st.markdown("---")
    st.markdown("**makeitAI by veddAI**")
    st.caption("Live Previews Powered by WebContainers.io")

# Generate Button
if st.button("🪄 Generate Now!", type="primary", use_container_width=True):
    if not prompt.strip():
        st.error("Please speak or type your idea first!")
    else:
        with st.spinner(f"Building with {ai_choice}... (10-30 sec)"):
            system_prompt = """
            You are an expert full-stack developer. Based on the user's description, generate EITHER a complete website OR a mobile app.
            Return ONLY valid JSON with these exact keys:
            {
                "type": "website" or "app",
                "name": "Project name",
                "description": "Short description",
                "code": "Complete single-file code:
                         - For website: React + TailwindCSS (src/App.jsx with all imports and export default App)
                         - For app: React Native Expo (App.js with all imports and export default function App)",
                "package_json": "Complete package.json as JSON string (with dependencies like react, vite, tailwind for website; expo for app, and scripts: { 'start': 'vite' or 'expo start --web' })",
                "deployment": "Step-by-step guide to deploy (Vercel for websites, Expo for apps)"
            }
            """

            try:
                if "ChatGPT" in ai_choice:
                    response = openai.chat.completions.create(
                        model="gpt-4o-mini",
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    raw = response.choices[0].message.content

                elif "Gemini" in ai_choice:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response = model.generate_content(
                        f"{system_prompt}\nUser request: {prompt}",
                        generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
                    )
                    raw = response.text

                else:  # Grok
                    headers = {"Authorization": f"Bearer {GROK_API_KEY}", "Content-Type": "application/json"}
                    payload = {
                        "model": "grok-beta",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"}
                    }
                    resp = requests.post("https://api.x.ai/v1/chat/completions", json=payload, headers=headers)
                    resp.raise_for_status()
                    raw = resp.json()["choices"][0]["message"]["content"]

                data = json.loads(raw)
                project_type = data.get("type", "project").title()

                st.success(f"✅ {project_type} generated with {ai_choice}!")

                # Tabs
                tab1, tab2, tab3, tab4 = st.tabs(["Code", "Live Preview (WebContainers.io)", "Deployment Guide", "Download ZIP"])

                with tab1:
                    lang = "javascript" if data.get("type") == "app" else "jsx"
                    st.code(data.get("code", "// No code generated"), language=lang)
                    st.code(data.get("package_json", "{}"), language="json")

                with tab2:
                    st.markdown("### Live Preview with WebContainers.io")
                    if st.button("🚀 Start Preview (Boots Node.js in Browser)"):
                        with st.spinner("Booting WebContainer... (20-40 sec first time)"):
                            # WebContainer embed script (from official docs)
                            preview_html = f"""
                            <div id="container" style="width:100%;height:800px;">
                                <div id="logs" style="background:#000;color:#0f0;padding:10px;height:150px;overflow:auto;font-family:monospace;font-size:12px;"></div>
                                <iframe id="preview" style="width:100%;height:600px;border:1px solid #ccc;" src="about:blank"></iframe>
                            </div>
                            <script type="module">
                                import {{ WebContainer }} from 'https://unpkg.com/@webcontainer/api@latest';
                                const logDiv = document.getElementById('logs');
                                const iframe = document.getElementById('preview');
                                
                                const log = (data) => {{
                                    logDiv.innerHTML += data + '<br>';
                                    logDiv.scrollTop = logDiv.scrollHeight;
                                }};
                                
                                log('Booting WebContainer...');
                                const wc = await WebContainer.boot({{ coep: 'credentialless', forwardPreviewErrors: true }});
                                
                                // Mount files
                                const files = {{
                                    'package.json': {{ file: {{ contents: `{data.get('package_json', '{}')}` }} }},
                                    'App.js': {{ file: {{ contents: `{data.get('code', '')}` }} }},
                                    'index.html': {{ file: {{ contents: '<div id="root"></div><script type="module" src="main.js"></script>' }} }},
                                    'main.js': {{ file: {{ contents: 'import ReactDOM from "react-dom"; ReactDOM.render(document.getElementById("root")); ' }} }}
                                }};
                                await wc.mount(files);
                                
                                // Install deps
                                log('Installing dependencies...');
                                const install = await wc.spawn('npm', ['install']);
                                install.output.pipeTo(new WritableStream({{ write: log }}));
                                await install.exit;
                                
                                // Start server
                                log('Starting server...');
                                const start = await wc.spawn('npm', ['start']);
                                start.output.pipeTo(new WritableStream({{ write: log }}));
                                
                                // Server ready
                                wc.on('server-ready', (port, url) => {{
                                    log(`Preview ready at ${{url}}`);
                                    iframe.src = url;
                                }});
                                
                                wc.on('error', (err) => log(`Error: ${{err.message}}`));
                            </script>
                            """
                            components.html(preview_html, height=850)

                with tab3:
                    st.markdown(data.get("deployment", "No deployment steps provided"))

                with tab4:
                    buffer = BytesIO()
                    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        main_file = "App.jsx" if data.get("type") == "website" else "App.js"
                        zf.writestr(main_file, data.get("code", ""))
                        zf.writestr("package.json", data.get("package_json", "{}"))
                        zf.writestr("README.md", f"# {data.get('name', 'My Project')}\n\n{data.get('description', '')}\n\n## Deployment\n{data.get('deployment', '')}")
                    buffer.seek(0)
                    st.download_button(
                        "📦 Download Full Project ZIP",
                        buffer.getvalue(),
                        file_name=f"{data.get('name', 'my-project').lower().replace(' ', '-')}-makeitAI.zip",
                        mime="application/zip"
                    )

            except Exception as e:
                st.error(f"API Error: {str(e)}")
                st.info("Tip: Add $5 to OpenAI for unlimited generations. Voice uses Whisper (free with key).")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #888;'>Made with ❤️ by veddAI • Powered by makeitAI + WebContainers.io</p>", unsafe_allow_html=True)