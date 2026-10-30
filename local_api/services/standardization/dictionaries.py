"""Version-controlled dictionaries for canonical technology names, aliases, and safe OCR/spelling corrections."""

# ---------------------------------------------------------------------------
# 1. Technology and Tool Canonicalization Aliases
# Key: casefolded lowercase string
# Value: Canonical official spelling/casing
# ---------------------------------------------------------------------------
TECH_ALIASES: dict[str, str] = {
    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "postgress": "PostgreSQL",
    "postgre sql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "mongo db": "MongoDB",
    "cassandra": "Apache Cassandra",
    "apache cassandra": "Apache Cassandra",
    "redis": "Redis",
    "oracle": "Oracle",
    "mysql": "MySQL",
    "sqlite": "SQLite",
    "mariadb": "MariaDB",
    "dynamodb": "DynamoDB",
    "elasticsearch": "Elasticsearch",

    # Messaging & Streaming
    "kafka": "Kafka",
    "kafkka": "Kafka",
    "apache kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "activemq": "ActiveMQ",
    "pulsar": "Apache Pulsar",

    # Web & App Servers
    "apache tomcat9": "Apache Tomcat 9",
    "apache tomcat 9": "Apache Tomcat 9",
    "tomcat9": "Apache Tomcat 9",
    "tomcat": "Apache Tomcat",
    "apache tomcat": "Apache Tomcat",
    "nginx": "NGINX",
    "apache": "Apache HTTP Server",

    # Collaboration & Productivity Tools
    "jira": "Jira",
    "jira software": "Jira",
    "confluence": "Confluence",
    "ms visio": "Microsoft Visio",
    "visio": "Microsoft Visio",
    "microsoft visio": "Microsoft Visio",
    "teams": "Microsoft Teams",
    "ms teams": "Microsoft Teams",
    "microsoft teams": "Microsoft Teams",
    "draw.io": "draw.io",
    "drawio": "draw.io",
    "excel": "Microsoft Excel",
    "ms excel": "Microsoft Excel",
    "microsoft excel": "Microsoft Excel",
    "slack": "Slack",
    "trello": "Trello",

    # Testing & QA Tools
    "postman": "Postman",
    "hp alm": "HP ALM",
    "selenium": "Selenium",
    "junit": "JUnit",
    "testng": "TestNG",
    "jmeter": "Apache JMeter",
    "cypress": "Cypress",
    "finsim": "FINSIM",
    "msgsim": "MSGSIM",
    "t3": "T3",
    "boss": "BOSS",
    "ist switch": "IST Switch",
    "bharat switch": "Bharat Switch",
    "nexus": "Nexus",

    # Programming Languages & Frameworks
    "python": "Python",
    "python3": "Python",
    "golang": "Go",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "node js": "Node.js",
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "angular": "Angular",
    "angularjs": "AngularJS",
    "vue": "Vue.js",
    "vuejs": "Vue.js",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "spring-boot": "Spring Boot",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "docker": "Docker",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Microsoft Azure",

    # Operating Systems
    "linux": "Linux",
    "windows": "Windows",
    "ubuntu": "Ubuntu",
    "unix": "Unix",
    "macos": "macOS",
    "redhat": "Red Hat Enterprise Linux",
    "rhel": "Red Hat Enterprise Linux",
}

# ---------------------------------------------------------------------------
# 2. Technology Classification Categories
# ---------------------------------------------------------------------------
TECH_CATEGORIES: dict[str, str] = {
    # Programming Languages
    "Python": "programming_languages",
    "Go": "programming_languages",
    "Java": "programming_languages",
    "JavaScript": "programming_languages",
    "TypeScript": "programming_languages",
    "C++": "programming_languages",
    "C#": "programming_languages",
    "SQL": "programming_languages",
    "Ruby": "programming_languages",
    "PHP": "programming_languages",
    "Bash": "programming_languages",
    "Scala": "programming_languages",

    # Operating Systems
    "Linux": "operating_systems",
    "Windows": "operating_systems",
    "Ubuntu": "operating_systems",
    "Unix": "operating_systems",
    "macOS": "operating_systems",
    "Red Hat Enterprise Linux": "operating_systems",

    # Databases
    "PostgreSQL": "databases",
    "MongoDB": "databases",
    "Apache Cassandra": "databases",
    "Redis": "databases",
    "Oracle": "databases",
    "MySQL": "databases",
    "SQLite": "databases",
    "MariaDB": "databases",
    "DynamoDB": "databases",
    "Elasticsearch": "databases",

    # Messaging and Streaming
    "Kafka": "messaging_and_streaming",
    "RabbitMQ": "messaging_and_streaming",
    "ActiveMQ": "messaging_and_streaming",
    "Apache Pulsar": "messaging_and_streaming",

    # Testing Tools
    "Postman": "testing_tools",
    "HP ALM": "testing_tools",
    "Selenium": "testing_tools",
    "JUnit": "testing_tools",
    "TestNG": "testing_tools",
    "Apache JMeter": "testing_tools",
    "Cypress": "testing_tools",
    "FINSIM": "testing_tools",
    "MSGSIM": "testing_tools",
    "T3": "testing_tools",

    # Collaboration Tools
    "Jira": "collaboration_tools",
    "Confluence": "collaboration_tools",
    "Microsoft Visio": "collaboration_tools",
    "Microsoft Teams": "collaboration_tools",
    "draw.io": "collaboration_tools",
    "Microsoft Excel": "collaboration_tools",
    "Slack": "collaboration_tools",
    "Trello": "collaboration_tools",

    # Web Servers
    "Apache Tomcat 9": "web_servers",
    "Apache Tomcat": "web_servers",
    "NGINX": "web_servers",
    "Apache HTTP Server": "web_servers",

    # Cloud & Platforms
    "Docker": "tools_and_platforms",
    "Kubernetes": "tools_and_platforms",
    "AWS": "tools_and_platforms",
    "GCP": "tools_and_platforms",
    "Microsoft Azure": "tools_and_platforms",
    "Node.js": "tools_and_platforms",
    "React": "tools_and_platforms",
    "Spring Boot": "tools_and_platforms",

    # Payment Technologies
    "BOSS": "payment_technologies",
    "IST Switch": "payment_technologies",
    "Bharat Switch": "payment_technologies",
    "Nexus": "payment_technologies",
}

# ---------------------------------------------------------------------------
# 3. Explicit OCR and Spelling Correction Whitelist
# Used conservatively only for common scanning artifacts and known typos.
# ---------------------------------------------------------------------------
OCR_AND_SPELLING_CORRECTIONS: dict[str, str] = {
    # Common OCR letter merges or technical typos
    "postgress": "PostgreSQL",
    "kafkka": "Kafka",
    "apache tomcat9": "Apache Tomcat 9",
    "tomcat9": "Apache Tomcat 9",
    "ms visio": "Microsoft Visio",
    "collabration tools": "Collaboration Tools",
    "requriements": "requirements",
    "experiance": "experience",
    "knowlege": "knowledge",
    "managment": "management",
    "enviroment": "environment",
    "resposibilities": "responsibilities",
}

