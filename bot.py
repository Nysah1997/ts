"""
Bot básico de TeamSpeak 3 que se conecta usando ServerQuery
"""

import ts3
import time
import logging
import sys
from config import (
    TS3_HOST, TS3_PORT, TS3_QUERY_PORT, 
    TS3_USERNAME, TS3_PASSWORD,
    RECONNECT_DELAY, MAX_RECONNECT_ATTEMPTS
)

class TeamSpeakBot:
    def __init__(self):
        self.ts3conn = None
        self.connected = False
        self.reconnect_attempts = 0
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """Conectar al servidor TeamSpeak 3"""
        try:
            self.logger.info(f"Intentando conectar a {TS3_HOST}:{TS3_QUERY_PORT}...")
            
            # Crear conexión ServerQuery con timeout
            self.ts3conn = ts3.query.TS3Connection(TS3_HOST, TS3_QUERY_PORT)
            
            self.logger.info("Conexión ServerQuery establecida exitosamente")
            
            # Autenticar con las credenciales
            self.logger.info(f"Autenticando con usuario: {TS3_USERNAME}")
            self.ts3conn.exec_("login", client_login_name=TS3_USERNAME, client_login_password=TS3_PASSWORD)
            
            self.logger.info("✅ Autenticación exitosa")
            
            # Seleccionar el servidor virtual (por defecto el ID 1)
            self.ts3conn.exec_("use", sid=1)
            self.logger.info("Servidor virtual seleccionado")
            
            self.connected = True
            self.reconnect_attempts = 0
            
            # Mostrar información del servidor
            self.show_server_info()
            
            return True
            
        except ts3.query.TS3QueryError as e:
            self.logger.error(f"❌ Error de TeamSpeak Query: {e}")
            self.logger.error(f"Detalles del error: {type(e).__name__}")
            self.connected = False
            return False
        except ConnectionError as e:
            self.logger.error(f"❌ Error de conexión de red: {e}")
            self.logger.error("Verifica que el servidor esté accesible y el puerto correcto")
            self.connected = False
            return False
        except TimeoutError as e:
            self.logger.error(f"❌ Timeout de conexión: {e}")
            self.logger.error("El servidor no responde en el tiempo esperado")
            self.connected = False
            return False
        except Exception as e:
            self.logger.error(f"❌ Error de conexión: {e}")
            self.logger.error(f"Tipo de error: {type(e).__name__}")
            import traceback
            self.logger.error(f"Stack trace: {traceback.format_exc()}")
            self.connected = False
            return False
    
    def show_server_info(self):
        """Mostrar información básica del servidor"""
        try:
            # Obtener información del servidor
            server_info = self.ts3conn.exec_("serverinfo")
            
            if server_info:
                server_data = server_info[0]
                
                print("\n" + "="*50)
                print("📊 INFORMACIÓN DEL SERVIDOR")
                print("="*50)
                print(f"🏷️  Nombre: {server_data.get('virtualserver_name', 'N/A')}")
                print(f"👥 Clientes conectados: {server_data.get('virtualserver_clientsonline', 'N/A')}")
                print(f"📊 Máximo de clientes: {server_data.get('virtualserver_maxclients', 'N/A')}")
                print(f"🌐 IP: {server_data.get('virtualserver_ip', 'N/A')}")
                print(f"🔌 Puerto: {server_data.get('virtualserver_port', 'N/A')}")
                print(f"⏰ Tiempo activo: {server_data.get('virtualserver_uptime', 'N/A')} segundos")
                print("="*50)
                
                # Mostrar lista de clientes conectados
                self.show_connected_clients()
                
        except Exception as e:
            self.logger.error(f"Error al obtener información del servidor: {e}")
    
    def show_connected_clients(self):
        """Mostrar lista de clientes conectados"""
        try:
            clients = self.ts3conn.exec_("clientlist")
            
            if clients:
                print("\n👥 CLIENTES CONECTADOS:")
                print("-" * 30)
                for client in clients:
                    client_name = client.get('client_nickname', 'Desconocido')
                    client_id = client.get('clid', 'N/A')
                    client_type = client.get('client_type', '0')
                    
                    # Filtrar bots del servidor (client_type = 1)
                    if client_type == '0':
                        print(f"  👤 {client_name} (ID: {client_id})")
                print("-" * 30)
                
        except Exception as e:
            self.logger.error(f"Error al obtener lista de clientes: {e}")
    
    def disconnect(self):
        """Desconectar del servidor"""
        if self.ts3conn:
            try:
                self.ts3conn.exec_("logout")
                self.ts3conn.close()
                self.logger.info("🔌 Desconectado del servidor")
            except Exception as e:
                self.logger.error(f"Error al desconectar: {e}")
            finally:
                self.connected = False
                self.ts3conn = None
    
    def is_connected(self):
        """Verificar si la conexión está activa"""
        if not self.connected or not self.ts3conn:
            return False
        
        try:
            # Hacer una consulta simple para verificar la conexión
            self.ts3conn.exec_("whoami")
            return True
        except:
            self.connected = False
            return False
    
    def reconnect(self):
        """Intentar reconectar al servidor"""
        if self.reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
            self.logger.error(f"❌ Máximo de intentos de reconexión alcanzado ({MAX_RECONNECT_ATTEMPTS})")
            return False
        
        self.reconnect_attempts += 1
        self.logger.info(f"🔄 Intento de reconexión {self.reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS}")
        
        # Limpiar conexión anterior
        self.disconnect()
        
        # Esperar antes de reconectar
        time.sleep(RECONNECT_DELAY)
        
        return self.connect()
    
    def run(self):
        """Ejecutar el bot de forma continua"""
        self.logger.info("🚀 Iniciando bot de TeamSpeak 3...")
        
        # Conectar inicialmente
        if not self.connect():
            self.logger.error("❌ No se pudo establecer la conexión inicial")
            return
        
        self.logger.info("✅ Bot conectado y ejecutándose...")
        self.logger.info("Presiona Ctrl+C para detener el bot")
        
        try:
            while True:
                # Verificar conexión cada 60 segundos
                if not self.is_connected():
                    self.logger.warning("⚠️  Conexión perdida, intentando reconectar...")
                    if not self.reconnect():
                        self.logger.error("❌ No se pudo reconectar. Deteniendo bot.")
                        break
                
                # Esperar antes de la siguiente verificación
                time.sleep(60)
                
                # Mostrar estado cada 5 minutos
                if time.time() % 300 < 60:  # Aproximadamente cada 5 minutos
                    self.logger.info("💚 Bot funcionando correctamente...")
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Deteniendo bot por solicitud del usuario...")
        except Exception as e:
            self.logger.error(f"❌ Error inesperado: {e}")
        finally:
            self.disconnect()
            self.logger.info("👋 Bot detenido")
