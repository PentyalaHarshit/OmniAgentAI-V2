from typing import Dict, List, Any


class SystemDesignCrew:
    def __init__(self):
        self.design_patterns = self.build_design_patterns()

    def run(self, query: str):
        # Analyze system requirements
        system_type = self.detect_system_type(query)
        requirements = self.extract_requirements(query)
        scale = self.estimate_scale(query)
        
        # Generate design
        architecture = self.generate_architecture(system_type, requirements, scale)
        database_design = self.design_database(system_type, requirements)
        scaling_strategy = self.design_scaling(system_type, scale)
        caching_strategy = self.design_caching(system_type, requirements)
        load_balancing = self.design_load_balancing(system_type, scale)
        
        crew_steps = [
            {"thought": "System Design Agent: analyzing requirements", "output": f"System type: {system_type}"},
            {"thought": "Architecture Designer: creating system architecture", "output": "Architecture designed"},
            {"thought": "Database Designer: selecting database schema", "output": "Database design complete"},
            {"thought": "Scaling Strategist: planning horizontal/vertical scaling", "output": "Scaling strategy defined"},
            {"thought": "Caching Architect: designing cache layers", "output": "Caching strategy designed"},
            {"thought": "Load Balancer: distributing traffic", "output": "Load balancing configured"},
        ]
        
        return {
            "system_type": system_type,
            "requirements": requirements,
            "scale": scale,
            "architecture": architecture,
            "database_design": database_design,
            "scaling_strategy": scaling_strategy,
            "caching_strategy": caching_strategy,
            "load_balancing": load_balancing,
            "crew_steps": crew_steps,
        }

    @staticmethod
    def detect_system_type(query: str) -> str:
        """Detect the type of system from query."""
        query_lower = query.lower()
        
        system_types = {
            "video_streaming": ["youtube", "video", "streaming", "netflix", "content delivery"],
            "messaging": ["whatsapp", "messaging", "chat", "real-time", "message"],
            "social_media": ["facebook", "twitter", "social", "feed", "timeline", "posts"],
            "e-commerce": ["amazon", "ecommerce", "shopping", "cart", "payment", "product"],
            "file_storage": ["dropbox", "google drive", "file storage", "cloud storage"],
            "url_shortener": ["bitly", "url shortener", "tinyurl", "link shortener"],
            "web_scraper": ["scraper", "crawler", "web scraping", "data extraction"],
            "search_engine": ["google", "search", "elasticsearch", "indexing"],
            "api_gateway": ["api gateway", "microservices", "service mesh"],
            "notification": ["notification", "push", "email", "sms", "alert"],
        }
        
        for system_type, patterns in system_types.items():
            if any(pattern in query_lower for pattern in patterns):
                return system_type
        
        return "general_web_application"

    @staticmethod
    def extract_requirements(query: str) -> Dict[str, Any]:
        """Extract system requirements from query."""
        requirements = {
            "functional": [],
            "non_functional": [],
            "constraints": []
        }
        
        query_lower = query.lower()
        
        # Functional requirements
        if "upload" in query_lower:
            requirements["functional"].append("file_upload")
        if "search" in query_lower:
            requirements["functional"].append("search")
        if "real-time" in query_lower:
            requirements["functional"].append("real_time_updates")
        if "authentication" in query_lower or "auth" in query_lower:
            requirements["functional"].append("authentication")
        if "payment" in query_lower:
            requirements["functional"].append("payment_processing")
        
        # Non-functional requirements
        if "high availability" in query_lower or "ha" in query_lower:
            requirements["non_functional"].append("high_availability")
        if "low latency" in query_lower:
            requirements["non_functional"].append("low_latency")
        if "scalable" in query_lower:
            requirements["non_functional"].append("scalability")
        if "secure" in query_lower or "security" in query_lower:
            requirements["non_functional"].append("security")
        
        # Constraints
        if "million" in query_lower:
            requirements["constraints"].append("millions_of_users")
        if "billion" in query_lower:
            requirements["constraints"].append("billions_of_requests")
        if "global" in query_lower:
            requirements["constraints"].append("global_deployment")
        
        return requirements

    @staticmethod
    def estimate_scale(query: str) -> Dict[str, Any]:
        """Estimate system scale from query."""
        query_lower = query.lower()
        
        scale = {
            "users": "thousands",
            "requests_per_second": "hundreds",
            "data_size": "GB",
            "growth_rate": "moderate"
        }
        
        if "million" in query_lower:
            scale["users"] = "millions"
            scale["requests_per_second"] = "thousands"
            scale["data_size"] = "TB"
        
        if "billion" in query_lower:
            scale["users"] = "billions"
            scale["requests_per_second"] = "millions"
            scale["data_size"] = "PB"
        
        if "high growth" in query_lower or "rapid growth" in query_lower:
            scale["growth_rate"] = "high"
        
        return scale

    def generate_architecture(self, system_type: str, requirements: Dict, scale: Dict) -> Dict[str, Any]:
        """Generate system architecture."""
        architectures = {
            "video_streaming": {
                "components": ["CDN", "Load Balancer", "API Gateway", "Video Service", "Metadata Service", "User Service", "Recommendation Engine"],
                "pattern": "Microservices with Event-Driven Architecture"
            },
            "messaging": {
                "components": ["Load Balancer", "API Gateway", "Message Service", "WebSocket Server", "Presence Service", "Media Service", "Database Cluster"],
                "pattern": "Real-time Microservices with WebSocket"
            },
            "social_media": {
                "components": ["Load Balancer", "API Gateway", "User Service", "Post Service", "Feed Service", "Notification Service", "Graph Service"],
                "pattern": "Microservices with Graph Database"
            },
            "e-commerce": {
                "components": ["Load Balancer", "API Gateway", "User Service", "Product Service", "Order Service", "Payment Service", "Inventory Service"],
                "pattern": "Microservices with Event Sourcing"
            },
            "general_web_application": {
                "components": ["Load Balancer", "API Gateway", "Application Server", "Database", "Cache"],
                "pattern": "Three-Tier Architecture"
            }
        }
        
        return architectures.get(system_type, architectures["general_web_application"])

    def design_database(self, system_type: str, requirements: Dict) -> Dict[str, Any]:
        """Design database architecture."""
        databases = {
            "video_streaming": {
                "primary": "NoSQL (MongoDB/Cassandra) for metadata",
                "secondary": "PostgreSQL for user data",
                "cache": "Redis for session and hot data",
                "storage": "S3/Object Storage for video files"
            },
            "messaging": {
                "primary": "Cassandra for message storage",
                "secondary": "PostgreSQL for user profiles",
                "cache": "Redis for online status and sessions",
                "queue": "Kafka/RabbitMQ for message queuing"
            },
            "social_media": {
                "primary": "Graph Database (Neo4j) for relationships",
                "secondary": "PostgreSQL for user data",
                "cache": "Redis for feed caching",
                "search": "Elasticsearch for content search"
            },
            "e-commerce": {
                "primary": "PostgreSQL for transactions",
                "secondary": "MongoDB for product catalog",
                "cache": "Redis for cart and session",
                "search": "Elasticsearch for product search"
            },
            "general_web_application": {
                "primary": "PostgreSQL/MySQL",
                "cache": "Redis",
                "backup": "Read replicas"
            }
        }
        
        return databases.get(system_type, databases["general_web_application"])

    def design_scaling(self, system_type: str, scale: Dict) -> Dict[str, Any]:
        """Design scaling strategy."""
        users = scale.get("users", "thousands")
        
        if users == "billions":
            return {
                "horizontal_scaling": "Auto-scaling groups across multiple regions",
                "vertical_scaling": "High-performance instances",
                "database_scaling": "Sharding + Read Replicas",
                "cdn": "Global CDN with edge locations",
                "strategy": "Horizontal scaling with database sharding"
            }
        elif users == "millions":
            return {
                "horizontal_scaling": "Auto-scaling groups",
                "vertical_scaling": "Optimized instance types",
                "database_scaling": "Read Replicas + Partitioning",
                "cdn": "Regional CDN",
                "strategy": "Horizontal scaling with read replicas"
            }
        else:
            return {
                "horizontal_scaling": "Load balancer with multiple servers",
                "vertical_scaling": "Adequate instance sizing",
                "database_scaling": "Read replicas",
                "cdn": "Optional CDN",
                "strategy": "Basic horizontal scaling"
            }

    def design_caching(self, system_type: str, requirements: Dict) -> Dict[str, Any]:
        """Design caching strategy."""
        return {
            "cache_layers": ["Application cache", "Database cache", "CDN cache"],
            "cache_type": "Redis/Memcached",
            "cache_strategy": "Cache-aside with TTL",
            "invalidation": "Write-through for critical data",
            "distribution": "Distributed cache for high availability"
        }

    def design_load_balancing(self, system_type: str, scale: Dict) -> Dict[str, Any]:
        """Design load balancing strategy."""
        users = scale.get("users", "thousands")
        
        if users == "billions":
            return {
                "type": "Global Load Balancer (GSLB)",
                "algorithm": "Least Connections with Geographic routing",
                "health_checks": "Active health checks with circuit breakers",
                "ssl_termination": "At load balancer level",
                "session_persistence": "Sticky sessions if required"
            }
        elif users == "millions":
            return {
                "type": "Application Load Balancer",
                "algorithm": "Round Robin with health checks",
                "health_checks": "Active health checks",
                "ssl_termination": "At load balancer",
                "session_persistence": "As needed"
            }
        else:
            return {
                "type": "Load Balancer",
                "algorithm": "Round Robin",
                "health_checks": "Basic health checks",
                "ssl_termination": "Optional",
                "session_persistence": "Not required"
            }

    def build_design_patterns(self) -> Dict[str, List[str]]:
        """Build common design patterns database."""
        return {
            "scalability": ["Horizontal Scaling", "Vertical Scaling", "Database Sharding", "Read Replicas", "Caching"],
            "availability": ["Load Balancing", "Failover", "Multi-region Deployment", "Health Checks", "Circuit Breakers"],
            "consistency": ["ACID Transactions", "Eventual Consistency", "Distributed Transactions", "Optimistic Locking"],
            "performance": ["Caching", "CDN", "Database Indexing", "Asynchronous Processing", "Connection Pooling"]
        }
