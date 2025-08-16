from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import os
import json

app = Flask(__name__)

# A simple lock to prevent concurrent hashkit operations.
lock = threading.Lock()

def run_hashkit_command(args):
    """
    Runs the hashkit command as a subprocess and captures its output.
    """
    try:
        # Get a copy of the current environment variables
        env = os.environ.copy()
        # Set the environment variable to ensure UTF-8 encoding for the subprocess
        env['PYTHONIOENCODING'] = 'utf-8'

        # The first argument must be the executable name, which is `hashkit`.
        command = ['hashkit'] + args
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8', # This handles decoding the output
            env=env # This ensures the subprocess itself uses UTF-8 for its output
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr.strip()}"
    except FileNotFoundError:
        return "Error: `hashkit` executable not found. Make sure it's installed correctly."

@app.route('/')
def index():
    """Renders the main page with the hashkit web interface."""
    return render_template('index.html')

@app.route('/api/process', methods=['POST'])
def process():
    """Handles the main form submission for identification and cracking."""
    with lock:
        try:
            data = request.json
            hash_value = data.get('hash_value')
            action = data.get('action')
            threads = data.get('threads')

            if not hash_value and action != 'identify':
                return jsonify({"status": "error", "message": "Please provide a hash value."}), 400

            results = ""
            
            if action == 'identify':
                # Build command for identify action
                command_args = ['identify', hash_value]
                results = run_hashkit_command(command_args)
            elif action == 'crack':
                mode = data.get('mode')
                # Corrected: Use '--threads' instead of '-t' for the thread count flag
                threads_arg = ['--threads', str(threads)] if threads else []
                
                # Handle different attack modes by building command arguments.
                if mode == 'dictionary':
                    wordlist_text = data.get('wordlist_text', '').strip()
                    temp_wordlist_path = 'temp_wordlist.txt'
                    if not wordlist_text:
                        wordlist_text = "password\n123456\nqwerty\nadmin"
                    with open(temp_wordlist_path, 'w') as f:
                        f.write(wordlist_text)
                    
                    command_args = ['crack', hash_value, '-w', temp_wordlist_path] + threads_arg
                    results = run_hashkit_command(command_args)
                    # Clean up the temporary file
                    if os.path.exists(temp_wordlist_path):
                        os.remove(temp_wordlist_path)

                elif mode == 'bruteforce':
                    max_length = data.get('max_length', 6)
                    command_args = ['crack', hash_value, '-m', 'bruteforce', '--max-length', str(max_length)] + threads_arg
                    results = run_hashkit_command(command_args)
                elif mode == 'mask':
                    mask = data.get('mask', '')
                    if not mask:
                        return jsonify({"status": "error", "message": "Mask pattern is required for mask attack."}), 400
                    command_args = ['crack', hash_value, '-m', 'mask', '--mask', mask] + threads_arg
                    results = run_hashkit_command(command_args)
                else:
                    return jsonify({"status": "error", "message": "Invalid cracking mode."}), 400
            else:
                return jsonify({"status": "error", "message": "Invalid action."}), 400

            return jsonify({"status": "success", "results": results})

        except Exception as e:
            # General error handling
            return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500

@app.route('/api/wordlist', methods=['POST'])
def wordlist_management():
    """Handles wordlist management actions."""
    with lock:
        try:
            data = request.json
            action = data.get('action')
            
            results = ""
            
            if action == 'list':
                results = run_hashkit_command(['wordlist', 'list'])
            elif action == 'download':
                results = run_hashkit_command(['wordlist', 'download', 'rockyou'])
            elif action == 'clear':
                results = run_hashkit_command(['wordlist', 'clear'])
            else:
                return jsonify({"status": "error", "message": "Invalid wordlist action."}), 400

            return jsonify({"status": "success", "results": results})
        
        except Exception as e:
            return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)