# ThermoGuard IoT API

API RESTful para Sistema de Monitoramento Térmico de Data Center.

## 📋 Visão Geral

O ThermoGuard IoT é um sistema completo para monitoramento de temperatura e umidade em data centers, com controle automático de ar-condicionado via infravermelho utilizando dispositivos ESP32.

### Funcionalidades Principais

- 📊 **Dashboard em Tempo Real**: Monitoramento via WebSocket
- 🌡️ **Sensores DHT22/ESP32**: Coleta de temperatura e umidade
- ❄️ **Controle de AC**: Automação via sinais IR
- 🚨 **Sistema de Alertas**: Notificações automáticas
- 📈 **Relatórios**: Histórico e estatísticas

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Docker & Docker Compose (recomendado)

### Instalação com Docker

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/thermoguard_api.git
cd thermoguard_api

# Copie o arquivo de ambiente
cp env.example .env

# Inicie os containers
docker-compose up -d

# Execute as migrações
docker-compose exec api python manage.py migrate

# Crie um superusuário
docker-compose exec api python manage.py createsuperuser
```

### Instalação Manual

```bash
# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure o banco de dados e Redis
# Edite o arquivo .env com suas configurações

# Execute as migrações
python manage.py migrate

# Crie um superusuário
python manage.py createsuperuser

# Inicie o servidor
python manage.py runserver
```

## 📚 Documentação da API

Após iniciar o servidor, acesse:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin**: http://localhost:8000/admin/

## 🔐 Autenticação

### JWT (Para Dashboard)

```bash
# Login
POST /api/auth/login/
{
  "email": "usuario@email.com",
  "password": "senha123"
}

# Resposta
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": {...}
}

# Use o token nas requisições
Authorization: Bearer eyJ...
```

### API Key (Para ESP32)

```bash
# Header para dispositivos ESP32
X-API-Key: sua-chave-api
```

## 📡 Endpoints Principais

### Dashboard
- `GET /api/dashboard/` - Estado geral do sistema
- `GET /api/dashboard/rooms/{id}/` - Estado de uma sala

### Sensores
- `GET /api/sensors/` - Listar sensores
- `POST /api/sensors/{id}/readings/` - Enviar leitura (ESP32)
- `GET /api/sensors/{id}/readings/latest/` - Última leitura

### Ar-Condicionado
- `GET /api/air-conditioners/` - Listar ACs
- `POST /api/air-conditioners/{id}/turn-on/` - Ligar
- `POST /api/air-conditioners/{id}/turn-off/` - Desligar

### Alertas
- `GET /api/alerts/` - Listar alertas
- `PATCH /api/alerts/{id}/acknowledge/` - Reconhecer

## 🔌 WebSocket

### Conexão ao Dashboard

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/dashboard/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'sensor_reading':
      console.log('Nova leitura:', data.data);
      break;
    case 'ac_status_changed':
      console.log('Status AC:', data.data);
      break;
    case 'alert_triggered':
      console.log('Alerta:', data.data);
      break;
  }
};
```

### Sala Específica

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/room/{room_id}/');
```

## 📱 Integração ESP32

### Enviando Leituras

```cpp
// Exemplo em C++ para ESP32
HTTPClient http;
http.begin("http://api.thermoguard.local/api/sensors/readings/");
http.addHeader("Content-Type", "application/json");
http.addHeader("X-API-Key", API_KEY);

String payload = "{\"device_id\":\"" + WiFi.macAddress() + 
                 "\",\"temperature\":" + String(temp) + 
                 ",\"humidity\":" + String(humidity) + "}";

int httpCode = http.POST(payload);
```

## 🏗️ Estrutura do Projeto

```
thermoguard_api/
├── apps/
│   ├── core/           # Modelos base, utils, WebSocket consumers
│   ├── users/          # Autenticação e usuários
│   ├── sensors/        # Sensores e leituras
│   ├── devices/        # Ar-condicionado e IR
│   └── alerts/         # Sistema de alertas
├── config/             # Configurações Django
├── tests/              # Testes automatizados
├── nginx/              # Configuração Nginx
└── scripts/            # Scripts auxiliares
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=apps --cov-report=html

# Testes específicos
pytest tests/test_api.py -v
```

## 🐳 Docker

### Desenvolvimento

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Produção

```bash
docker-compose --profile production up -d
```

## ⚙️ Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `SECRET_KEY` | Chave secreta Django | - |
| `DEBUG` | Modo debug | `False` |
| `DB_HOST` | Host PostgreSQL | `localhost` |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379/0` |
| `ESP32_API_KEY` | Chave API para ESP32 | - |
| `CORS_ALLOWED_ORIGINS` | Origens CORS permitidas | - |

## 📊 Lógica de Automação

### Modo Automático

- Temperatura > setpoint + 1°C → Liga AC
- Temperatura < setpoint - 1°C → Desliga AC
- Histerese de 1°C para evitar oscilação

### Alertas Automáticos

| Condição | Severidade |
|----------|------------|
| Temp > setpoint + 5°C | Crítico |
| Temp > setpoint + 2°C | Aviso |
| Sensor offline > 5 min | Aviso |
| Falha comando AC | Aviso |

## 🔧 Tarefas Agendadas (Celery)

- `check_sensor_status`: A cada 1 minuto
- `cleanup_old_readings`: Diariamente
- `aggregate_readings`: A cada hora

## 📄 Licença

Este projeto está licenciado sob a MIT License.

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request
