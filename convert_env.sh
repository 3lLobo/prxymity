#!/bin/bash

# Input and output file
INPUT_FILE=".env"
OUTPUT_FILE=".env.example"

# Check if the input file exists
if [ ! -f "$INPUT_FILE" ]; then
  echo "Error: $INPUT_FILE does not exist."
  exit 1
fi

# Generate the .env.example
echo "Generating $OUTPUT_FILE from $INPUT_FILE..."

# Process each line
> "$OUTPUT_FILE"  # Clear output file if exists
while IFS= read -r line; do
  if [[ "$line" =~ ^[[:space:]]*#.*$ || "$line" =~ ^[[:space:]]*$ ]]; then
    # Copy comment or empty line as-is
    echo "$line" >> "$OUTPUT_FILE"
  elif [[ "$line" =~ ^[[:space:]]*([^=[:space:]]+)=.*$ ]]; then
    # Replace value with empty string
    key="${BASH_REMATCH[1]}"
    echo "${key}=" >> "$OUTPUT_FILE"
  else
    # Copy anything else as-is
    echo "$line" >> "$OUTPUT_FILE"
  fi
done < "$INPUT_FILE"

echo "$OUTPUT_FILE created successfully."

