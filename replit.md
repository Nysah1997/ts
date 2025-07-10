# TeamSpeak 3 Bot

## Overview

This is a Python-based TeamSpeak 3 bot that connects to a TeamSpeak server using the ServerQuery protocol. The bot is designed to establish and maintain a connection to a TeamSpeak server for automated interactions and monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

The application follows a simple modular architecture with three main components:

1. **Configuration Module** (`config.py`) - Centralized configuration management
2. **Bot Module** (`bot.py`) - Core bot functionality and connection handling
3. **Main Entry Point** (`main.py`) - Application startup and orchestration

The architecture is designed around the ServerQuery protocol, which allows programmatic access to TeamSpeak 3 servers through a TCP-based query interface.

## Key Components

### TeamSpeakBot Class
- **Purpose**: Main bot implementation that handles ServerQuery connections
- **Key Features**: 
  - Connection management with automatic reconnection logic
  - Integrated logging system
  - Authentication handling
  - Server selection capabilities

### Configuration Management
- **Centralized Settings**: All server connection details, credentials, and operational parameters
- **Environment**: Currently uses hardcoded values but structured for easy migration to environment variables
- **Security Note**: Credentials are currently stored in plain text (should be moved to secure storage)

### Connection Protocol
- **ServerQuery**: Uses the ts3 Python library for TeamSpeak 3 ServerQuery protocol
- **Authentication**: Username/password based authentication
- **Server Selection**: Automatically selects virtual server ID 1

## Data Flow

1. **Initialization**: Bot reads configuration from config.py
2. **Connection**: Establishes TCP connection to ServerQuery port (10002)
3. **Authentication**: Logs in using provided credentials
4. **Server Selection**: Selects the target virtual server
5. **Operation**: Ready for command execution and event handling

## External Dependencies

### Python Libraries
- **ts3**: Primary library for TeamSpeak 3 ServerQuery protocol implementation
- **logging**: Built-in Python logging for operational monitoring
- **time**: For reconnection delays and timing operations

### TeamSpeak 3 Server
- **Host**: 142.4.207.51
- **Main Port**: 20131 (TeamSpeak client connections)
- **Query Port**: 10002 (ServerQuery protocol)
- **Authentication**: Requires ServerQuery user account

## Deployment Strategy

### Current Implementation
- **Runtime**: Python 3 application
- **Dependencies**: Minimal external dependencies (ts3 library)
- **Configuration**: File-based configuration with hardcoded values
- **Logging**: Console output with structured logging

### Recommended Improvements
- **Environment Variables**: Move sensitive configuration to environment variables
- **Error Handling**: Implement comprehensive error handling and recovery
- **Health Monitoring**: Add health checks and monitoring capabilities
- **Containerization**: Consider Docker deployment for easier management

### Security Considerations
- **Credential Management**: Current plain-text storage should be replaced with secure credential management
- **Network Security**: Ensure secure network connectivity to TeamSpeak server
- **Access Control**: Implement proper access controls for bot operations

### Scalability Notes
- **Single Instance**: Current design supports single bot instance
- **Stateless Design**: Bot can be easily restarted without data loss
- **Resource Usage**: Minimal resource requirements for basic operations

## Recent Changes

### 2025-07-10: Bot Implementation Completed
- **Bot funcionando exitosamente**: Conexión establecida al servidor TeamSpeak 3
- **Configuración validada**: Servidor 142.4.207.51:10002, usuario "bote" autenticado
- **Arquitectura simplificada**: Implementación con socket directo para protocolo ServerQuery
- **Características implementadas**: 
  - Conexión automática y autenticación
  - Monitoreo de estado del servidor
  - Lista de clientes conectados
  - Reconexión automática
  - Logging detallado
- **Usuario server bound detectado**: Bot configurado para servidor virtual ID 2119