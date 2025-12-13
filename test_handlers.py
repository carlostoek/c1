#!/usr/bin/env python3
"""Test que los handlers de usuario están registrados."""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/repos/c1')

from bot.handlers.user import user_router

print("=== Test de Handlers de Usuario ===\n")

# Obtener todos los handlers del router
message_handlers = []
callback_handlers = []

# Revisar los observers del router
for update_type, observer in user_router.observers.items():
    if update_type == 'message':
        # Extraer handlers de message
        if hasattr(observer, '_handlers'):
            message_handlers = observer._handlers
    elif update_type == 'callback_query':
        # Extraer handlers de callback
        if hasattr(observer, '_handlers'):
            callback_handlers = observer._handlers

print(f"Message handlers: {len(message_handlers)}")
print(f"Callback handlers: {len(callback_handlers)}")
print()

# Buscar específicamente los callbacks que necesitamos
print("Buscando callbacks específicos:")
expected_callbacks = [
    'user:redeem_token',
    'user:request_free', 
    'user:cancel'
]

for expected in expected_callbacks:
    found = False
    for handler in callback_handlers:
        # Revisar los filtros del handler
        if hasattr(handler, 'filters'):
            for filter_item in handler.filters:
                if hasattr(filter_item, 'data') and filter_item.data == expected:
                    found = True
                    break
        if found:
            break
    
    status = "✅" if found else "❌"
    print(f"{status} {expected}")

print("\nTest completado!")
