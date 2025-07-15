#!/usr/bin/env python3
"""
BMasterAI Gradio UI Example with Anthropic API Integration
Similar to AWS AI-on-EKS gradio-app-llama.py but using Anthropic Claude models
"""

import os
import json
import logging
import gradio as gr
import requests
from typing import Dict, List, Any, Optional
import asyncio
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BMasterAIConfig:
    """Configuration class for BMasterAI framework"""
    anthropic_api_key: str
    model_name: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: str = "You are a helpful AI assistant powered by BMasterAI framework."
    enable_streaming: bool = True
    timeout: int = 30

class BMasterAIFramework:
    """
    BMasterAI Framework - AI inference framework with Anthropic API integration
    """
    
    def __init__(self, config: BMasterAIConfig):
        self.config = config
        self.anthropic_base_url = "https://api.anthropic.com/v1/messages"
        self.session_history: List[Dict[str, Any]] = []
        
        # Validate API key
        if not self.config.anthropic_api_key:
            raise ValueError("Anthropic API key is required")
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers for Anthropic API request"""
        return {
            "Content-Type": "application/json",
            "x-api-key": self.config.anthropic_api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def _prepare_messages(self, user_input: str, chat_history: List[List[str]]) -> List[Dict[str, str]]:
        """Prepare messages for the API call"""
        messages = []
        
        # Add chat history
        for user_msg, assistant_msg in chat_history:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if assistant_msg:
                messages.append({"role": "assistant", "content": assistant_msg})
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def _prepare_payload(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Prepare the complete payload for Anthropic API"""
        return {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "system": self.config.system_prompt,
            "messages": messages,
            "stream": False  # Set to False for simpler implementation
        }
    
    def generate_response(self, user_input: str, chat_history: List[List[str]] = None) -> str:
        """
        Generate response using Anthropic API
        """
        try:
            if chat_history is None:
                chat_history = []
            
            # Prepare request
            headers = self._prepare_headers()
            messages = self._prepare_messages(user_input, chat_history)
            payload = self._prepare_payload(messages)
            
            logger.info(f"Sending request to Anthropic API with model: {self.config.model_name}")
            
            # Make API call
            response = requests.post(
                self.anthropic_base_url,
                headers=headers,
                json=payload,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_response = result["content"][0]["text"]
                
                # Update session history
                self.session_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "user_input": user_input,
                    "assistant_response": assistant_response,
                    "model": self.config.model_name
                })
                
                return assistant_response
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return f"Error: {error_msg}"
                
        except requests.exceptions.Timeout:
            error_msg = "Request timeout - please try again"
            logger.error(error_msg)
            return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            "total_interactions": len(self.session_history),
            "model": self.config.model_name,
            "last_interaction": self.session_history[-1]["timestamp"] if self.session_history else None
        }

class BMasterAIGradioApp:
    """
    BMasterAI Gradio Application
    """
    
    def __init__(self):
        # Initialize configuration
        self.config = BMasterAIConfig(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model_name=os.getenv("MODEL_NAME", "claude-3-5-sonnet-20241022"),
            max_tokens=int(os.getenv("MAX_TOKENS", "4096")),
            temperature=float(os.getenv("TEMPERATURE", "0.7")),
            system_prompt=os.getenv("SYSTEM_PROMPT", "You are a helpful AI assistant powered by BMasterAI framework."),
        )
        
        # Initialize BMasterAI framework
        try:
            self.bmasterai = BMasterAIFramework(self.config)
            self.framework_status = "✅ BMasterAI Framework Initialized"
        except Exception as e:
            logger.error(f"Failed to initialize BMasterAI: {e}")
            self.framework_status = f"❌ Framework Error: {e}"
            self.bmasterai = None
    
    def chat_interface(self, message: str, history: List[List[str]]) -> List[List[str]]:
        """
        Chat interface function for Gradio ChatInterface
        """
        if not self.bmasterai:
            history.append([message, "Error: BMasterAI framework not initialized. Please check your API key."])
            return history
        
        if not message.strip():
            history.append([message, "Please enter a message."])
            return history
        
        try:
            # Generate response using BMasterAI
            response = self.bmasterai.generate_response(message, history)
            history.append([message, response])
            return history
        except Exception as e:
            error_response = f"Error generating response: {str(e)}"
            logger.error(error_response)
            history.append([message, error_response])
            return history
    
    def get_model_info(self) -> str:
        """Get current model information"""
        if not self.bmasterai:
            return "BMasterAI framework not initialized"
        
        stats = self.bmasterai.get_session_stats()
        return f"""
        **BMasterAI Framework Status:** {self.framework_status}
        **Model:** {self.config.model_name}
        **Max Tokens:** {self.config.max_tokens}
        **Temperature:** {self.config.temperature}
        **Total Interactions:** {stats['total_interactions']}
        **Last Interaction:** {stats.get('last_interaction', 'None')}
        """
    
    def update_model_settings(self, model_name: str, max_tokens: int, temperature: float, system_prompt: str):
        """Update model settings"""
        try:
            self.config.model_name = model_name
            self.config.max_tokens = max_tokens
            self.config.temperature = temperature
            self.config.system_prompt = system_prompt
            
            # Reinitialize framework with new settings
            if self.bmasterai:
                self.bmasterai.config = self.config
            
            return f"✅ Settings updated successfully!\nModel: {model_name}"
        except Exception as e:
            return f"❌ Error updating settings: {str(e)}"
    
    def clear_session(self):
        """Clear session history"""
        if self.bmasterai:
            self.bmasterai.session_history = []
        return "Session cleared successfully!"
    
    def create_interface(self) -> gr.Blocks:
        """
        Create the Gradio interface
        """
        
        # Custom CSS for better styling
        custom_css = """
        .gradio-container {
            max-width: 1200px;
            margin: auto;
        }
        .header-text {
            text-align: center;
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .status-box {
            background-color: #f0f0f0;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        """
        
        with gr.Blocks(css=custom_css, title="BMasterAI Chat Interface") as demo:
            
            # Header
            gr.HTML("""
            <div class="header-text">
                🚀 BMasterAI Framework - Anthropic Claude Integration
            </div>
            <div style="text-align: center; margin-bottom: 20px;">
                <p>Advanced AI inference framework with Anthropic Claude models</p>
            </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=3):
                    # Main chat interface
                    chatbot = gr.Chatbot(
                        label="BMasterAI Chat",
                        height=500,
                        show_label=True,
                        elem_id="chatbot"
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="Your Message",
                            placeholder="Enter your message here...",
                            lines=2,
                            scale=4
                        )
                        submit_btn = gr.Button("Send", variant="primary", scale=1)
                    
                    with gr.Row():
                        clear_btn = gr.Button("Clear Chat", variant="secondary")
                        session_clear_btn = gr.Button("Clear Session", variant="secondary")
                
                with gr.Column(scale=1):
                    # Model information and settings
                    gr.HTML("<h3>🔧 Model Settings</h3>")
                    
                    model_info = gr.Markdown(
                        value=self.get_model_info(),
                        label="Current Configuration"
                    )
                    
                    refresh_info_btn = gr.Button("Refresh Info", variant="secondary")
                    
                    # Model settings
                    with gr.Accordion("Advanced Settings", open=False):
                        model_dropdown = gr.Dropdown(
                            choices=[
                                "claude-3-5-sonnet-20241022",
                                "claude-3-5-haiku-20241022", 
                                "claude-3-opus-20240229",
                                "claude-3-sonnet-20240229",
                                "claude-3-haiku-20240307"
                            ],
                            value=self.config.model_name,
                            label="Model"
                        )
                        
                        max_tokens_slider = gr.Slider(
                            minimum=100,
                            maximum=8192,
                            value=self.config.max_tokens,
                            step=100,
                            label="Max Tokens"
                        )
                        
                        temperature_slider = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=self.config.temperature,
                            step=0.1,
                            label="Temperature"
                        )
                        
                        system_prompt_box = gr.Textbox(
                            value=self.config.system_prompt,
                            label="System Prompt",
                            lines=3
                        )
                        
                        update_settings_btn = gr.Button("Update Settings", variant="primary")
                        settings_status = gr.Textbox(label="Settings Status", interactive=False)
            
            # Event handlers
            def chat_fn(message, history):
                return self.chat_interface(message, history)
            
            def submit_message(message, history):
                if message.strip():
                    updated_history = chat_fn(message, history)
                    return "", updated_history
                return message, history
            
            # Wire up the interface
            submit_btn.click(
                submit_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            
            msg.submit(
                submit_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot]
            )
            
            clear_btn.click(
                lambda: ([], ""),
                outputs=[chatbot, msg]
            )
            
            session_clear_btn.click(
                lambda: [[], "", self.clear_session()],
                outputs=[chatbot, msg, settings_status]
            )
            
            refresh_info_btn.click(
                self.get_model_info,
                outputs=[model_info]
            )
            
            update_settings_btn.click(
                self.update_model_settings,
                inputs=[model_dropdown, max_tokens_slider, temperature_slider, system_prompt_box],
                outputs=[settings_status]
            )
            
            # Auto-refresh model info when settings change
            update_settings_btn.click(
                self.get_model_info,
                outputs=[model_info]
            )
        
        return demo

def main():
    """
    Main function to launch the BMasterAI Gradio application
    """
    # Environment setup instructions
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY environment variable not set!")
        print("\n" + "="*60)
        print("🔑 SETUP REQUIRED:")
        print("Please set your Anthropic API key as an environment variable:")
        print("export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nOr create a .env file with:")
        print("ANTHROPIC_API_KEY=your-api-key-here")
        print("="*60 + "\n")
    
    # Create and launch the application
    app = BMasterAIGradioApp()
    demo = app.create_interface()
    
    # Launch configuration
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    share = os.getenv("GRADIO_SHARE", "false").lower() == "true"
    
    logger.info(f"Launching BMasterAI Gradio app on {server_name}:{server_port}")
    
    demo.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        show_error=True,
        debug=False
    )

if __name__ == "__main__":
    main()
