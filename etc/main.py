# main.py
import uuid
from datetime import datetime
import repo
from repo import ValidationError

def demo():
    try:
        uid = str(uuid.uuid4())

        # Crear
        repo.crear_personal_client(
            client_uuid=uid,
            personal_identification="A-12345678",
            first_name="Adriana",
            last_name="Gómez",
            email="adriana@example.com",
            phone_number="+507 6000-0000",
            registration_date=datetime.now()
        )
        print("✔ Registro insertado:", uid)

        # Leer
        fila = repo.buscar_personal_client_por_uuid(uid)
        print("✔ Buscado por UUID:", fila)

        # Actualizar
        filas = repo.actualizar_email(uid, "adri.gomez@example.com")
        print(f"✔ Email actualizado (filas afectadas: {filas})")

        # Listar
        clientes = repo.obtener_todos_personal_client(5)
        print("✔ Últimos clientes:")
        for c in clientes:
            print("  ", c)

        # Borrar (opcional)
        # repo.borrar_personal_client(uid)

    except ValidationError as ve:
        print("❌ Error de validación:", ve)
    except Exception as e:
        print("❌ Error inesperado:", e)

if __name__ == "__main__":
    demo()
