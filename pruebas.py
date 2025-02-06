from datetime import datetime, time
import pytz

# Define la zona horaria
peru_tz = pytz.timezone('America/Lima')

# Obtén la hora actual
current_time = datetime.now(peru_tz).time()

# Imprime la hora para verificar
print("Hora actual:", current_time)
