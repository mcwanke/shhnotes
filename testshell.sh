#!/bin/bash

echo "Running ShhNotes"
echo ""

while true; do
    echo "1) Start recording"
    echo "2) Stop recording"
    echo "3) Show status"
    echo "4) Display output"
    echo "5) Exit"
    echo ""
    read -p "Choose an option: " choice

    case $choice in
        1)
            read -p "Enter session label (default: test): " label
            label=${label:-test}
            shhnotes start --label "$label"
            ;;
        2)
            shhnotes stop
            ;;
        3)
            shhnotes status
            ;;
        4)
            echo ""
            echo "=== Transcripts ==="
            TRANSCRIPT_DIR=~/Documents/shhnotes/transcripts
            if [ -d "$TRANSCRIPT_DIR" ]; then
                ls -lh "$TRANSCRIPT_DIR"
                echo ""
                # Display the latest transcript
                LATEST=$(ls -t "$TRANSCRIPT_DIR"/*.md 2>/dev/null | head -1)
                if [ -n "$LATEST" ]; then
                    echo "--- Latest Transcript ---"
                    cat "$LATEST"
                fi
            else
                echo "No transcripts directory found"
            fi
            echo ""
            ;;
        5)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
    echo ""
done
