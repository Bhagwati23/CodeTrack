#!/usr/bin/env python3
"""
Generate secure keys for Railway deployment
Run this script to generate secure environment variables
"""

import secrets
import string

def generate_key(length=32):
    """Generate a secure random key"""
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))

def main():
    print("🔐 CodeTrack Pro - Secure Key Generator")
    print("=" * 50)
    print()
    
    print("Copy these environment variables to your Railway project:")
    print()
    
    print(f"FLASK_SECRET_KEY={generate_key(32)}")
    print(f"SESSION_SECRET={generate_key(32)}")
    print()
    
    print("Optional AI API Keys (add if you have them):")
    print("OPENAI_API_KEY=your-openai-key")
    print("DEEPSEEK_API_KEY=your-deepseek-key")
    print("GEMINI_API_KEY=your-gemini-key")
    print("OPENROUTER_API_KEY=your-openrouter-key")
    print("HUGGINGFACE_API_KEY=your-huggingface-key")
    print()
    
    print("Optional Email Configuration:")
    print("SENDGRID_API_KEY=your-sendgrid-key")
    print()
    
    print("✅ Keys generated successfully!")
    print("💡 Paste these into Railway Variables tab")

if __name__ == "__main__":
    main()
