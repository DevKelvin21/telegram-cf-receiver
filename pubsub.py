from google.cloud import pubsub_v1
import json
import logging

# Configure logging for PubSub operations
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

class PubSubPublisher:
    def __init__(self, project_id: str, topic_name: str):
        self.project_id = project_id
        self.topic_name = topic_name
        logger.info(f"Initializing PubSubPublisher for project: {project_id}, topic: {topic_name}")
        try:
            self.publisher = pubsub_v1.PublisherClient()
            self.topic_path = self.publisher.topic_path(self.project_id, self.topic_name)
            logger.info(f"PubSubPublisher initialized successfully. Topic path: {self.topic_path}")
        except Exception as e:
            logger.error(f"Failed to initialize PubSubPublisher: {str(e)}")
            raise

    def publish(self, data: dict):
        """Publish a message to the Pub/Sub topic."""
        try:
            logger.info(f"Publishing message to topic {self.topic_name}: {data.get('message_id', 'unknown_id')}")
            message_json = json.dumps(data).encode('utf-8')
            future = self.publisher.publish(self.topic_path, message_json)
            result = future.result()  # Wait for the publish to complete
            logger.info(f"Message published successfully. Message ID: {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to publish message to {self.topic_name}: {str(e)}")
            logger.error(f"Message data: {data}")
            raise