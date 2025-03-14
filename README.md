# 🔒 Terraform Security Enhancer

A Streamlit application that analyzes and enhances the security of Terraform configurations using AI.

## Overview

Terraform Security Enhancer is a tool designed to help DevOps engineers and cloud architects improve the security posture of their infrastructure-as-code. It uses OpenAI's GPT-4o model to analyze Terraform files, identify security vulnerabilities, and suggest improvements to enhance security.

## Features

- **GitHub Repository Integration**: Clone and analyze Terraform repositories directly from GitHub
- **Local Repository Support**: Analyze Terraform files from local directories
- **Module Resolution**: Automatically resolves and analyzes Terraform modules
- **Security Enhancement**: Uses AI to suggest security improvements
- **Diff Visualization**: View original and enhanced code side-by-side with highlighted differences
- **Example Selection**: Choose from available examples in the repository

## Installation

### Prerequisites

- Python 3.7+
- Git
- OpenAI API key

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/terraform-security-enhancer.git
   cd terraform-security-enhancer
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

1. Start the Streamlit application:
   ```bash
   streamlit run app.py
   ```

2. In the web interface:
   - Enter a GitHub repository URL or a local Terraform repository path
   - Select a Terraform example from the dropdown
   - Enter a security enhancement prompt (or use the default)
   - Click "Enhance Security" to begin the analysis

3. Review the enhanced code:
   - View updated code in the "Updated Code" tab
   - Compare with original code in the "Original Code" tab
   - See highlighted differences in the "Differences" tab

## How It Works

1. The application analyzes the structure of your Terraform code, including modules and their dependencies
2. It sends the Terraform files to OpenAI's API with your security enhancement prompt
3. The AI generates improved versions of your files with enhanced security features
4. The application displays the original and improved code side-by-side with differences highlighted

## Example Prompts

- "Update the VPC by adding security groups with strict ingress/egress rules, enable VPC flow logs, and implement network ACLs for better security."
- "Add encryption for all S3 buckets, implement least privilege IAM policies, and enable CloudTrail logging."
- "Implement security headers for all ALBs, add WAF protection, and implement secure TLS configurations."

## Requirements

The following Python packages are required:
- streamlit
- openai
- python-dotenv
- pathlib

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.