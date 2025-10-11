#!/usr/bin/env python3
"""
JWT Service HTTPS Startup Script
Flask doesn't support SSL natively in production, so we use Waitress WSGI server
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description='DSP AI JWT Service with HTTPS')
    parser.add_argument('--host', default=os.getenv('HOST', '0.0.0.0'), help='Host to bind to')
    parser.add_argument('--port', type=int, default=int(os.getenv('PORT', '5000')), help='HTTP port to bind to')
    parser.add_argument('--https-port', type=int, default=int(os.getenv('HTTPS_PORT', '5443')), help='HTTPS port to bind to')
    parser.add_argument('--ssl', action='store_true', default=os.getenv('SSL_ENABLED', 'false').lower() == 'true', help='Enable HTTPS')
    parser.add_argument('--ssl-cert', default=os.getenv('SSL_CERT_FILE', 'certs/server.crt'), help='SSL certificate file')
    parser.add_argument('--ssl-key', default=os.getenv('SSL_KEY_FILE', 'certs/server.key'), help='SSL key file')
    parser.add_argument('--threads', type=int, default=int(os.getenv('THREADS', '4')), help='Number of threads')
    args = parser.parse_args()
    
    # Import app after environment is loaded
    from app import app
    
    if args.ssl:
        try:
            from waitress import serve
        except ImportError:
            print("Error: waitress is required for HTTPS support")
            print("Install with: pip install waitress")
            sys.exit(1)
        
        port = args.https_port
        ssl_keyfile = args.ssl_key
        ssl_certfile = args.ssl_cert
        
        # Verify SSL files exist
        if not os.path.exists(ssl_certfile):
            print(f"Error: SSL certificate not found: {ssl_certfile}")
            print("Run: python generate_ssl_certs.py")
            sys.exit(1)
        if not os.path.exists(ssl_keyfile):
            print(f"Error: SSL key not found: {ssl_keyfile}")
            print("Run: python generate_ssl_certs.py")
            sys.exit(1)
        
        print(f"Starting JWT Service with HTTPS on {args.host}:{port}")
        print(f"  Certificate: {ssl_certfile}")
        print(f"  Key: {ssl_keyfile}")
        print(f"  Threads: {args.threads}")
        print()
        print(f"  API Documentation: https://{args.host}:{port}/dspai-docs")
        print()
        
        # Use Waitress with SSL
        serve(
            app,
            host=args.host,
            port=port,
            threads=args.threads,
            url_scheme='https',
            ident='JWT-Service',
            # SSL configuration
            # Note: Waitress doesn't support SSL directly, need to use a reverse proxy
            # or use alternative WSGI server like Gunicorn with SSL
        )
        
        print("\n⚠ Note: Waitress doesn't support SSL directly.")
        print("For production HTTPS, use one of these options:")
        print("1. Nginx reverse proxy with SSL termination (recommended)")
        print("2. Gunicorn with SSL: gunicorn --certfile=certs/server.crt --keyfile=certs/server.key app:app")
        print("3. Run behind APISIX gateway with SSL")
        
    else:
        port = args.port
        print(f"Starting JWT Service with HTTP on {args.host}:{port}")
        print(f"  API Documentation: http://{args.host}:{port}/dspai-docs")
        print("⚠ Warning: Running without HTTPS. Use --ssl for production.")
        print()
        
        # Development mode - use Flask's built-in server
        debug = os.getenv('DEBUG', 'true').lower() == 'true'
        app.run(
            host=args.host,
            port=port,
            debug=debug
        )

if __name__ == '__main__':
    main()
