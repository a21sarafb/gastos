# App de Gestión de Gastos Compartidos

Aplicación web desarrollada con Django para gestionar gastos compartidos entre dos personas, con reparto proporcional configurable según sus ingresos. Diseñada para futuras ampliaciones con IA/ML.

## Funcionalidades
- Gestión de usuarios: registro e inicio de sesión seguro mediante Django, con perfiles asociados a cada persona.
- Porcentajes de aportación: cada usuario tiene asignado un porcentaje (por defecto 63 % y 37 %), usado para repartir ingresos y gastos.
- Fondos comunes configurables: podéis definir fondos para "Supermercado", "Gastos del piso", "Viajes", "Compras del piso" y "Ahorro de pareja". Cada fondo recibe una aportación mensual y descuenta automáticamente los gastos de su categoría.
- Seguimiento del saldo y aportaciones: el panel de fondos muestra cuánto dinero queda en cada fondo, la cantidad aportada este mes y la contribución individual de cada persona.
- Registro de ingresos y gastos: formulario para registrar operaciones con fecha, importe, descripción y categoría (asociada a un fondo o gasto personal).
- Historial y división proporcional: visualización de todas las transacciones y división automática de los gastos comunes según los porcentajes.
- Dashboard de resumen: página con gráficas interactivas (Chart.js) que muestran la distribución mensual de gastos por categoría y la evolución de gastos de los últimos meses.
- Interfaz moderna y adaptable: diseño basado en Bootstrap con tonos pastel rojo/rosa y optimizado para su uso en móviles y como aplicación PWA.
- Panel de administración: gestión de usuarios, fondos y gastos desde el administrador de Django.

## 🛠 Tecnologías usadas
- Backend: Python 3.13 y Django 5.2 (compatible con Python 3.11 en producción).
- Base de datos: SQLite en desarrollo y PostgreSQL en producción (mediante Koyeb).
- Frontend: HTML5, CSS3, Bootstrap 5 con tema personalizado en tonos pastel; plantillas de Django.
- Gráficas: Chart.js para los dashboards de gastos mensuales.
- Servidor WSGI: Gunicorn con WhiteNoise para servir archivos estáticos en producción.
- Despliegue: Koyeb (plan gratuito con un servicio web y una base de datos Postgres).

## ⚙ Instalación local
1. Clona el repositorio  
   ```bash
   git clone https://github.com/a21sarafb/gastos
   cd gastos-compartidos
   ```
2. Crea entorno virtual  
   ```bash
   python -m venv env
   env\Scripts\activate # En Windows
   # source env/bin/activate # En Linux/macOS
   ```
3. Instala dependencias  
   ```bash
   pip install -r requirements.txt
   ```
   Si aún no tienes requirements.txt , puedes generarlo con:  
   ```bash
   pip freeze > requirements.txt
   ```
4. Aplica migraciones y ejecuta servidor  
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```
   Accede a <http://127.0.0.1:8000> desde tu navegador.

## ☁ Despliegue en Koyeb
1. Prepara el repositorio: asegúrate de tener en la raíz los ficheros `requirements.txt`, `Procfile` y `runtime.txt`.  
   - Procfile debe contener:  
     ```bash
     web: gunicorn gastos_project.wsgi:application --log-file -
     ```
   - En `runtime.txt` indica la versión de Python, por ejemplo:  
     ```
     python-3.11.0
     ```

2. Configura variables de entorno:  
   - `DJANGO_SECRET_KEY`: clave secreta aleatoria  
   - `DJANGO_DEBUG`: False en producción  
   - `DJANGO_ALLOWED_HOSTS`: el subdominio asignado por Koyeb (ej. miapp.koyeb.app)  
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`

3. Comandos de build y ejecución:  
   ```bash
   pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
   ```  
   Ejecución:  
   ```bash
   gunicorn gastos_project.wsgi:application --log-file -
   ```

4. Despliega y prueba: vincula tu repositorio de GitHub, selecciona la rama principal y despliega.  
   Koyeb descargará el código, instalará dependencias, aplicará migraciones, recopilará estáticos y publicará la aplicación en tu subdominio.

Con esta configuración podrás usar la aplicación desde cualquier dispositivo y ambos usuarios verán siempre el mismo saldo y las mismas transacciones.

## Crear usuarios de prueba
```python
from django.contrib.auth.models import User
u1 = User.objects.create_user(username='sara', password='1234')
u2 = User.objects.create_user(username='adri', password='1234')
u1.userprofile.porcentaje_actual = 63; u1.userprofile.save()
u2.userprofile.porcentaje_actual = 37; u2.userprofile.save()
```

## Acceso al panel de administración
```bash
python manage.py createsuperuser
```
Admin disponible en: <http://127.0.0.1:8000/admin/>

## Próximas funcionalidades
- Predicción de gastos con ML y análisis de tendencias.  
- Clasificación automática de gastos mediante modelos de IA.  
- Notificaciones cuando se superen los presupuestos establecidos en cada fondo.  

## Licencia
Este proyecto se publica bajo la licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente.

## Autoría
Desarrollado por Sara Facal Boullosa, 2025.  

---
**Pricing for intensive infractrucure - Koyeb**  
<https://www.koyeb.com/pricing>
