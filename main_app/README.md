#### Description
main service interact with front-end

#### Tasks
- View documents:
    - show processing status of documents
    - load PDF from Object storage
- Docs processing:
    - recieve **scan** request
    - add task to **RabbitMQ**
    - add request document to Object storage
    - return response to frontend immediately
