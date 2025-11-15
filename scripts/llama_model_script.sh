#!/bin/bash

# LLaMA Manager Quick Action - Fish Shell Compatible
MODELS_DIR="$HOME/active_projects/LEGAL/ohio_code/llm_model/"

# Auto-detect llama-server location
if command -v llama-server &> /dev/null; then
    LLAMA_SERVER="llama-server"
elif [ -f "$HOME/llama.cpp/build/bin/llama-server" ]; then
    LLAMA_SERVER="$HOME/llama.cpp/build/bin/llama-server"
elif [ -f "$HOME/llama.cpp/llama-server" ]; then
    LLAMA_SERVER="$HOME/llama.cpp/llama-server"
elif [ -f "/usr/local/bin/llama-server" ]; then
    LLAMA_SERVER="/usr/local/bin/llama-server"
else
    osascript -e 'display alert "llama-server not found" message "Please set LLAMA_SERVER path in the script or add llama-server to PATH"'
    exit 1
fi

# Create models directory
mkdir -p "$MODELS_DIR"

# Function to show dialog
show_dialog() {
    osascript -e 'choose from list {"Setup Models", "List Models", "Test Model", "Chat with Model", "Download Mistral", "Run Enricher", "Start Server"} with prompt "LLaMA.cpp Manager:" default items {"Chat with Model"}'
}

# Function to select model from available models
select_model() {
    # Get list of models
    models=($(ls "$MODELS_DIR"/*.gguf 2>/dev/null))

    if [ ${#models[@]} -eq 0 ]; then
        osascript -e 'display alert "No models found" message "Please download a model first using Setup Models"'
        exit 1
    fi

    # Create model names for display
    model_names=""
    for model in "${models[@]}"; do
        basename_model=$(basename "$model")
        if [ -z "$model_names" ]; then
            model_names="\"$basename_model\""
        else
            model_names="$model_names, \"$basename_model\""
        fi
    done

    # Show selection dialog
    selected=$(osascript -e "choose from list {$model_names} with prompt \"Select a model:\" default items {\"$(basename "${models[0]}")\"}")

    if [ "$selected" != "false" ]; then
        echo "$MODELS_DIR/$selected"
    else
        exit 1
    fi
}

# Get user choice
CHOICE=$(show_dialog)

case "$CHOICE" in
    "Setup Models")
        osascript -e 'display notification "Starting download..." with title "LLaMA Manager"'

        # Show download in Terminal for progress - Fish shell compatible
        osascript -e "tell application \"Terminal\"
            activate
            do script \"bash -c 'echo \\\"Downloading DeepSeek Coder model...\\\" && \\
                echo \\\"This will take a few minutes (4.1 GB file)...\\\" && \\
                echo \\\"\\\" && \\
                curl -L --progress-bar \\
                    --create-dirs \\
                    -o \\\"$MODELS_DIR/deepseek-coder-7b-instruct.Q4_K_M.gguf\\\" \\
                    \\\"https://huggingface.co/TheBloke/deepseek-coder-7B-instruct-v1.5-GGUF/resolve/main/deepseek-coder-7b-instruct-v1.5.Q4_K_M.gguf\\\" && \\
                echo \\\"\\\" && \\
                echo \\\"✅ Download complete!\\\" && \\
                echo \\\"Model saved to: $MODELS_DIR\\\" && \\
                ls -lh \\\"$MODELS_DIR\\\"/*.gguf; exec bash'\"
        end tell"
        ;;

    "Download Mistral")
        osascript -e 'display notification "Starting Mistral download..." with title "LLaMA Manager"'

        # Show download in Terminal for progress - Fish shell compatible
        osascript -e "tell application \"Terminal\"
            activate
            do script \"bash -c 'echo \\\"Downloading Mistral 7B Instruct model...\\\" && \\
                echo \\\"This will take a few minutes (4.1 GB file)...\\\" && \\
                echo \\\"\\\" && \\
                curl -L --progress-bar \\
                    --create-dirs \\
                    -o \\\"$MODELS_DIR/mistral-7b-instruct-v0.2.Q4_K_M.gguf\\\" \\
                    \\\"https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf\\\" && \\
                echo \\\"\\\" && \\
                echo \\\"✅ Download complete!\\\" && \\
                echo \\\"Model saved to: $MODELS_DIR\\\" && \\
                ls -lh \\\"$MODELS_DIR\\\"/*.gguf; exec bash'\"
        end tell"
        ;;

    "List Models")
        models=$(ls -la "$MODELS_DIR"/*.gguf 2>/dev/null | awk '{print $9 " (" $5 " bytes)"}')
        if [ -z "$models" ]; then
            osascript -e 'display alert "No Models Found" message "No GGUF models found in ~/models directory"'
        else
            osascript -e "display dialog \"Models in $MODELS_DIR:\n\n$models\" buttons {\"OK\"} default button \"OK\""
        fi
        ;;

    "Test Model")
        MODEL=$(select_model)
        if [ -n "$MODEL" ]; then
            osascript -e "tell application \"Terminal\"
                activate
                do script \"bash -c 'echo \\\"Testing model: $(basename "$MODEL")\\\" && llama-cli -m \\\"$MODEL\\\" -p \\\"Hello, how are you today?\\\" -n 50; exec bash'\"
            end tell"
        fi
        ;;

    "Chat with Model")
        MODEL=$(select_model)
        if [ -n "$MODEL" ]; then
            # Check which command is available
            if command -v llama-cli &> /dev/null; then
                CMD="llama-cli"
            elif command -v llama &> /dev/null; then
                CMD="llama"
            elif command -v ./llama &> /dev/null; then
                CMD="./llama"
            else
                osascript -e 'display alert "LLaMA not found" message "Please install llama.cpp first"'
                exit 1
            fi

            osascript -e "tell application \"Terminal\"
                activate
                do script \"bash -c '$CMD -m \\\"$MODEL\\\" --interactive --color --ctx-size 4096 --temp 0.7 --repeat-penalty 1.1 --n-predict -1 --interactive-first; exec bash'\"
            end tell"
        fi
        ;;

    "Run Enricher")
        MODEL=$(select_model)
        if [ -n "$MODEL" ]; then
            # Prompt for input file
            INPUT_FILE=$(osascript -e 'set theFile to choose file with prompt "Select JSONL input file:" of type {"jsonl", "json"}
            POSIX path of theFile')

            if [ -n "$INPUT_FILE" ]; then
                osascript -e "tell application \"Terminal\"
                    activate
                    do script \"bash -c 'cd \\\"$(dirname "$INPUT_FILE")\\\" && python3 \\\"$HOME/robust_enricher.py\\\" \\\"$MODEL\\\" \\\"$INPUT_FILE\\\"; exec bash'\"
                end tell"
            fi
        fi
        ;;

    "Start Server")
        MODEL=$(select_model)
        if [ -n "$MODEL" ]; then
            PORT=$(osascript -e 'text returned of (display dialog "Server port:" default answer "8004")')
            PORT=${PORT:-8004}

            osascript -e "tell application \"Terminal\"
                activate
                do script \"bash -c '\\\"$LLAMA_SERVER\\\" -m \\\"$MODEL\\\" --host 0.0.0.0 --port $PORT --ctx-size 4096 -ngl 35 --parallel 4; exec bash'\"
            end tell"

            # Wait a moment then open browser
            sleep 2
            open "http://localhost:$PORT"
        fi
        ;;

    *)
        exit 0
        ;;
esac