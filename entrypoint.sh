#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Run the database initialization at RUNTIME
echo "Initializing database..."
python -c "from src.utils.database import init_database; init_database()"

# Execute the command passed to the docker container (the CMD)
exec "$@"