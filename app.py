import os
import re
import streamlit as st
from openai import OpenAI
from pathlib import Path
import json
from dotenv import load_dotenv
import difflib
import html
import subprocess
import shutil
import tempfile

load_dotenv()

st.set_page_config(
    page_title="Terraform Security Enhancer",
    page_icon="🔒",
    layout="wide"
)

def get_openai_client():
    api_key = st.session_state.get("openai_api_key", os.getenv("OPENAI_API_KEY"))
    if not api_key:
        return None
    return OpenAI(api_key=api_key)

def find_terraform_files(directory):
    terraform_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".tf"):
                terraform_files.append(os.path.join(root, file))
    return terraform_files

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        return file.read()

def extract_module_references(file_content):
    module_references = []
    module_pattern = r'module\s+"([^"]+)"\s+{[^}]*source\s+=\s+"([^"]+)"'
    matches = re.finditer(module_pattern, file_content, re.DOTALL)
    
    for match in matches:
        module_name = match.group(1)
        source_path = match.group(2)
        module_references.append({"name": module_name, "source": source_path})
    
    return module_references

def resolve_module_paths(base_file, module_references, repo_dir):
    resolved_paths = []
    base_dir = os.path.dirname(base_file)
    
    for module_ref in module_references:
        source_path = module_ref["source"]
        
        if source_path.startswith("./") or source_path.startswith("../"):
            abs_path = os.path.normpath(os.path.join(base_dir, source_path))
            if os.path.exists(abs_path):
                resolved_paths.append(abs_path)
        elif source_path == "../../":
            abs_path = os.path.normpath(os.path.join(repo_dir))
            if os.path.exists(abs_path):
                resolved_paths.append(abs_path)
        elif not source_path.startswith("github.com") and not source_path.startswith("git::"):
            abs_path = os.path.normpath(os.path.join(repo_dir, source_path))
            if os.path.exists(abs_path):
                resolved_paths.append(abs_path)
    
    return resolved_paths

def analyze_terraform_files(repo_dir, example_path):
    example_full_path = os.path.join(repo_dir, example_path)
    
    tf_files = find_terraform_files(example_full_path)
    
    file_contents = {}
    module_references = []
    
    for tf_file in tf_files:
        content = read_file(tf_file)
        file_contents[tf_file] = content
        
        refs = extract_module_references(content)
        for ref in refs:
            module_references.append({"file": tf_file, "reference": ref})
    
    resolved_modules = set()
    for module_ref in module_references:
        source_file = module_ref["file"]
        source_path = module_ref["reference"]["source"]
        
        module_paths = resolve_module_paths(source_file, [module_ref["reference"]], repo_dir)
        
        for module_path in module_paths:
            if os.path.isdir(module_path):
                module_tf_files = find_terraform_files(module_path)
                for module_file in module_tf_files:
                    if module_file not in file_contents:
                        module_content = read_file(module_file)
                        file_contents[module_file] = module_content
                        resolved_modules.add(module_file)
    
    return file_contents, resolved_modules

def enhance_security(file_contents, prompt, client):
    context = "I have the following Terraform files that define AWS infrastructure:\n\n"
    
    for file_path, content in file_contents.items():
        file_name = os.path.basename(file_path)
        context += f"File: {file_name}\n```hcl\n{content}\n```\n\n"
    
    full_prompt = f"{context}\n{prompt}\n\nPlease update the Terraform code to enhance security. Return only the modified files in the following format:\n\nFILE: <filename>\n```hcl\n<updated content>\n```\n\nFILE: <another filename>\n```hcl\n<updated content>\n```"
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a Terraform and AWS security expert. Your task is to enhance the security of Terraform configurations."},
                {"role": "user", "content": full_prompt}
            ],
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def parse_openai_response(response):
    file_pattern = r'FILE: ([^\n]+)\n```(?:hcl|terraform)?\n(.*?)\n```'
    matches = re.finditer(file_pattern, response, re.DOTALL)
    
    updated_files = {}
    for match in matches:
        file_name = match.group(1).strip()
        content = match.group(2).strip()
        updated_files[file_name] = content
    
    return updated_files

def generate_diff_html(original, updated):
    diff = difflib.HtmlDiff()
    diff_html = diff.make_file(original.splitlines(), updated.splitlines(), 
                              "Original", "Updated", context=True)
    return diff_html

def find_original_file(file_name, file_contents):
    for path in file_contents:
        if os.path.basename(path) == file_name:
            return path
    return None

def clone_github_repo(repo_url, target_dir):
    try:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        
        os.makedirs(target_dir, exist_ok=True)
        
        result = subprocess.run(
            ["git", "clone", repo_url, target_dir],
            capture_output=True,
            text=True,
            check=True
        )
        return True, "Repository cloned successfully!"
    except subprocess.CalledProcessError as e:
        return False, f"Error cloning repository: {e.stderr}"
    except Exception as e:
        return False, f"An error occurred: {str(e)}"

def list_directories(path):
    try:
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
    except Exception as e:
        return []

def main():
    st.title("🔒 Terraform Security Enhancer")
    
    with st.sidebar:
        st.header("Configuration")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            st.success("OpenAI API Key loaded from environment variables")
        else:
            st.error("OpenAI API Key not found in environment variables")
        
        st.markdown("---")
        st.markdown("### How to use")
        st.markdown("""
        1. Enter a GitHub repository URL or provide a local Terraform repository path
        2. Select a Terraform example
        3. Enter your security enhancement prompt
        4. Click 'Enhance Security'
        """)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Input")
        
        github_url = st.text_input("GitHub Repository URL (Optional)", placeholder="https://github.com/username/terraform-repo")
        
        if github_url:
            clone_button = st.button("Clone Repository")
            if clone_button:
                with st.spinner("Cloning repository..."):
                    temp_dir = os.path.join(tempfile.gettempdir(), "terraform_repo")
                    success, message = clone_github_repo(github_url, temp_dir)
                    
                    if success:
                        st.success(message)
                        st.session_state["repo_path"] = temp_dir
                        st.subheader("Repository Structure:")
                        repo_dirs = list_directories(temp_dir)
                        if repo_dirs:
                            for dir_name in repo_dirs:
                                st.write(f"📁 {dir_name}")
                        else:
                            st.info("No directories found in the repository root.")
                    else:
                        st.error(message)
        
        repo_path = st.text_input(
            "Terraform Repository Path", 
            value=st.session_state.get("repo_path", "c:\\Users\\Subham\\Desktop\\amentities\\opsly\\terraform-aws-vpc")
        )
        
        examples = []
        if os.path.exists(os.path.join(repo_path, "examples")):
            examples = [d for d in os.listdir(os.path.join(repo_path, "examples")) if os.path.isdir(os.path.join(repo_path, "examples", d))]
        
        selected_example = st.selectbox("Select Example", options=examples)
        
        security_prompt = st.text_area("Security Enhancement Prompt", value="Update the VPC by adding security groups with strict ingress/egress rules, enable VPC flow logs, and implement network ACLs for better security.")
        
        enhance_button = st.button("Enhance Security")
        
        if enhance_button:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                st.error("OpenAI API Key not found in environment variables. Please add it to your .env file.")
            elif not selected_example:
                st.error("Please select a Terraform example.")
            else:
                with st.spinner("Analyzing Terraform files..."):
                    example_path = os.path.join("examples", selected_example)
                    
                    file_contents, resolved_modules = analyze_terraform_files(repo_path, example_path)
                    
                    st.session_state["file_contents"] = file_contents
                    st.session_state["resolved_modules"] = resolved_modules
                    
                    st.success(f"Found {len(file_contents)} Terraform files.")
                    
                    client = get_openai_client()
                    
                    if client:
                        with st.spinner("Enhancing security with OpenAI..."):
                            response = enhance_security(file_contents, security_prompt, client)
                            
                            updated_files = parse_openai_response(response)
                            
                            st.session_state["updated_files"] = updated_files
                            st.session_state["raw_response"] = response
                            
                            st.success(f"Security enhancements completed for {len(updated_files)} files.")
                    else:
                        st.error("Failed to initialize OpenAI client. Please check your API key in the .env file.")
    
    with col2:
        st.header("Output")
        
        if "updated_files" in st.session_state and st.session_state["updated_files"]:
            for file_name, updated_content in st.session_state["updated_files"].items():
                with st.expander(f"Updated: {file_name}"):
                    original_path = find_original_file(file_name, st.session_state["file_contents"])
                    
                    tab1, tab2, tab3 = st.tabs(["Updated Code", "Original Code", "Differences"])
                    
                    with tab1:
                        st.code(updated_content, language="hcl")
                    
                    with tab2:
                        if original_path:
                            original_content = st.session_state["file_contents"][original_path]
                            st.code(original_content, language="hcl")
                        else:
                            st.warning(f"Original file not found for {file_name}")
                    
                    with tab3:
                        if original_path:
                            original_content = st.session_state["file_contents"][original_path]
                            diff_html = generate_diff_html(original_content, updated_content)
                            st.components.v1.html(diff_html, height=500, scrolling=True)
                        else:
                            st.warning(f"Cannot generate diff: original file not found for {file_name}")
            
            with st.expander("Raw OpenAI Response"):
                st.text_area("", value=st.session_state.get("raw_response", ""), height=300)
        else:
            st.info("Enhanced Terraform files will appear here after processing.")

if __name__ == "__main__":
    main()
