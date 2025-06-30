# 💸 App de Gestión de Gastos Compartidos

Aplicación web desarrollada con Django para gestionar gastos compartidos entre dos personas, con reparto proporcional configurable según sus ingresos. Accesible desde iPhone como PWA y diseñada para futuras ampliaciones con IA/ML.

---

## 🚀 Funcionalidades

- Registro e inicio de sesión de usuarios
- Asociación automática de perfiles con porcentaje de aportación
- Registro de gastos con fecha, categoría, descripción e importe
- División proporcional de los gastos en base a los porcentajes configurados
- Visualización de historial de gastos
- Cálculo de deuda entre ambos usuarios
- Interfaz responsiva compatible con iPhone
- Preparada para extensión con gráficos mensuales y análisis de IA

---

## 🛠️ Tecnologías usadas

- **Backend**: Python 3.13, Django 5.2
- **Base de datos**: SQLite (desarrollo) / PostgreSQL (producción)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Django templates
- **Gráficas (futuro)**: Chart.js
- **Despliegue (sugerido)**: PythonAnywhere, Render, Railway

---

## ⚙️ Instalación local

### 1. Clona el repositorio
```bash
git clone https://github.com/tuusuario/gastos-compartidos.git
cd gastos-compartidos
```

### 2. Crea entorno virtual
```bash
python -m venv env
env\Scripts\activate  # En Windows
# source env/bin/activate  # En Linux/macOS
```

### 3. Instala dependencias
```bash
pip install -r requirements.txt
```

> Si aún no tienes `requirements.txt`, puedes generarlo con:
```bash
pip freeze > requirements.txt
```

### 4. Aplica migraciones y ejecuta servidor
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Accede a `http://127.0.0.1:8000` desde tu navegador.

---

## 👥 Crear usuarios de prueba

Desde la shell de Django:

```python
from django.contrib.auth.models import User
u1 = User.objects.create_user(username='sara', password='1234')
u2 = User.objects.create_user(username='adri', password='1234')
u1.userprofile.porcentaje_actual = 56; u1.userprofile.save()
u2.userprofile.porcentaje_actual = 44; u2.userprofile.save()
```

---

## 📁 Estructura de carpetas

```
gastos_project/
├── core/
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   ├── urls.py
│   └── templates/core/
│       ├── base.html
│       ├── login.html
│       ├── registro.html
│       ├── lista_gastos.html
│       └── crear_gasto.html
├── gastos_project/
│   ├── settings.py
│   ├── urls.py
├── db.sqlite3
└── manage.py
```

---

## 🔐 Acceso al panel de administración

```bash
python manage.py createsuperuser
```

Admin disponible en: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 🧠 Próximas funcionalidades

- Dashboard con gráficos por mes y categoría
- Predicción de gastos con ML
- Clasificación automática de gastos
- Notificaciones por superación de presupuestos

---

## 📝 Licencia

Este proyecto se publica bajo la licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente.

---

## 💡 Autoría

Desarrollado por Sara Facal Boullosa, 2025.