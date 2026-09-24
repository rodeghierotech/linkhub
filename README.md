# LinkShort V2

Plataforma local de gerenciamento de links construída com FastAPI, SQLAlchemy, SQLite e templates Jinja2. A V2 mantém o redirecionamento simples da V1 e adiciona contas, propriedade dos links e analytics detalhados.

## Funcionalidades

- Cadastro, login e logout com sessão assinada.
- Senhas protegidas com Argon2.
- Links isolados por usuário e rotas privadas protegidas.
- Alias automático ou personalizado (`/r/portfolio`).
- Ativação, desativação, cópia, analytics e exclusão de links.
- Um registro por clique, sem armazenamento de endereço IP.
- Navegador, sistema operacional, dispositivo e origem do acesso.
- Dashboard com totais, últimos sete dias, link principal e gráfico diário.
- Página individual com métricas por link.
- Proteção CSRF em ações POST e autorização por proprietário.
- Migração incremental do banco V1.

## Arquitetura

```text
app/
├── main.py                 # app factory, sessão e montagem das rotas
├── auth/                   # cadastro, login, sessão e usuários
├── links/                  # criação, autorização e redirecionamento
├── analytics/              # agregações SQL e dados para gráficos
├── database/               # engine, sessão e modelos ORM
├── templates/              # páginas Jinja2
├── static/                 # CSS e JavaScript
└── utils/                  # CSRF, aliases e User-Agent
migrations/                 # migrations Alembic
tests/                      # testes de integração e migração
```

Fluxo principal: `router → service → repository → SQLAlchemy`.

## Banco de dados

### `users`

Conta local com nome, e-mail único, hash da senha e data de criação.

### `links`

URL original, alias único, proprietário, status e data de criação. O campo `legacy_click_count` preserva apenas o total acumulado pela V1.

### `clicks`

Um registro por acesso com data, referrer, categoria da origem, User-Agent, navegador, sistema operacional e dispositivo. Nenhum IP é coletado.

Os links importados da V1 ficam temporariamente sem proprietário e são associados automaticamente ao primeiro usuário cadastrado. Como os cliques antigos não tinham data ou User-Agent, eles entram no total histórico, mas não são inventados nos gráficos e distribuições.

## Instalação

Requer Python 3.11 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Configuração

As variáveis são opcionais para execução local:

| Variável | Padrão | Uso |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./linkshort.db` | Conexão SQLAlchemy |
| `SESSION_SECRET` | valor local de desenvolvimento | Assinatura do cookie; defina um segredo forte fora do ambiente local |
| `COOKIE_SECURE` | `false` | Use `true` quando a aplicação estiver sob HTTPS |

Exemplo para a sessão atual do PowerShell:

```powershell
$env:SESSION_SECRET = "troque-por-um-segredo-longo-e-aleatorio"
```

## Migração

Para atualizar um banco V1 existente sem apagar os dados:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

A aplicação também executa migrations pendentes ao iniciar. Ainda assim, mantenha backup do arquivo SQLite antes de migrations em dados importantes.
Downgrade automático para a V1 não é oferecido porque removeria o histórico detalhado da V2; para voltar, restaure o backup criado antes da migration.

## Execução

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --host 127.0.0.1 --port 8000
```

Acesse [http://127.0.0.1:8000](http://127.0.0.1:8000). O primeiro cadastro assume automaticamente os links migrados da V1.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

A suíte cobre migração da V1, cadastro, login, sessão, criação de link, alias duplicado e inválido, redirecionamento, registro de clique, link ausente ou inativo, isolamento entre usuários e agregações de analytics.

## Segurança

- Hash Argon2 por meio de `pwdlib`.
- Cookie HTTP-only, SameSite=Lax e opção Secure por variável de ambiente.
- Token CSRF por sessão em todos os formulários que alteram dados.
- Consultas privadas sempre filtradas pelo `user_id` autenticado.
- URLs validadas por `pydantic.HttpUrl` e aliases por lista segura.
- Templates `.html` usam o autoescape do Jinja2.
- ORM SQLAlchemy com parâmetros, sem SQL concatenado.
- Nenhum endereço IP é persistido.

## Escopo

A V2 permanece local e síncrona. Redis, filas, geolocalização, domínio personalizado, pagamentos, equipes, API pública, QR Code, OAuth e outros recursos avançados continuam fora do escopo.
