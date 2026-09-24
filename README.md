# Encurtador de Links

Aplicação web para cadastrar URLs longas, gerar links curtos únicos, redirecionar e contabilizar cliques.

## Objetivo

- Cadastrar uma URL longa e gerar um código curto único.
- Acessar `/r/{codigo}` e ser redirecionado para a URL original.
- Contabilizar cada acesso (clique).
- Visualizar todos os links e a quantidade de cliques de cada um em um dashboard.
- Excluir links.

## Tecnologias

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- SQLite
- Pydantic v2
- Jinja2 (templates server-side)
- HTML/CSS/JS puro

## Estrutura

```text
app/
├── main.py                # criação da app FastAPI, montagem de rotas e static
├── database/
│   ├── database.py        # engine, sessão e dependency get_db
│   └── models.py          # modelo ORM Link
├── links/
│   ├── router.py          # rotas HTTP (dashboard, criar, redirecionar, excluir)
│   ├── service.py         # regras de negócio (geração de código, validações)
│   ├── repository.py      # acesso ao banco de dados
│   └── schemas.py         # schemas Pydantic (LinkCreate, LinkRead, DashboardStats)
├── templates/
│   ├── base.html
│   └── dashboard.html
└── static/
    ├── css/style.css
    └── js/app.js
requirements.txt
README.md
```

## Instalação

Criar ambiente virtual:

```bash
python -m venv .venv
```

Ativar:

- Windows: `.venv\Scripts\activate`
- Linux/Mac: `source .venv/bin/activate`

Instalar dependências:

```bash
pip install -r requirements.txt
```

## Execução

```bash
uvicorn app.main:app --reload
```

Acesse: http://127.0.0.1:8000

O banco SQLite (`linkshort.db`) é criado automaticamente na primeira execução.

## Exemplo de uso

1. Abra `http://127.0.0.1:8000`.
2. Cole uma URL, ex: `https://meusite.com/produtos/promocao?id=123`.
3. Clique em "Encurtar" — o link aparece na tabela como `http://127.0.0.1:8000/r/a8K3xP`.
4. Acesse o link curto: você é redirecionado para a URL original e o clique é contabilizado.
5. Use "Copiar" para copiar a URL curta, "Abrir" para testar o redirecionamento, ou "Excluir" para remover o link.

## Decisões técnicas

- **Código curto**: 6 caracteres alfanuméricos gerados com `secrets.choice` (`app/utils/short_code.py`), com verificação de unicidade antes de persistir.
- **Validação de URL**: `pydantic.HttpUrl` via `TypeAdapter`, exigindo esquema (`http://`/`https://`) e host válido.
- **Camadas**: `router` (HTTP) → `service` (regras de negócio) → `repository` (acesso a dados), evitando lógica de negócio nas rotas.
- **Banco síncrono**: SQLAlchemy 2.0 em modo síncrono (suficiente para SQLite/V1; simplifica manutenção).
- **Sem autenticação/QR Code/expiração/etc.**: fora de escopo desta V1, conforme especificado.

## Escopo não implementado (V1)

Autenticação, contas de usuário, Redis, filas, geolocalização, análise de navegador, QR Code, senha em links, expiração, domínio personalizado, planos/pagamentos — previstos para versões futuras.
