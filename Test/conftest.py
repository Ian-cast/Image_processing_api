import os

# Use a dedicated database for tests unless the environment already picks one
# (the CI workflow sets DB_NAME for its throwaway MySQL service).
os.environ.setdefault("DB_NAME", "image_api_test")