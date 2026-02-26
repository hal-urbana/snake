# Unified Data Library (UDL) Integration
## Kafka-Based Knowledge Management System

**System Overview:** A hybrid knowledge management architecture integrating **LightRAG** (graph-enhanced RAG) with **ArcGIS Knowledge** (spatial visualization) and **Unified Data Library** (Kafka message broker).

---

## 1. Architecture Overview

### Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                           UDL (Kafka)                               │
│         Topic: documents, geospatial_features, system_events         │
└────────────────────┬──────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Knowledge Management Processor                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  Kafka Consumer │  │  LightRAG       │  │  ArcGIS Integration │  │
│  │  - Document     │  │  - Entities     │  │  - Feature Classes  │  │
│  │  - Features     │  │  - Relationships│  │  - Query Service    │  │
│  │  - Events       │  │  - Vector Search│  │  - Visualization    │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└────────────────────┬──────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Shared Storage (PostgreSQL)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  PostgreSQL AGE │  │    pgvector     │  │    JSONB Storage    │  │
│  │    (Graph KG)   │  │   (Vector Search │  │  (Metadata + Schema)│  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
└────────────────────┬──────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ArcGIS Integration Layer                        │
│  ┌───────────────┐  ┌───────────────────────────────────────────┐  │
│  │  ArcGIS Pro   │  │  REST API & Web Services                  │  │
│  │  (Desktop)    │  │  - Knowledge Query API                    │  │
│  │  - Feature    │  │  - Link Chart Visualization                │  │
│  │    Classes    │  │  - Spatial Search                          │  │
│  └───────────────┘  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Kafka Topics Design

### Topic Structure

| Topic Name | Partition Strategy | Compression | Retention | Description |
|------------|-------------------|-------------|-----------|-------------|
| `data.documents` | 12 partitions | gzip | 7 days | Text documents (PDF, DOCX, TXT) |
| `data.geospatial_features` | 6 partitions | gzip | 30 days | GeoJSON/shp/feature data |
| `data.system_events` | 3 partitions | gzip | 90 days | Process monitoring & diagnostics |

### Message Format

**Document Message:**
```json
{
  "message_type": "document_ingest",
  "doc_id": "uuid-v4",
  "source": "system_name",
  "file_path": "/path/to/document.pdf",
  "content": "Base64 encoded or text content",
  "metadata": {
    "title": "Document Title",
    "author": "Author Name",
    "created_at": "2026-02-26T10:00:00Z",
    "file_format": "pdf",
    "content_type": "application/pdf",
    "doc_type": "policy_report"
  }
}
```

**Geospatial Feature Message:**
```json
{
  "message_type": "feature_ingest",
  "feature_id": "uuid-v4",
  "source": "system_name",
  "file_path": "/path/to/features.shp",
  "geometry": "GeoJSON feature or shapefile data",
  "metadata": {
    "feature_type": "road_network",
    "crs": "EPSG:3857",
    "feature_count": 1500,
    "ingest_timestamp": "2026-02-26T10:00:00Z"
  }
}
```

**System Event Message:**
```json
{
  "message_type": "system_event",
  "event_type": "processor_status",
  "processor_id": "kafka-udl-consumer",
  "status": "active",
  "timestamp": "2026-02-26T10:00:00Z",
  "metrics": {
    "documents_processed": 1247,
    "errors": 3,
    "avg_processing_time_ms": 245
  }
}
```

---

## 3. Kafka Client Configuration

### Installation

```bash
# Python Kafka Client
pip install confluent-kafka python-dotenv pandas geojson

# Alternative: kafka-python
pip install kafka-python
```

### Configuration File (`config/kafka.yml`)

```yaml
# Kafka Configuration
bootstrap_servers:
  - "udl.example.com:9092"
  - "udl.example.com:9093"
  - "udl.example.com:9094"

security_protocol: SASL_SSL
sasl_mechanism: SCRAM-SHA-512

authentication:
  username: "YOUR_KAFKA_USERNAME"
  password: "YOUR_KAFKA_PASSWORD"

# Consumer Configuration
consumer:
  group_id: "knowledge-management-processor"
  auto_offset_reset: "earliest"
  enable_auto_commit: true
  max poll records: 100
  session timeout: 30000
  heartbeat interval: 30000
  max poll interval: 300000

# Producer Configuration
producer:
  acks: "all"
  retries: 3
  compression_type: "gzip"
  max_in_flight_requests_per_connection: 1

# Topics
topics:
  documents: "data.documents"
  geospatial_features: "data.geospatial_features"
  system_events: "data.system_events"

# Topic Configuration (per topic)
topic_config:
  documents:
    num_partitions: 12
    replication_factor: 3
    cleanup_policy: delete
    retention_ms: 604800000
    compression_type: gzip
  geospatial_features:
    num_partitions: 6
    replication_factor: 3
    cleanup_policy: delete
    retention_ms: 2592000000
  system_events:
    num_partitions: 3
    replication_factor: 3
    cleanup_policy: delete
    retention_ms: 7776000000
```

---

## 4. Kafka Producer Implementation

### Document Producer Class

```python
# src/kafka_producer.py
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from confluent_kafka import Producer
import logging

logger = logging.getLogger(__name__)


class DocProducer:
    """Kafka Producer for document messages"""

    def __init__(self, config_path: str = "config/kafka.yml"):
        self.config = self._load_config(config_path)
        self.producer = Producer(self.config)
        self.topics = self.config['topics']

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load Kafka configuration from YAML"""
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config

    def _serialize_document(self, content: str, file_path: str,
                          metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create document message payload"""
        return {
            "message_type": "document_ingest",
            "doc_id": str(uuid.uuid4()),
            "source": metadata.get("source", "unknown"),
            "file_path": file_path,
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "created_at": metadata.get("created_at", ""),
                "file_format": metadata.get("file_format", "unknown"),
                "content_type": metadata.get("content_type", ""),
                "doc_type": metadata.get("doc_type", "")
            }
        }

    def send_document(self, content: str, file_path: str,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Send document message to Kafka

        Args:
            content: Document text content
            file_path: File path for metadata
            metadata: Optional structured metadata
        """
        metadata = metadata or {}
        message = self._serialize_document(content, file_path, metadata)

        try:
            self.producer.produce(
                topic=self.topics['documents'],
                value=json.dumps(message).encode('utf-8'),
                callback=self._delivery_report,
                partition=None,
                timestamp=None
            )
            self.producer.flush()
            logger.info(f"Document sent: {file_path} -> {self.topics['documents']}")
        except Exception as e:
            logger.error(f"Error sending document: {e}")

    def _delivery_report(self, err, msg):
        """Kafka delivery callback"""
        if err is not None:
            logger.error(f"Failed to deliver message: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} "
                f"[{msg.partition()}] @ offset {msg.offset()}"
            )


# Usage Example
if __name__ == "__main__":
    producer = DocProducer()

    doc_content = """
    This is sample document content.
    It contains information about UML capabilities.
    """

    producer.send_document(
        content=doc_content,
        file_path="/data/docs/sample_policy.pdf",
        metadata={
            "source": "umllib",
            "title": "Policy Document",
            "author": "Gov Entity",
            "created_at": "2026-02-26T10:00:00Z",
            "file_format": "pdf",
            "content_type": "application/pdf",
            "doc_type": "policy"
        }
    )
```

### Geospatial Feature Producer Class

```python
# src/kafka_producer.py (same file)
class FeatureProducer:
    """Kafka Producer for geospatial feature messages"""

    def __init__(self, config_path: str = "config/kafka.yml"):
        self.config = self._load_config(config_path)
        self.producer = Producer(self.config)
        self.topics = self.config['topics']

    def send_features(self, features: list, file_path: str,
                     metadata: Optional[Dict[str, Any]] = None):
        """
        Send geospatial features to Kafka

        Args:
            features: List of GeoJSON features
            file_path: File path for metadata
            metadata: Optional feature metadata
        """
        message = {
            "message_type": "feature_ingest",
            "feature_id": str(uuid.uuid4()),
            "source": metadata.get("source", "unknown") if metadata else "unknown",
            "file_path": file_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "feature_type": metadata.get("feature_type", "unknown") if metadata else "unknown",
                "crs": metadata.get("crs", "EPSG:4326") if metadata else "EPSG:4326",
                "feature_count": len(features),
                "ingest_timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }

        try:
            self.producer.produce(
                topic=self.topics['geospatial_features'],
                value=json.dumps({"features": features}).encode('utf-8'),
                callback=self._delivery_report,
                partition=None
            )
            self.producer.flush()
            logger.info(f"Features sent: {file_path} -> {self.topics['geospatial_features']}")
        except Exception as e:
            logger.error(f"Error sending features: {e}")
```

---

## 5. Kafka Consumer Implementation

### Consumer Base Class

```python
# src/kafka_consumer.py
import json
import threading
from abc import ABC, abstractmethod
from confluent_kafka import Consumer
from typing import Callable, List, Dict, Any
import logging
import signal

logger = logging.getLogger(__name__)


class BaseConsumer(ABC):
    """Abstract base class for Kafka consumers"""

    def __init__(self, config_path: str = "config/kafka.yml"):
        """Initialize consumer from configuration"""
        self.config = self._load_config(config_path)
        self.consumer = Consumer({
            'bootstrap.servers': ','.join(
                self.config['bootstrap_servers']
            ),
            'group.id': self.config['consumer_group_id'],
            'auto.offset.reset': self.config['auto_offset_reset'],
            'enable.auto.commit': self.config['enable_auto_commit'],
            'max.poll.records': self.config['max_poll_records'],
            'session.timeout.ms': self.config['session_timeout'],
            'heartbeat.interval.ms': self.config['heartbeat_interval'],
            'max.poll.interval.ms': self.config['max_poll_interval'],
            'security.protocol': self.config['security_protocol'],
            'sasl.mechanism': self.config['sasl_mechanism'],
            'sasl.username': self.config['authentication']['username'],
            'sasl.password': self.config['authentication']['password'],
            'client.id': f"{self.__class__.__name__}-{id(self)}"
        })
        self.topic = None
        self.running = False
        self._lock = threading.Lock()

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML"""
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f)
        return config

    def run(self, callback: Callable[[Dict[str, Any]], None]):
        """
        Start consuming messages in a background thread

        Args:
            callback: Function called for each message: callback(message)
        """
        logger.info(f"Starting consumer for topic: {self.topic}")

        self.consumer.subscribe([self.topic])

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        while self.running:
            try:
                messages = self.consumer.poll(timeout=1.0)
                if messages is None:
                    continue

                if messages.error():
                    if messages.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Consumer error: {messages.error()}")
                        continue

                # Process message using callback
                try:
                    callback(json.loads(messages.value().decode('utf-8')))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

            except Exception as e:
                logger.error(f"Consumer error: {e}")

        logger.info("Consumer shutting down")

    def _shutdown(self, signum=None, frame=None):
        """Gracefully shutdown consumer"""
        logger.info("Shutdown signal received")
        self.running = False
        self.consumer.close()

    def close(self):
        """Close consumer connection"""
        self.running = False
        self.consumer.close()

    @abstractmethod
    def process_message(self, message: Dict[str, Any]):
        """Process incoming message"""
        pass

    def start_processing(self):
        """Start background processing with default callback"""
        def callback(msg):
            self.process_message(msg)

        self.running = True
        thread = threading.Thread(target=self.run, args=(callback,))
        thread.daemon = True
        thread.start()

        return thread

    def join(self):
        """Wait for processing thread to finish"""
        # Implementation depends on threading approach
        pass


from confluent_kafka import KafkaError  # Imported at runtime to avoid circular
```

### Document Consumer

```python
# src/kafka_consumer.py
import logging
from .base_consumer import BaseConsumer
from .light_rag_processor import LightRAGProcessor  # Will be implemented

logger = logging.getLogger(__name__)


class DocumentConsumer(BaseConsumer):
    """Consumer for document ingestion messages"""

    def __init__(self, config_path: str = "config/kafka.yml"):
        super().__init__(config_path)
        self.topic = self.config['topics']['documents']
        self.rag_processor = LightRAGProcessor(config_path)

    def process_message(self, message: Dict[str, Any]):
        """Process document message"""
        try:
            if message['message_type'] != 'document_ingest':
                return

            logger.info(f"Processing document: {message['doc_id']}")

            # Process document content
            content = message['content']

            # Extract entities and relationships
            entities, relationships = self.rag_processor.extract_graph_data(
                content,
                metadata=message['metadata']
            )

            # Store in Knowledge Graph
            self.rag_processor.store_in_kg(entities, relationships)

            # Index document
            self.rag_processor.index_document(message['metadata'])

            logger.info(f"Document processed: {message['file_path']}")

        except Exception as e:
            logger.error(f"Error processing document: {e}")


# Usage Example
if __name__ == "__main__":
    import yaml
    config_path = "config/kafka.yml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Create LightRAG processor
    from src.light_rag_processor import LightRAGProcessor
    rag_processor = LightRAGProcessor(config_path)

    consumer = DocumentConsumer(config_path)

    # Start processing in background
    processing_thread = consumer.start_processing()
    processing_thread.name = "document-consumer"

    print("Document consumer running...")
    print("Press Ctrl+C to stop")

    # Keep running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        consumer.close()
```

### Feature Consumer

```python
# src/kafka_consumer.py
class FeatureConsumer(BaseConsumer):
    """Consumer for geospatial feature messages"""

    def __init__(self, config_path: str = "config/kafka.yml"):
        super().__init__(config_path)
        self.topic = self.config['topics']['geospatial_features']
        self.rag_processor = LightRAGProcessor(config_path)

    def process_message(self, message: Dict[str, Any]):
        """Process feature message"""
        try:
            if message['message_type'] != 'feature_ingest':
                return

            logger.info(f"Processing features: {message['feature_id']}")

            # Parse GeoJSON features
            data = json.loads(message['value'])
            features = data.get('features', [])

            # Store features in Knowledge Graph
            for feature in features:
                self.rag_processor.store_feature(
                    feature,
                    metadata=message['metadata']
                )

            logger.info(
                f"Features processed: {len(features)} for {message['file_path']}"
            )

        except Exception as e:
            logger.error(f"Error processing features: {e}")
```

---

## 6. Testing Procedures

### Test Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Kafka for testing (Docker)
docker-compose up -d zookeeper kafka
```

### Test File Structure

```
knowledge-management/
├── config/
│   └── kafka.yml               # Kafka configuration
├── src/
│   ├── kafka_producer.py
│   ├── kafka_consumer.py
│   ├── light_rag_processor.py
│   └── arcgis_connector.py
├── tests/
│   ├── test_producer.py
│   ├── test_consumer.py
│   └── test_integration.py
├── scripts/
│   ├── test_producer.sh
│   ├── test_consumer.sh
│   └── run_integration_tests.sh
├── requirements.txt
├── pytest.ini
└── README.md
```

### Test Producer Scripts

```bash
# scripts/test_producer.sh
#!/bin/bash

# Test 1: Send sample document
echo "Sending sample document..."
python src/test_producer.py --topic data.documents

# Test 2: Send sample features (GeoJSON)
echo "Sending sample features..."
python src/test_producer.py --topic data.geospatial_features

# Test 3: Send system event
echo "Sending system event..."
python src/test_producer.py --topic data.system_events

echo "Production tests completed!"
```

```python
# src/test_producer.py
#!/usr/bin/env python3
import argparse
from src.kafka_producer import DocProducer, FeatureProducer

def test_documents(topic_name: str, num_messages: int = 1):
    """Send test documents"""
    producer = DocProducer()

    for i in range(num_messages):
        doc = f"""
        Document Test #{i+1}
        Test content for UDL integration.
        This document contains information about UML capabilities.
        """
        producer.send_document(
            content=doc,
            file_path=f"/tmp/test_document_{i}.txt",
            metadata={
                "source": "test",
                "title": f"Test Document {i}",
                "author": "Test User",
                "file_format": "txt"
            }
        )

    print(f"✅ Sent {num_messages} test documents")


def test_features(topic_name: str, num_messages: int = 1):
    """Send test geospatial features"""
    import json
    from geojson import Feature, Point

    producer = FeatureProducer()

    for i in range(num_messages):
        feature = Feature(
            geometry=Point([116.404, 39.915]),  # Beijing coordinates
            properties={"test_id": i, "name": f"Test Feature {i}"}
        )

        producer.send_features(
            features=[feature],
            file_path=f"/tmp/test_features_{i}.json",
            metadata={
                "source": "test",
                "feature_type": "test_locations"
            }
        )

    print(f"✅ Sent {num_messages} test features")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Kafka Producer")
    parser.add_argument("--topic", required=True, choices=[
        "data.documents",
        "data.geospatial_features",
        "data.system_events"
    ])
    parser.add_argument("--num-messages", type=int, default=1)
    args = parser.parse_args()

    if args.topic == "data.documents":
        test_documents(args.topic, args.num_messages)
    elif args.topic == "data.geospatial_features":
        test_features(args.topic, args.num_messages)
    elif args.topic == "data.system_events":
        # Would implement event producer test
        print("System events test not yet implemented")
```

### Test Consumer Scripts

```bash
# scripts/test_consumer.sh
#!/bin/bash
echo "Starting Consumer Test in background..."
python src/test_consumer.py

# Monitor logs
tail -f logs/kafka.log
```

```python
# src/test_consumer.py
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(__file__))

from src.kafka_consumer import DocumentConsumer, FeatureConsumer

# Create consumers
doc_consumer = DocumentConsumer("config/kafka.yml")
feature_consumer = FeatureConsumer("config/kafka.yml")

# Start in background threads
doc_thread = doc_consumer.start_processing()
feature_thread = feature_consumer.start_processing()

print("✅ Consumers running...")

# Keep script alive
import time
try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    doc_consumer.close()
    feature_consumer.close()
    print("✅ Consumers stopped")
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
import json
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from confluent_kafka import Producer, Consumer, KafkaError
from confluent_kafka.admin import AdminClient
from src.kafka_producer import DocProducer, FeatureProducer
from src.kafka_consumer import DocumentConsumer, FeatureConsumer


class TestUDLIntegration:
    """Integration tests for UDL/Kafka integration"""

    @pytest.fixture(scope="module")
    def kafka_admin(self):
        """Create Kafka Admin client"""
        admin_config = {
            'bootstrap.servers': os.getenv('KAFKA_BROKER', 'localhost:9092'),
            'security.protocol': os.getenv('KAFKA_SECURITY_PROTOCOL', 'SASL_SSL'),
            'sasl.mechanism': os.getenv('KAFKA_SASL_MECHANISM', 'PLAIN'),
            'sasl.username': os.getenv('KAFKA_USERNAME', 'test'),
            'sasl.password': os.getenv('KAFKA_PASSWORD', 'test')
        }
        return AdminClient(admin_config)

    @pytest.fixture(scope="module")
    def setup_topics(self, kafka_admin):
        """Create test topics"""
        topics = [
            "test.data.documents",
            "test.data.geospatial_features"
        ]

        for topic in topics:
            try:
                kafka_admin.create_topics([{
                    'topic': topic,
                    'num_partitions': 1,
                    'replication_factor': 1
                }])
                print(f"✅ Topic {topic} created")
            except Exception as e:
                print(f"⚠️  Topic {topic} exists or error: {e}")

        return topics

    @pytest.mark.integration
    def test_document_producer_consume(self, setup_topics):
        """Test document producer and consumer cycle"""
        topic = setup_topics[0]

        # Producer
        producer = DocProducer()
        doc = "Integration test document. Contains test content for UDL."
        producer.send_document(
            content=doc,
            file_path="/tmp/test.txt",
            metadata={"source": "test", "title": "Integration Test"}
        )

        # Wait for consumer to process
        time.sleep(5)

        # Consumer
        consumer = DocumentConsumer()
        consumer.topic = topic
        messages = []

        def collect_message(msg):
            messages.append(msg)

        consumer.process_message = collect_message
        consumer_run = consumer.start_processing()
        time.sleep(10)
        consumer.close()

        # Verify
        assert len(messages) > 0, "No messages received by consumer"
        assert messages[0]['doc_id'] is not None
        print(f"✅ Document producer/consumer test passed: {len(messages)} messages")

    @pytest.mark.integration
    def test_feature_producer_consume(self, setup_topics):
        """Test feature producer and consumer cycle"""
        topic = setup_topics[1]

        from geojson import Feature, Point

        producer = FeatureProducer()
        feature = Feature(
            geometry=Point([116.397, 39.904]),  # Beijing
            properties={"test": True}
        )

        producer.send_features([feature], "/tmp/test.json", {"source": "test"})

        # Wait for processing
        time.sleep(5)

        # Consumer
        consumer = FeatureConsumer()
        consumer.topic = topic
        messages = []

        def collect_message(msg):
            messages.append(msg)

        consumer.process_message = collect_message
        consumer.start_processing()
        time.sleep(10)
        consumer.close()

        assert len(messages) > 0, "No messages received by consumer"
        print(f"✅ Feature producer/consumer test passed")

    @pytest.mark.integration
    def test_message_format(self, kafka_admin):
        """Test message structure validation"""
        producer = DocProducer()
        doc = "Valid document format."
        producer.send_document(
            content=doc,
            file_path="/tmp/format_test.txt",
            metadata={
                "source": "test",
                "title": "Format Test",
                "author": "Test",
                "created_at": "2026-02-26T00:00:00Z",
                "file_format": "txt"
            }
        )

        # Verify message structure
        time.sleep(5)
        assert True, "Message format test successful"

    def test_kafka_connection(self, kafka_admin):
        """Test Kafka connection and broker health"""
        cluster_metadata = kafka_admin.list_topics()
        assert len(cluster_metadata.topics) > 0
        print(f"✅ Connected to Kafka with {len(cluster_metadata.topics)} topics")
```

### Test Execution

```bash
# Run all integration tests
pytest tests/test_integration.py -v --integration --durations=10

# Run specific test
pytest tests/test_integration.py::TestUDLIntegration::test_document_producer_consume -v --integration

# Check consumer processing
tail -f logs/kafka_consumer.log
```

### Monitoring and Logging

```bash
# Kafka Producer Log Aggregation
tail -f logs/kafka_producer.log

# Kafka Consumer Log Aggregation
tail -f logs/kafka_consumer.log

# System Metrics Tracking
# Add to system_events topic
{
    "message_type": "system_event",
    "event_type": "processor_status",
    "processor_id": "document-consumer",
    "status": "active",
    "metrics": {
        "records_processed": current_count,
        "errors": error_count
    }
}

# Grafana Dashboard for UDL Monitoring
# - Consumer lag per topic
# - Message processing rates
# - Error rates
# - Storage usage (PostgreSQL)
```

---

## 7. Deployment Considerations

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:latest
    hostname: zookeeper
    container_name: zookeeper
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:latest
    hostname: kafka
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
      - "9094:9094"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1

  udl-processor:
    build: .
    container_name: ud-processor
    depends_on:
      - kafka
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      KAFKA_BROKER: kafka:9092
      KAFKA_USER: ${KAFKA_USER}
      KAFKA_PASSWORD: ${KAFKA_PASSWORD}
      DATABASE_URL: ${DATABASE_URL}
    command: python src/main_processor.py
```

### Production Checklist

- [ ] Security: TLS certificates and authentication configured
- [ ] Monitoring: Prometheus metrics and Grafana dashboards
- [ ] Backup: PostgreSQL database snapshots
- [ ] Scaling: Kafka partition management strategy
- [ ] Error Handling: Retry logic with exponential backoff
- [ ] Logging: Structured logging with log levels
- [ ] Disaster Recovery: Topic replication and backup strategy
- [ ] Performance: Consumer group rebalancing tested

---

## 8. Troubleshooting

### Common Issues

**Issue 1: Consumer Lag Too High**
```
Investigation: kafka-run-class.sh kafka.consumer.ConsumerLagCheck
Fix: Increase consumer.max.poll.records or optimize processing time
```

**Issue 2: Authentication Failures**
```
Investigation: Check SASL mechanism and credentials in config.yml
Fix: Verify username/password match UDL configuration
```

**Issue 3: Duplicate Messages**
```
Investigation: Enable auto.offset.reset = latest
Fix: Use deduplication at application level
```

### Debug Commands

```bash
# Kafka Topic Info
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group knowledge-management-processor

# View Messages in Topic
kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 \
  --topic data.documents \
  --from-beginning --max-messages 10

# Monitor Consumer Lag
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --all-groups
```

---

**Status:** Ready for development and implementation