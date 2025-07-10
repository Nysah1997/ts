#!/usr/bin/env python3
"""
Punto de entrada principal para el bot de TeamSpeak 3
"""

import sys
import os
from simple_bot import SimpleTeamSpeakBot

def main():
    """Función principal"""
    print("="*60)
    print("🎮 BOT DE TEAMSPEAK 3 - SERVERQUERY")
    print("="*60)
    print(f"🌐 Servidor: 142.4.207.51:20131")
    print(f"🔌 Puerto Query: 10002")
    print(f"👤 Usuario: bote")
    print("="*60)
    
    # Crear e iniciar el bot
    bot = SimpleTeamSpeakBot()
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n🛑 Interrumpido por el usuario")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
