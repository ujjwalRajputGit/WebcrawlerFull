# Web Crawler

A distributed web crawler system designed to extract product URLs from e-commerce websites.

## Architecture

The system consists of two main components:

- **API Server**: FastAPI application that handles HTTP requests and initiates crawling tasks
- **Worker**: Celery worker that performs the actual web crawling asynchronously

### Technology Stack

- **FastAPI**: Web framework for the API
- **Celery**: Distributed task queue
- **Redis**: Message broker and result backend for Celery
- **MongoDB**: Storage for crawled URLs and metadata
- **Python 3.9+**: Core programming language

## Installation

### Prerequisites

- Python 3.9+
- Redis
- MongoDB
- Docker (optional, for containerized deployment)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/web-crawler.git
   cd web-crawler
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   Create a `.env` file based on the sample provided:
   ```
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_USERNAME=default
   REDIS_PASSWORD=your_redis_password
   
   MONGO_URI=mongodb://localhost:27017
   MONGO_DB=webcrawler
   
   ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```

## Running the Application

### Development Mode

1. Start the API server:
   ```bash
   cd server
   uvicorn src.main:app --reload
   ```

2. Start the Celery worker:
   ```bash
   cd worker
   celery -A src.tasks worker --loglevel=info
   ```

### Using Docker Compose

```bash
docker-compose up -d
```

## API Documentation

Once the server is running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Main Endpoints

- `GET /`: Root endpoint, shows API status
- `GET /health`: Health check endpoint for monitoring
- `POST /crawl`: Start a crawling task for specified domains

## Configuration

The application can be configured through environment variables or the `.env` file:

### Redis Configuration
- `REDIS_HOST`: Redis server hostname (default: "localhost")
- `REDIS_PORT`: Redis server port (default: 6379)
- `REDIS_USERNAME`: Redis username (default: "default")
- `REDIS_PASSWORD`: Redis password 

### MongoDB Configuration
- `MONGO_URI`: MongoDB connection string (default: "mongodb://localhost:27017")
- `MONGO_DB`: MongoDB database name (default: "webcrawler")

### API Configuration
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

### Logging Configuration
- `LOG_TO_FILE`: Whether to log to file (default: true)
- `LOG_LEVEL_CONSOLE`: Console log level (default: "INFO")
- `LOG_LEVEL_FILE`: File log level (default: "DEBUG")

### Crawler Configuration
- `DEFAULT_MAX_CRAWL_DEPTH`: Default maximum crawl depth (default: 3)

## Project Structure

## License

[MIT License](LICENSE)
