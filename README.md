# APPSPEC Frontend

**APPSPEC** (Apoio ao Diagnóstico de Apendicite) é uma aplicação web educacional que dá suporte ao diagnóstico de apendicite, comparando três métodos lado a lado: **Escore de Alvarado**, **KNN** e **SVM**.

Projeto da disciplina *Construção de APIs para Inteligência Artificial* da **UFG**.

> ⚠️ **Aviso:** Sistema exclusivamente didático — **NÃO** substitui avaliação médica presencial.

## Arquitetura

```
Browser ──HTML/SSR──> appsec-frontend (FastAPI, porta 3000) ──HTTP──> appsec-backend (porta 8082)
```

O frontend atua como um **BFF (Backend-for-Frontend)**: renderiza HTML no servidor (SSR) com Jinja2 e faz proxy de todas as requisições para o backend via `httpx`. O JWT é armazenado em cookie HTTP-only, nunca exposto ao cliente.

## Stack

| Tecnologia | Versão | Uso |
|---|---|---|
| Python | 3.12+ | Runtime |
| FastAPI | >=0.115.0 | Framework web ASGI |
| Uvicorn | >=0.34.0 | Servidor ASGI |
| Jinja2 | >=3.1.0 | Templates HTML |
| httpx | >=0.27.0 | Cliente HTTP assíncrono |
| python-jose | >=3.3 | Decodificação JWT |
| Bootstrap 5 | 5.3.2 | CSS via CDN |
| marked.js | latest | Markdown no chat via CDN |
| Ruff | — | Linter e formatador |

## Pré-requisitos

- Python 3.12+
- Backend do APPSPEC rodando em `http://localhost:8082`

## Instalação

```bash
# Clonar o repositório
git clone <repo-url>
cd appsec-frontend

# Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar
python -m app.main
```

A aplicação iniciará em `http://localhost:3000`.

## Configuração

Todas as configurações são feitas por variáveis de ambiente:

| Variável | Padrão | Descrição |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8082` | URL do backend |
| `SECRET_KEY` | `appsec-dev-secret-key-nao-use-em-producao` | Chave para decodificar JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Tempo de expiração do token |
| `CORS_ORIGINS` | `http://localhost:3000,http://127.0.0.1:3000` | Origens permitidas (separadas por vírgula) |

## Autenticação e Papéis

O login é feito via formulário em `/auth/login-web`. O JWT retornado é armazenado em cookie HTTP-only.

**Papéis:**

| Papel | Acesso |
|---|---|
| `admin` | Avaliar paciente, ver histórico, remover registros, ver métricas |
| `professional` | Avaliar paciente, ver histórico, remover registros, ver métricas |
| `viewer` | Ver histórico e métricas (somente leitura) |

Usuário padrão: `admin` / `admin123`

## Rotas

### Páginas Web

| Método | Rota | Descrição | Auth |
|---|---|---|---|
| GET | `/` | Redireciona para `/diagnosticos/` | — |
| GET | `/auth/login-page` | Formulário de login | — |
| POST | `/auth/login-web` | Autentica e define cookie JWT | — |
| POST | `/auth/logout` | Remove cookie JWT | Sim |
| GET | `/diagnosticos/` | Formulário clínico (Escore de Alvarado) | Sim |
| POST | `/diagnosticos/avaliar` | Envia dados e mostra resultado 3-modelos | admin, professional |
| GET | `/diagnosticos/historico` | Histórico com filtros | Sim |
| DELETE | `/diagnosticos/{id}` | Remove um diagnóstico | admin, professional |
| GET | `/metricas/` | Dashboard de métricas dos modelos | Sim |
| GET | `/duvidas/` | Chat de dúvidas | Sim |
| POST | `/duvidas/enviar` | Envia pergunta ao backend LLM | Sim |
| GET | `/backend-docs` | Redireciona para `/docs` do backend | — |

### Formulário Clínico

O formulário coleta os 8 critérios do Escore de Alvarado (1986):

**Sintomas (S):**
- Dor migratória para FID
- Anorexia (perda de apetite)
- Náuseas ou vômitos
- Dor à palpação em FID

**Sinais (S):**
- Descompressão dolorosa (Blumberg)
- Temperatura axilar (> 37,3 °C = 1 ponto)
- Leucócitos (> 10.000/mm³ = 2 pontos)
- Neutrofilia (desvio à esquerda)

### Resultado

A página de resultado compara os três métodos:
- **Alvarado Score:** pontuação de 0 a 10 com interpretação clínica e conduta sugerida
- **KNN:** probabilidade, classe predita, confiança, distância média aos vizinhos
- **SVM:** probabilidade, classe predita, confiança, parâmetros do kernel

### Histórico

Tabela com filtros por data, classificação Alvarado, e predição de cada modelo. Usuários admin/professional podem remover registros.

### Métricas

Dashboard com:
- Acurácia, sensibilidade, especificidade, VPP, VPN para cada modelo
- Curvas ROC e Precision-Recall (AUC e Average Precision)
- Matrizes de confusão
- Gráficos comparativos (imagens estáticas)

### Chat de Dúvidas

Interface no estilo WhatsApp que envia perguntas para um LLM via backend. Usa `marked.js` para renderizar respostas em Markdown.

## Estrutura do Projeto

```
appsec-frontend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configurações via env vars
│   ├── main.py                # App FastAPI, middlewares, error handlers
│   ├── routers/
│   │   ├── auth.py            # Login/logout
│   │   ├── diagnostico.py     # Formulário, avaliação, histórico
│   │   ├── duvidas.py         # Chat de dúvidas
│   │   └── metricas.py        # Dashboard de métricas
│   └── templates/
│       ├── base.html          # Layout principal (navbar, footer, disclaimer)
│       ├── login.html         # Formulário de login
│       ├── index.html         # Formulário clínico
│       ├── resultado.html     # Comparação 3-modelos
│       ├── historico.html     # Tabela de histórico
│       ├── metricas.html      # Dashboard de métricas
│       ├── duvidas.html       # Chat de dúvidas
│       └── 403.html           # Página de acesso negado
├── static/diagnostico/img/    # Imagens (matrizes confusão, curvas ROC/PR)
├── requirements.txt           # Dependências Python
└── .github/workflows/ci.yml   # CI: ruff lint + verificação de imports
```

## CI

O pipeline do GitHub Actions executa:
1. **Lint:** `ruff check` + `ruff format --check`
2. **Test:** instala dependências e valida `from app.main import app`

## Dataset

Os modelos ML (KNN e SVM) foram treinados no dataset **Regensburg Pediatric Appendicitis** (UCI ID 938, Marcinkevics et al., 2023).
