"""
Bot simple de TeamSpeak 3 usando socket directo para ServerQuery
"""

import socket
import time
import logging
import sys
import threading
import re
from config import (
    TS3_HOST, TS3_PORT, TS3_QUERY_PORT, 
    TS3_USERNAME, TS3_PASSWORD,
    RECONNECT_DELAY, MAX_RECONNECT_ATTEMPTS
)

class SimpleTeamSpeakBot:
    def __init__(self):
        self.socket = None
        self.connected = False
        self.reconnect_attempts = 0
        self.server_id = None
        self.bot_client_id = None
        self.listening_events = False
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Comandos disponibles
        self.commands = {
            '!mp': self.command_mass_poke,
            '!mm': self.command_mass_move,
            '!mk': self.command_mass_kick,
            '!test': self.command_test_clients
        }
    
    def send_command(self, command):
        """Enviar comando al servidor TeamSpeak"""
        try:
            if not self.socket:
                return None
            
            full_command = command + "\n\r"
            self.socket.send(full_command.encode('utf-8'))
            
            # Leer respuesta
            response = ""
            while True:
                self.socket.settimeout(2)  # Timeout corto para no bloquear
                try:
                    data = self.socket.recv(1024).decode('utf-8')
                    response += data
                    if "error id=" in response:
                        break
                except socket.timeout:
                    # Si hay timeout, puede que sea un evento
                    if response and "notify" in response:
                        # Es un evento, procesarlo
                        self.handle_event(response)
                        response = ""
                        continue
                    break
            
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Error enviando comando: {e}")
            return None
    

    
    def connect(self):
        """Conectar al servidor TeamSpeak 3"""
        try:
            self.logger.info(f"Conectando a {TS3_HOST}:{TS3_QUERY_PORT}...")
            
            # Crear socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            
            # Conectar
            self.socket.connect((TS3_HOST, TS3_QUERY_PORT))
            
            # Leer mensaje de bienvenida
            welcome = self.socket.recv(1024).decode('utf-8')
            self.logger.info(f"Mensaje de bienvenida: {welcome.strip()}")
            
            # Autenticar
            self.logger.info(f"Autenticando con usuario: {TS3_USERNAME}")
            auth_response = self.send_command(f"login {TS3_USERNAME} {TS3_PASSWORD}")
            
            if auth_response and "error id=0" in auth_response:
                self.logger.info("✅ Autenticación exitosa")
            else:
                self.logger.error(f"❌ Error de autenticación: {auth_response}")
                return False
            
            # Verificar en qué servidor estamos (para usuarios server bound no necesitamos cambiar)
            whoami_response = self.send_command("whoami")
            if whoami_response and "error id=0" in whoami_response:
                self.logger.info("✅ Usuario server bound - usando servidor asignado")
                # Extraer información del servidor actual
                if "virtualserver_id=" in whoami_response:
                    for part in whoami_response.split():
                        if part.startswith("virtualserver_id="):
                            self.server_id = part.split("=")[1]
                            self.logger.info(f"📍 Usando servidor virtual ID: {self.server_id}")
                        elif part.startswith("client_id="):
                            self.bot_client_id = part.split("=")[1]
                            self.logger.info(f"🤖 ID del bot: {self.bot_client_id}")
            else:
                self.logger.warning("⚠️ No se pudo verificar información del usuario, continuando...")
            
            # Registrar eventos para escuchar comandos
            self.register_events()
            
            self.connected = True
            self.reconnect_attempts = 0
            
            # Mostrar información del servidor
            self.show_server_info()
            
            # Los eventos se procesarán en el bucle principal
            self.logger.info("🎧 Sistema de comandos activado")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error de conexión: {e}")
            self.connected = False
            return False
    
    def show_server_info(self):
        """Mostrar información básica del servidor"""
        try:
            # Obtener información del servidor
            server_info = self.send_command("serverinfo")
            
            if server_info and "error id=0" in server_info:
                print("\n" + "="*50)
                print("📊 INFORMACIÓN DEL SERVIDOR")
                print("="*50)
                
                # Parsear información básica
                lines = server_info.split('\n')
                for line in lines:
                    if line.startswith('virtualserver_name='):
                        name = line.split('=', 1)[1]
                        print(f"🏷️  Nombre: {name}")
                    elif line.startswith('virtualserver_clientsonline='):
                        clients = line.split('=', 1)[1]
                        print(f"👥 Clientes conectados: {clients}")
                    elif line.startswith('virtualserver_maxclients='):
                        max_clients = line.split('=', 1)[1]
                        print(f"📊 Máximo de clientes: {max_clients}")
                
                print("="*50)
                
                # Mostrar lista de clientes conectados
                self.show_connected_clients()
                
                # Mostrar comandos disponibles
                print("\n🎮 COMANDOS DISPONIBLES:")
                print("-" * 30)
                print("  !mp - Enviar poke a todos los usuarios")
                print("  !mm - Mover todos al canal del comando")
                print("  !mk - Expulsar a todos del servidor")
                print("  !test - Ver lista de usuarios (debug)")
                print("-" * 30)
                
        except Exception as e:
            self.logger.error(f"Error al obtener información del servidor: {e}")
    
    def show_connected_clients(self):
        """Mostrar lista de clientes conectados"""
        try:
            clients_info = self.send_command("clientlist")
            
            if clients_info and "error id=0" in clients_info:
                print("\n👥 CLIENTES CONECTADOS:")
                print("-" * 30)
                
                # Parsear lista de clientes usando el mismo método que get_all_clients
                if "clid=" in clients_info:
                    client_blocks = clients_info.split("clid=")[1:]
                    
                    for block in client_blocks:
                        client_data = {}
                        parts = block.split()
                        if parts:
                            client_data['clid'] = parts[0]
                            
                            for part in parts:
                                if '=' in part:
                                    key, value = part.split('=', 1)
                                    client_data[key] = value
                        
                        client_name = client_data.get('client_nickname', 'Desconocido')
                        client_id = client_data.get('clid', 'N/A')
                        client_type = client_data.get('client_type', '0')
                        
                        # Mostrar todos los usuarios reales (client_type = 0)
                        if client_type == '0':
                            print(f"  👤 {client_name} (ID: {client_id})")
                
                print("-" * 30)
                
        except Exception as e:
            self.logger.error(f"Error al obtener lista de clientes: {e}")
    
    def register_events(self):
        """Registrar eventos para escuchar comandos en el chat"""
        try:
            # Registrar eventos de chat del servidor
            self.send_command("servernotifyregister event=textserver")
            # Registrar eventos de chat de canal
            self.send_command("servernotifyregister event=textchannel")
            # Registrar eventos de chat privado
            self.send_command("servernotifyregister event=textprivate")
            
            self.listening_events = True
            self.logger.info("✅ Eventos registrados - escuchando comandos")
            
        except Exception as e:
            self.logger.error(f"Error registrando eventos: {e}")
    
    def get_all_clients(self):
        """Obtener lista de todos los clientes conectados (excluyendo solo el bot actual)"""
        try:
            clients_info = self.send_command("clientlist")
            clients = []
            
            self.logger.info(f"Debug - Respuesta clientlist: {clients_info}")
            
            if clients_info and "error id=0" in clients_info:
                # Parsear respuesta que puede venir en una sola línea con múltiples clientes
                if "clid=" in clients_info:
                    # Dividir por clid= para obtener cada cliente
                    client_blocks = clients_info.split("clid=")[1:]  # Ignorar la parte antes del primer clid=
                    
                    for block in client_blocks:
                        client_data = {}
                        # El primer valor es el ID del cliente
                        parts = block.split()
                        if parts:
                            client_data['clid'] = parts[0]
                            
                            # Procesar el resto de los parámetros
                            for part in parts:
                                if '=' in part:
                                    key, value = part.split('=', 1)
                                    client_data[key] = value
                        
                        self.logger.info(f"Debug - Cliente encontrado: {client_data}")
                        
                        # Incluir todos los usuarios reales (client_type=0) excepto el bot actual
                        if (client_data.get('client_type') == '0' and 
                            client_data.get('clid') != self.bot_client_id):
                            clients.append(client_data)
                            self.logger.info(f"Debug - Cliente agregado: {client_data.get('client_nickname')} (ID: {client_data.get('clid')})")
            
            self.logger.info(f"Debug - Total clientes válidos encontrados: {len(clients)}")
            return clients
            
        except Exception as e:
            self.logger.error(f"Error obteniendo lista de clientes: {e}")
            return []
    
    def command_mass_poke(self, invoker_id, channel_id):
        """Comando !mp - Enviar poke a todos los usuarios"""
        try:
            clients = self.get_all_clients()
            poked_count = 0
            
            for client in clients:
                client_id = client.get('clid')
                client_name = client.get('client_nickname', 'Desconocido')
                
                if client_id:
                    # Enviar poke al cliente
                    poke_response = self.send_command(f"clientpoke clid={client_id} msg=¡Poke\smásivo\sdel\sbot!")
                    
                    if poke_response and "error id=0" in poke_response:
                        poked_count += 1
                        self.logger.info(f"👉 Poke enviado a {client_name}")
                    else:
                        self.logger.warning(f"❌ No se pudo hacer poke a {client_name}")
            
            self.logger.info(f"✅ Comando !mp ejecutado - {poked_count} usuarios recibieron poke")
            
        except Exception as e:
            self.logger.error(f"Error ejecutando comando !mp: {e}")
    
    def command_mass_move(self, invoker_id, channel_id):
        """Comando !mm - Mover todos los usuarios al canal del comando"""
        try:
            clients = self.get_all_clients()
            moved_count = 0
            
            for client in clients:
                client_id = client.get('clid')
                client_name = client.get('client_nickname', 'Desconocido')
                current_channel = client.get('cid')
                
                # Solo mover si no está ya en el canal de destino
                if client_id and current_channel != channel_id:
                    move_response = self.send_command(f"clientmove clid={client_id} cid={channel_id}")
                    
                    if move_response and "error id=0" in move_response:
                        moved_count += 1
                        self.logger.info(f"🚶 {client_name} movido al canal {channel_id}")
                    else:
                        self.logger.warning(f"❌ No se pudo mover a {client_name}")
            
            self.logger.info(f"✅ Comando !mm ejecutado - {moved_count} usuarios movidos")
            
        except Exception as e:
            self.logger.error(f"Error ejecutando comando !mm: {e}")
    
    def command_mass_kick(self, invoker_id, channel_id):
        """Comando !mk - Kick a todos los usuarios del servidor"""
        try:
            clients = self.get_all_clients()
            kicked_count = 0
            
            for client in clients:
                client_id = client.get('clid')
                client_name = client.get('client_nickname', 'Desconocido')
                
                if client_id:
                    # Kick del servidor (reasonid=5 = kick del servidor)
                    kick_response = self.send_command(f"clientkick clid={client_id} reasonid=5 reasonmsg=Kick\smásivo\sdel\sbot")
                    
                    if kick_response and "error id=0" in kick_response:
                        kicked_count += 1
                        self.logger.info(f"👢 {client_name} expulsado del servidor")
                    else:
                        self.logger.warning(f"❌ No se pudo expulsar a {client_name}")
            
            self.logger.info(f"✅ Comando !mk ejecutado - {kicked_count} usuarios expulsados")
            
        except Exception as e:
            self.logger.error(f"Error ejecutando comando !mk: {e}")
    
    def command_test_clients(self, invoker_id, channel_id):
        """Comando !test - Mostrar información de clientes para debugging"""
        try:
            self.logger.info("🔍 Ejecutando comando de test...")
            clients = self.get_all_clients()
            
            self.logger.info(f"📋 Clientes encontrados para comandos: {len(clients)}")
            for client in clients:
                self.logger.info(f"  - {client.get('client_nickname', 'Sin nombre')} (ID: {client.get('clid')}, Tipo: {client.get('client_type')})")
            
        except Exception as e:
            self.logger.error(f"Error ejecutando comando !test: {e}")
    
    def process_command(self, message, invoker_id, channel_id):
        """Procesar comandos recibidos en el chat"""
        try:
            # Limpiar mensaje y extraer solo el comando base
            clean_message = message.strip().lower()
            
            # Extraer solo el primer palabra (el comando) ignorando argumentos adicionales
            command = clean_message.split()[0] if clean_message else ""
            
            self.logger.info(f"Debug - Mensaje completo: '{clean_message}'")
            self.logger.info(f"Debug - Comando extraído: '{command}'")
            self.logger.info(f"Debug - Comandos disponibles: {list(self.commands.keys())}")
            
            if command in self.commands:
                command_func = self.commands[command]
                self.logger.info(f"🎯 Ejecutando comando: {command} por cliente {invoker_id}")
                command_func(invoker_id, channel_id)
            else:
                self.logger.info(f"⚠️ Comando no reconocido: {command}")
            
        except Exception as e:
            self.logger.error(f"Error procesando comando: {e}")
    
    def handle_event(self, event_data):
        """Manejar eventos recibidos del servidor"""
        try:
            self.logger.info(f"Debug - Evento recibido: {event_data}")
            
            if "notifytextmessage" in event_data:
                # Parsear evento de mensaje de texto
                parts = event_data.split()
                
                invoker_id = None
                message = None
                channel_id = None
                target_mode = None
                invoker_name = None
                
                for part in parts:
                    if part.startswith("invokerid="):
                        invoker_id = part.split("=")[1]
                    elif part.startswith("msg="):
                        message = part.split("=", 1)[1].replace("\\s", " ")
                    elif part.startswith("targetmode="):
                        target_mode = part.split("=")[1]
                        # targetmode=1 = privado, targetmode=2 = canal, targetmode=3 = servidor
                    elif part.startswith("target="):
                        channel_id = part.split("=")[1]
                    elif part.startswith("invokername="):
                        invoker_name = part.split("=", 1)[1]
                
                self.logger.info(f"Debug - Mensaje procesado: {message} de {invoker_name} (ID: {invoker_id})")
                
                # Procesar comando si viene de otro cliente (no del bot)
                if (invoker_id and message and invoker_id != self.bot_client_id and 
                    message.startswith("!")):
                    self.logger.info(f"Debug - Procesando comando: {message}")
                    self.process_command(message, invoker_id, channel_id)
                    
        except Exception as e:
            self.logger.error(f"Error manejando evento: {e}")
    
    def disconnect(self):
        """Desconectar del servidor"""
        if self.socket:
            try:
                self.send_command("logout")
                self.socket.close()
                self.logger.info("🔌 Desconectado del servidor")
            except Exception as e:
                self.logger.error(f"Error al desconectar: {e}")
            finally:
                self.connected = False
                self.socket = None
    
    def is_connected(self):
        """Verificar si la conexión está activa"""
        if not self.connected or not self.socket:
            return False
        
        try:
            # Hacer una consulta simple para verificar la conexión
            response = self.send_command("whoami")
            return response and "error id=0" in response
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
        self.logger.info("🚀 Iniciando bot simple de TeamSpeak 3...")
        
        # Conectar inicialmente
        if not self.connect():
            self.logger.error("❌ No se pudo establecer la conexión inicial")
            return
        
        self.logger.info("✅ Bot conectado y ejecutándose...")
        self.logger.info("Presiona Ctrl+C para detener el bot")
        
        try:
            last_keepalive = time.time()
            
            while True:
                current_time = time.time()
                
                # Verificar si hay eventos pendientes
                try:
                    self.socket.settimeout(0.1)  # Timeout muy corto para no bloquear
                    data = self.socket.recv(4096).decode('utf-8')
                    if data and "notify" in data:
                        self.handle_event(data.strip())
                except socket.timeout:
                    pass  # No hay eventos, continuar
                except Exception:
                    pass  # Error menor, continuar
                
                # Verificar conexión cada 60 segundos
                if current_time - last_keepalive > 60:
                    if not self.is_connected():
                        self.logger.warning("⚠️  Conexión perdida, intentando reconectar...")
                        if not self.reconnect():
                            self.logger.error("❌ No se pudo reconectar. Deteniendo bot.")
                            break
                    
                    last_keepalive = current_time
                    
                    # Mostrar estado cada 5 minutos
                    if current_time % 300 < 60:
                        self.logger.info("💚 Bot funcionando correctamente...")
                
                # Pausa corta para no consumir mucho CPU
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Deteniendo bot por solicitud del usuario...")
        except Exception as e:
            self.logger.error(f"❌ Error inesperado: {e}")
        finally:
            self.disconnect()
            self.logger.info("👋 Bot detenido")