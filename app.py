import streamlit as st
import re
import base64
from io import BytesIO
import pandas as pd
from PIL import Image
import io
import markdown
import pdfkit
from html2image import Html2Image
import os

def convert_latex_to_markdown(text):
    """
    Convert ChatGPT-style LaTeX delimiters to Markdown-compatible delimiters.
    - \( ... \) → $ ... $
    - \[ ... \] → $$ ... $$
    """
    # Convert display equations: \[ ... \] to $$ ... $$
    text = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', text, flags=re.DOTALL)
    
    # Convert inline equations: \( ... \) to $ ... $
    text = re.sub(r'\\\((.*?)\\\)', r'$\1$', text, flags=re.DOTALL)
    
    return text

def markdown_to_html(markdown_text):
    """Convert markdown text to HTML."""
    return markdown.markdown(markdown_text, extensions=['extra', 'codehilite'])

def html_to_pdf(html_content, output_path="output.pdf"):
    """Convert HTML to PDF."""
    try:
        pdfkit.from_string(html_content, output_path)
        return output_path
    except Exception as e:
        st.error(f"Error converting to PDF: {e}")
        return None

def html_to_image(html_content, output_path="output.jpg"):
    """Convert HTML to image."""
    try:
        hti = Html2Image()
        hti.screenshot(html_str=html_content, save_as=output_path)
        return output_path
    except Exception as e:
        st.error(f"Error converting to image: {e}")
        return None

def get_download_link(file_path, link_text, file_type):
    """Generate a download link for a file."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/{file_type};base64,{b64}" download="{os.path.basename(file_path)}">{link_text}</a>'
        return href
    except Exception as e:
        st.error(f"Error creating download link: {e}")
        return None

def main():
    # Set page config FIRST - before any other Streamlit commands
    st.set_page_config(
        page_title="LaTeX to Markdown Converter",
        page_icon="📝",
        layout="wide"
    )
    
    # Hide deploy and menu button (AFTER set_page_config)
    hide_streamlit_style = """
        <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
            .stApp {
                background-color: #f8f9fa;
                color: #212529;
            }
            .stTextArea textarea {
                background-color: #ffffff;
                font-family: 'Courier New', monospace;
            }
            .converted-text {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .css-18e3th9 {
                padding-top: 1rem;
                padding-bottom: 1rem;
            }
            .css-1d391kg {
                padding: 1rem;
            }
            h1, h2, h3 {
                color: #0066cc;
            }
            .stButton>button {
                background-color: #0066cc;
                color: white;
                border-radius: 5px;
            }
            .stButton>button:hover {
                background-color: #004c99;
            }
            .info-box {
                background-color: #e6f3ff;
                padding: 10px;
                border-left: 5px solid #0066cc;
                border-radius: 3px;
            }
            .title-container {
                text-align: center;
                margin-bottom: 2rem;
            }
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    
    # Title with styled container
    st.markdown('<div class="title-container">', unsafe_allow_html=True)
    st.title("LaTeX to Markdown Equation Converter")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    This app converts LaTeX equations from ChatGPT-style formatting to Markdown-compatible formatting:
    <ul>
        <li><code>\\( ... \\)</code> → <code>$ ... $</code> (inline equations)</li>
        <li><code>\\[ ... \\]</code> → <code>$$ ... $$</code> (display equations)</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Example input section
    with st.expander("Show Example Input", expanded=False):
        example_text = """Here's an example of inline LaTeX: \\(E = mc^2\\) in a sentence.

And here's a display equation:
\\[
\\int_{a}^{b} f(x) \\, dx = F(b) - F(a)
\\]

You can have multiple equations in your text:
\\(\\alpha + \\beta = \\gamma\\) and \\(x^2 + y^2 = z^2\\)

Another display equation:
\\[
\\frac{d}{dx}\\left( \\int_{a}^{x} f(t) \\, dt \\right) = f(x)
\\]
"""
        st.code(example_text, language="markdown")
    
    # User input section
    st.subheader("Input Text (with ChatGPT-style LaTeX)")
    
    # Add a paste button
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("Paste"):
            try:
                import pyperclip
                clipboard_text = pyperclip.paste()
                st.session_state.user_input = clipboard_text
            except ImportError:
                st.error("Pyperclip not installed. Please install with: pip install pyperclip")
            except Exception as e:
                st.error(f"Error accessing clipboard: {e}")
    
    # Initialize session state for user input if it doesn't exist
    if 'user_input' not in st.session_state:
        st.session_state.user_input = ""
    
    if 'raw_output' not in st.session_state:
        st.session_state.raw_output = ""
    
    if 'display_mode' not in st.session_state:
        st.session_state.display_mode = "rendered_only"
    
    # Define callback function to update state
    def update_input():
        st.session_state.user_input = st.session_state.input_area
    
    # Text area that updates in real-time
    user_input = st.text_area(
        "Type or paste your text containing LaTeX equations here:",
        value=st.session_state.user_input,
        height=200,
        help="Input text should contain LaTeX equations enclosed in \\( ... \\) for inline equations or \\[ ... \\] for display equations.",
        key="input_area",
        on_change=update_input  # Update the state immediately when text changes
    )
    
    # Display mode selection
    display_modes = ["Show only rendered output", "Show rendered and raw output side by side"]
    display_mode_index = 0 if st.session_state.display_mode == "rendered_only" else 1
    selected_mode = st.radio("Display Mode:", display_modes, index=display_mode_index)
    
    # Update display mode in session state
    st.session_state.display_mode = "rendered_only" if selected_mode == display_modes[0] else "side_by_side"
    
    # Real-time conversion
    if user_input:
        # Initial conversion from input
        if not st.session_state.raw_output:
            converted_text = convert_latex_to_markdown(user_input)
            st.session_state.raw_output = converted_text
        
        # Output section
        st.subheader("Output")
        
        # Update callback for editable raw output
        def update_raw_output():
            st.session_state.raw_output = st.session_state.editable_raw_output
            # Force the page to rerun
            st.experimental_rerun()
        
        if st.session_state.display_mode == "side_by_side":
            col1, col2 = st.columns(2)
            
            # Rendered output column - Use the current raw_output from session state
            with col1:
                st.markdown("### Rendered Output")
                st.markdown(f'<div class="converted-text">{st.session_state.raw_output}</div>', unsafe_allow_html=True)
            
            # Raw output column with editable text area
            with col2:
                st.markdown("### Raw Output (Editable)")
                editable_raw = st.text_area(
                    "Edit converted markdown:",
                    value=st.session_state.raw_output,
                    height=300,
                    key="editable_raw_output",
                    on_change=update_raw_output
                )
        else:
            # Only rendered output - Use the current raw_output from session state
            st.markdown("### Rendered Output")
            st.markdown(f'<div class="converted-text">{st.session_state.raw_output}</div>', unsafe_allow_html=True)
        
        # Export options
        st.subheader("Export Options")
        
        export_col1, export_col2, export_col3, export_col4 = st.columns(4)
        
        # Export to HTML
        with export_col1:
            if st.button("Export to HTML"):
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Exported Markdown</title>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
                        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                        code {{ font-family: 'Courier New', monospace; }}
                    </style>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML" async></script>
                </head>
                <body>
                    {markdown_to_html(st.session_state.raw_output)}
                </body>
                </html>
                """
                
                b64 = base64.b64encode(html_content.encode()).decode()
                href = f'<a href="data:text/html;base64,{b64}" download="converted_markdown.html">Download HTML</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        # Export to Markdown
        with export_col2:
            if st.button("Export to Markdown"):
                b64 = base64.b64encode(st.session_state.raw_output.encode()).decode()
                href = f'<a href="data:text/markdown;base64,{b64}" download="converted_markdown.md">Download Markdown</a>'
                st.markdown(href, unsafe_allow_html=True)
        
        # Export to PDF
        with export_col3:
            if st.button("Export to PDF"):
                st.warning("PDF export requires wkhtmltopdf to be installed on your system")
                try:
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Exported Markdown</title>
                        <meta charset="UTF-8">
                        <style>
                            body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; }}
                            pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                            code {{ font-family: 'Courier New', monospace; }}
                        </style>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML" async></script>
                    </head>
                    <body>
                        {markdown_to_html(st.session_state.raw_output)}
                    </body>
                    </html>
                    """
                    
                    pdf_path = "converted_markdown.pdf"
                    pdfkit.from_string(html_content, pdf_path)
                    
                    with open(pdf_path, "rb") as pdf_file:
                        pdf_bytes = pdf_file.read()
                    
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="converted_markdown.pdf">Download PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Clean up
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                        
                except Exception as e:
                    st.error(f"Error exporting to PDF: {e}")
                    st.info("Make sure wkhtmltopdf is installed on your system.")
        
        # Export to JPG
        with export_col4:
            if st.button("Export to JPG"):
                st.warning("This feature requires html2image package with Chrome or Firefox installed")
                try:
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>Exported Markdown</title>
                        <meta charset="UTF-8">
                        <style>
                            body {{ font-family: Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; background-color: white; }}
                            pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; }}
                            code {{ font-family: 'Courier New', monospace; }}
                        </style>
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.7/MathJax.js?config=TeX-MML-AM_CHTML" async></script>
                    </head>
                    <body>
                        {markdown_to_html(st.session_state.raw_output)}
                    </body>
                    </html>
                    """
                    
                    # Save HTML to a temporary file
                    temp_html = "temp_export.html"
                    with open(temp_html, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    
                    # Convert to image
                    img_path = "converted_markdown.jpg"
                    hti = Html2Image()
                    hti.screenshot(url=os.path.abspath(temp_html), save_as=img_path)
                    
                    # Provide download link
                    with open(img_path, "rb") as img_file:
                        img_bytes = img_file.read()
                    
                    b64 = base64.b64encode(img_bytes).decode()
                    href = f'<a href="data:image/jpeg;base64,{b64}" download="converted_markdown.jpg">Download JPG</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    
                    # Clean up
                    if os.path.exists(temp_html):
                        os.remove(temp_html)
                    if os.path.exists(img_path):
                        os.remove(img_path)
                        
                except Exception as e:
                    st.error(f"Error exporting to JPG: {e}")
                    st.info("Make sure html2image is installed and a browser is available.")
    else:
        st.warning("Please enter some text to convert.")
        
    # Footer
    st.markdown("""
    <hr>
    <div style="text-align: center; color: #666; font-size: 0.8em;">
        LaTeX to Markdown Converter | Made with Streamlit
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()