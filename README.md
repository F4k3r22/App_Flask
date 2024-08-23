### Documentación Detallada de la Aplicación Flask

#### 1. **Configuración y Dependencias**
   - **Flask**: Framework para manejar rutas y lógica web.
   - **Flask-MySQLdb**: Conecta la aplicación con una base de datos MySQL.
   - **Stripe**: Gestiona los pagos dentro de la aplicación.
   - **Otros Módulos**: `PIL` para manejo de imágenes, `requests` para realizar solicitudes HTTP, y `os`, `time` y `random` para funcionalidades adicionales.

### Instalación 

   ```bash
pip install flask flask-mysqldb requests pillow stripe
```

#### 2. **Rutas Principales**
   - **`/`**: Página principal que muestra los créditos restantes del usuario.
   - **`/login` y `/register`**: Rutas para iniciar sesión y registrarse.
   - **`/generate`**: Permite a los usuarios generar imágenes usando una API externa (Rendernet).
   - **`/buy_credits` y `/purchase_credits`**: Gestionan la compra de créditos usando Stripe.
   - **`/payment_success`**: Actualiza los créditos del usuario después de una compra exitosa.

#### 3. **Gestión de Créditos**
   - **Validación de Créditos**: Antes de generar una imagen, se verifica si el usuario tiene créditos disponibles.
   - **Actualización de Créditos**: Después de la generación de imágenes o la compra de créditos, la base de datos se actualiza.

#### 4. **Integración con Stripe**
   - **`purchase_credits`**: Crea una sesión de pago en Stripe y redirige al usuario a la página de pago.
   - **`payment_success`**: Actualiza los créditos del usuario tras una compra exitosa y lo redirige a la página de confirmación.

#### 5. **Manejo de Imágenes**
   - **Carga y Procesamiento de Imágenes**: Los usuarios pueden subir imágenes (por ejemplo, para usar FaceLock), las cuales son procesadas y enviadas a la API de Rendernet para generar nuevas imágenes.

#### 6. **Seguridad**
   - **Manejo de Sesiones**: Asegura que solo usuarios autenticados puedan acceder a funciones como generación de imágenes y compra de créditos.
   - **Almacenamiento Seguro**: La clave secreta de Stripe y otras configuraciones sensibles se almacenan de manera segura.

#### 7. **Otras Funcionalidades**
   - **Prompts Generados Dinámicamente**: Basado en el género del usuario, se generan prompts personalizados para LinkedIn o Instagram.
   - **Control de Límite Diario**: Implementa un límite de generación de imágenes cada 24 horas.

### 8. **Obtención y configuración de las API de RenderNet**
  - **Configuración de la clave API y la descarga de imagenes:** Nos vamos a la función `@app.route('/generate', methods=['POST'])
def generate_image():`
y modificamos el `api_key = 'Your_API_Key'` y ponemos nuestra clave API de RenderNet.

**Lanzamos la App en modo desarrollador:** modificando la ultima linea para que quede asi `aapp.run(debug=true host='0.0.0.0' port=5000)` y probamos la generación, va obtener un error, pero lo importante es que mande la petición al servidor de RenderNet.

**Obtener el user_id del servidor de RenderNet:** Despues de mandar la petición vamos a [Listar Generaciones](https://docs.rendernet.ai/api-reference/endpoint/generations/list_generations) vamos a ver una página algo asi, pon tu API Key en el Header, y le das a Send, deberias ver la generación que haz mandado al servidor.

![Img](api.PNG)

**Aca vas a buscar el campo url**
![Img](api2.PNG)

De este campo vas a copiar el `usr_jFREal2mBT` de la URL `https://redernet-image-data.s3.amazonaws.com/prod/user_generated/usr_jFREal2mBT/img_0qCkaxZ79t.png` (en tu caso sera diferente)

Y despues de copiar el user id, lo vas a pegar aqui donde dice `user_id` en esta linea, para obtener correctemente cada imagen generada: `image_url = f"https://redernet-image-data.s3.amazonaws.com/prod/user_generated/user_id/{image_id}.png"`

### **Despues de estos ajustes ya puedes ir a desplegar producción :b**



### Desplegar a producción

#### 1. **Instalación y Configuración**
##### 1.1. **Requisitos Previos**
- Python 3.x
- MySQL
- Nginx (para producción)
- Pip para instalar dependencias

##### 1.2. **Instalación de Dependencias**
```bash
pip install flask flask-mysqldb requests pillow stripe
```

##### 1.3. **Configuración de la Base de Datos**
Crea una base de datos MySQL con el siguiente script, igual puedes cambiar el nombre de la base de datos si inifinityca no te convence:

```sql
CREATE DATABASE infinityca;
USE infinityca;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    pno VARCHAR(20),
    password VARCHAR(100),
    user_id VARCHAR(10) UNIQUE,
    last_generation_date DATETIME,
    image_generations_remaining INT DEFAULT 5,
    gender VARCHAR(10)
);
```

#### 2. **Despliegue en Producción**
##### 2.1. **Configuración de Nginx**
Configura Nginx como un reverse proxy para tu aplicación Flask.

```nginx
server {
    listen 80;
    server_name your_domain_or_IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        include proxy_params;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

##### 2.2. **Iniciar la Aplicación**
Usa `gunicorn` para ejecutar la aplicación en producción:

```bash
gunicorn --workers 3 app:app
```

#### 3. **Mantenimiento y Seguridad**
- **Seguridad**: Asegúrate de que las configuraciones de las claves API sean seguras.
- **SSL**: Configura un certificado SSL en Nginx para asegurar las conexiones.