import requests

FIREBASE_PROJECT_ID = "blockdata-8efc5"
FIREBASE_API_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"
REGISTERED_USERS = set()  # Usamos un conjunto para evitar duplicados


class Usuario:

    def check_user_exists(user_id):
        """Verifica si el usuario ya existe en Firestore utilizando el user_id."""
        # URL para hacer la consulta en Firestore usando runQuery
        url = f"{FIREBASE_API_URL}:runQuery"

        # print("User ID:", user_id)
        # Construir la consulta structuredQuery
        query = {
            "structuredQuery": {
                "from": [{"collectionId": "usuarios", "allDescendants": False}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "user_id"},
                        "op": "EQUAL",
                        "value": {"stringValue": str(user_id)},
                    }
                },
            }
        }

        # Hacemos la solicitud POST para verificar la existencia del usuario
        response = requests.post(url, json=query)

        if response.status_code == 200:
            # Si la respuesta contiene datos, significa que el usuario existe
            data = response.json()
            REGISTERED_USERS.add(user_id)

            # print(data)

            # Verificamos si la respuesta contiene el campo 'document'
            if len(data) > 0 and "document" in data[0]:
                return True  # Usuario encontrado
            else:
                return False  # No se encontraron resultados
        else:
            # print(f"Error al verificar el usuario: {response.status_code}, {response.text}")
            return False

    def save_user_to_firestore(user_id, url_user, name_user, creditos, registro_fecha):
        """Guardar los detalles del usuario en Firestore si no existe."""
        # Verificar si el usuario ya existe
        if Usuario.check_user_exists(user_id):
            # print("El usuario ya existe.")
            REGISTERED_USERS.add(user_id)
            return False

        # Si no existe, guardar el nuevo usuario
        data = {
            "fields": {
                "user_id": {"stringValue": str(user_id)},  # Convertir a cadena
                "url_user": {"stringValue": url_user},
                "name_user": {"stringValue": name_user},
                "creditos": {"integerValue": creditos},  # Guardar como entero
                "registro_fecha": {"stringValue": registro_fecha},
            }
        }

        # Construir la URL para agregar el documento a la colección "usuarios"
        url = f"{FIREBASE_API_URL}/usuarios"

        # Realizar la solicitud POST para guardar el usuario
        response = requests.post(url, json=data)

        if response.status_code == 200:
            # print("Usuario registrado correctamente en Firestore")
            REGISTERED_USERS.add(user_id)
            return True
        else:
            # print(f"Error al guardar los detalles del usuario: {response.status_code}, {response.text}")
            return False

    def save_to_firestore(
        id_adm, name_adm, url_adm, id_client, name_client, url_client, hora, numero
    ):
        """Guardar detalles en Firestore cuando se confirme el bloqueo"""
        data = {
            "fields": {
                "id_adm": {"stringValue": str(id_adm)},  # Convertir a cadena
                "name_adm": {"stringValue": name_adm},
                "url_adm": {"stringValue": url_adm},
                # Convertir a cadena
                "id_client": {"stringValue": str(id_client)},
                "name_client": {"stringValue": name_client},
                "url_client": {"stringValue": url_client},
                "hora": {"stringValue": hora},
                "numero": {"stringValue": str(numero)},  # Convertir a cadena
            }
        }

        # Construir la URL para agregar el documento a la colección "bloqueos"
        url = f"{FIREBASE_API_URL}/bloqueos"

        # Realizar la solicitud POST a Firebase Firestore
        response = requests.post(url, json=data)

        if response.status_code == 200:
            Usuario.restar_creditos(id_client, 15)
            # print("Detalles guardados correctamente en Firestore")
        # else:
        # print(f"Error al guardar los detalles: {response.status_code}, {response.text}")

    def get_creditos(user_id):
        """Obtiene los créditos de un usuario desde Firestore utilizando su user_id."""
        # URL para hacer la consulta en Firestore usando runQuery
        url = f"{FIREBASE_API_URL}:runQuery"

        # Construir la consulta structuredQuery
        query = {
            "structuredQuery": {
                "from": [{"collectionId": "usuarios", "allDescendants": False}],
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "user_id"},
                        "op": "EQUAL",
                        "value": {"stringValue": str(user_id)},
                    }
                },
            }
        }

        # Hacemos la solicitud POST para consultar el usuario
        response = requests.post(url, json=query)

        if response.status_code == 200:
            # Si la respuesta contiene datos, significa que el usuario existe
            data = response.json()

            # Verificamos si la respuesta contiene el campo 'document'
            if len(data) > 0 and "document" in data[0]:
                # Extraemos los créditos desde el documento
                document = data[0]["document"]
                creditos = (
                    document["fields"].get("creditos", {}).get("integerValue", 0)
                )  # 0 si no existe
                # print("Creditos: ", creditos)
                return creditos
            else:
                # print("Usuario no encontrado.")
                return None
        else:
            # print(f"Error al obtener los créditos: {response.status_code}, {response.text}")
            return None

    def restar_creditos(user_id, cantidad):
        """Restar créditos del usuario en Firestore y actualizar el valor."""

        # Preparar el cuerpo de la consulta para obtener el documento con el campo `user_id`
        query = {
            "structuredQuery": {
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "user_id"},
                        "op": "EQUAL",
                        "value": {"stringValue": user_id},
                    }
                },
                "from": [{"collectionId": "usuarios", "allDescendants": False}],
            }
        }

        # URL de la API REST de Firestore para realizar la consulta
        query_url = f"{FIREBASE_API_URL}:runQuery"

        # Realizar la solicitud POST para realizar la consulta
        response = requests.post(query_url, json=query)

        if response.status_code != 200:
            # print(f"Error al buscar el documento del usuario: {response.status_code}, {response.text}")
            return False

        data = response.json()

        # Verificar si el documento fue encontrado
        if not data:
            # print(f"No se encontró un usuario con el user_id {user_id}.")
            return False

        # Obtener el ID del documento encontrado (en Firestore el ID del documento es diferente del user_id)
        document_id = data[0]["document"]["name"].split("/")[-1]
        document_fields = data[0]["document"]["fields"]
        # Obtener los créditos actuales del usuario
        creditos = document_fields.get("creditos", {}).get("integerValue", None)
        url_user = document_fields.get("url_user", {}).get("stringValue", "")
        name_user = document_fields.get("name_user", {}).get("stringValue", "")

        registro_fecha = document_fields.get("registro_fecha", {}).get(
            "stringValue", ""
        )

        if creditos is None:
            # print(f"El usuario {user_id} no tiene créditos registrados.")
            return False

        # Restar los créditos
        nuevos_creditos = int(creditos) - cantidad

        if nuevos_creditos < 0:
            # print("No tienes suficientes créditos para realizar esta acción.")
            return False

        # Preparar los datos para la actualización
        data_update = {
            "fields": {
                "user_id": {"stringValue": str(user_id)},
                "url_user": {"stringValue": url_user},
                "name_user": {"stringValue": name_user},
                "creditos": {"integerValue": nuevos_creditos},  # Guardar como entero
                "registro_fecha": {"stringValue": registro_fecha},
            }
        }

        # URL para actualizar el documento de usuario en Firestore usando el ID encontrado
        update_url = f"{FIREBASE_API_URL}/usuarios/{document_id}"

        # Realizar la solicitud PATCH para actualizar los créditos
        update_response = requests.patch(update_url, json=data_update)

        if update_response.status_code == 200:
            # print(f"Se han restado {cantidad} créditos del usuario {user_id}. Nuevos créditos: {nuevos_creditos}")
            return True
        else:
            # print(f"Error al actualizar los créditos: {update_response.status_code}, {update_response.text}")
            return False

    def agg_creditos(user_id, cantidad):
        """Restar créditos del usuario en Firestore y actualizar el valor."""

        # Preparar el cuerpo de la consulta para obtener el documento con el campo `user_id`
        query = {
            "structuredQuery": {
                "where": {
                    "fieldFilter": {
                        "field": {"fieldPath": "user_id"},
                        "op": "EQUAL",
                        "value": {"stringValue": user_id},
                    }
                },
                "from": [{"collectionId": "usuarios", "allDescendants": False}],
            }
        }

        # URL de la API REST de Firestore para realizar la consulta
        query_url = f"{FIREBASE_API_URL}:runQuery"

        # Realizar la solicitud POST para realizar la consulta
        response = requests.post(query_url, json=query)

        if response.status_code != 200:
            # print(f"Error al buscar el documento del usuario: {response.status_code}, {response.text}")
            return False

        data = response.json()

        # Verificar si el documento fue encontrado
        if not data:
            # print(f"No se encontró un usuario con el user_id {user_id}.")
            return False

        # Obtener el ID del documento encontrado (en Firestore el ID del documento es diferente del user_id)
        document_id = data[0]["document"]["name"].split("/")[-1]
        document_fields = data[0]["document"]["fields"]
        # Obtener los créditos actuales del usuario
        creditos = document_fields.get("creditos", {}).get("integerValue", None)
        url_user = document_fields.get("url_user", {}).get("stringValue", "")
        name_user = document_fields.get("name_user", {}).get("stringValue", "")

        registro_fecha = document_fields.get("registro_fecha", {}).get(
            "stringValue", ""
        )

        if creditos is None:
            # print(f"El usuario {user_id} no tiene créditos registrados.")
            return False

        # Restar los créditos
        nuevos_creditos = int(creditos) + cantidad

        if nuevos_creditos < 0:
            # print("No tienes suficientes créditos para realizar esta acción.")
            return False

        # Preparar los datos para la actualización
        data_update = {
            "fields": {
                "user_id": {"stringValue": str(user_id)},
                "url_user": {"stringValue": url_user},
                "name_user": {"stringValue": name_user},
                "creditos": {"integerValue": nuevos_creditos},  # Guardar como entero
                "registro_fecha": {"stringValue": registro_fecha},
            }
        }

        # URL para actualizar el documento de usuario en Firestore usando el ID encontrado
        update_url = f"{FIREBASE_API_URL}/usuarios/{document_id}"

        # Realizar la solicitud PATCH para actualizar los créditos
        update_response = requests.patch(update_url, json=data_update)

        if update_response.status_code == 200:
            # print(f"Se han restado {cantidad} créditos del usuario {user_id}. Nuevos créditos: {nuevos_creditos}")
            return True
        else:
            # print(f"Error al actualizar los créditos: {update_response.status_code}, {update_response.text}")
            return False
