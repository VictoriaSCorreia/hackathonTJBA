# Backend FastAPI – Modo Convidado

Este backend foi simplificado para operar com usuários convidados. Agora a API cria e identifica usuários apenas por um `guest_id` único (UUID), sem campos de e‑mail ou nome completo.

## O que mudou
- Modelo `User`:
  - Removidos: `email`, `full_name`.
  - Adicionado: `guest_id: str` (único e indexado).
- Schemas:
  - `UserBase` e `UserRead` expõem `guest_id` e `id`.
  - `UserCreate` removido (não é mais necessário).
- Serviço (`UserService`):
  - `create_guest()` cria um usuário com `guest_id` (UUID v4).
  - `get_by_guest_id(guest_id)` recupera usuário por `guest_id`.
- Dependências (`app/api/deps.py`):
  - `get_current_guest` identifica usuário a partir do header `X-Guest-Id` ou cookie `guest_id`.
- Rotas (v1):
  - `POST /api/v1/sessions` cria um novo convidado.
  - `GET /api/v1/me` retorna o convidado atual (requer `guest_id` em header/cookie).
  - Rotas antigas de `POST /users` e `GET /users/{id}` foram removidas/substituídas.

## Como rodar

Pré‑requisitos: Docker e Docker Compose instalados.

1) Subir serviços
```bash
make up
```

2) Aplicar migrações do banco
```bash
make migrate
```

3) Acessar documentação interativa
```
http://localhost:8000/docs
```

Observação: Se desejar gerar novas migrações automáticas com base nas models, use:
```bash
make revision
```

## Variáveis de ambiente
- `DATABASE_URL` já está configurada no `docker-compose.yml` para um Postgres local no serviço `db`.

## Endpoints

- Criar sessão de convidado
  - `POST /api/v1/sessions`
  - Resposta 201
    ```json
    {
      "id": 1,
      "guest_id": "2c5d8b3e-6e3f-47f1-9b2f-2a5d2a1a9cdd"
    }
    ```

- Obter usuário atual (requer identificação de convidado)
  - `GET /api/v1/me`
  - Envie o `guest_id` em um dos canais:
    - Header: `X-Guest-Id: <guest_id>`
    - ou Cookie: `guest_id=<guest_id>`
  - Resposta 200
    ```json
    {
      "id": 1,
      "guest_id": "2c5d8b3e-6e3f-47f1-9b2f-2a5d2a1a9cdd"
    }
    ```

- Healthcheck
  - `GET /api/v1/health`
  - Resposta 200
    ```json
    { "status": "ok" }
    ```

## Testando rápido via curl

1) Criar um convidado
```bash
curl -s -X POST http://localhost:8000/api/v1/sessions | jq
```

2) Usar o `guest_id` retornado para acessar `/me`
```bash
GUEST_ID="<cole-o-guest_id-aqui>"
curl -s -H "X-Guest-Id: $GUEST_ID" http://localhost:8000/api/v1/me | jq
```

Ou usando cookie:
```bash
curl -s --cookie "guest_id=$GUEST_ID" http://localhost:8000/api/v1/me | jq
```

## Estrutura relevante
- `app/models/user.py`: definição do modelo `User` com `guest_id`.
- `app/schemas/user.py`: schemas Pydantic (`UserRead`).
- `app/services/user_service.py`: criação e busca por `guest_id`.
- `app/api/deps.py`: `get_current_guest` por header/cookie.
- `app/api/v1/routes/users.py`: rotas `POST /sessions` e `GET /me`.
- `alembic/versions/0001_guest_user.py`: migração inicial da tabela `users`.

## Solução de problemas
- Falha ao construir imagem por `apt-get update` (HTTP 403):
  - Tente novamente o `docker compose build api` após alguns minutos (intermitência do mirror).
  - Opcionalmente troque mirrors Debian no `Dockerfile` se persistir.

## Agente Jurídico (Chat)

- `POST /api/v1/chat`
  - Body:
    ```json
    { "user_message": "Comprei um produto com defeito, o que faço?", "conversation_id": "opcional" }
    ```
  - Resposta 200:
    ```json
    {
      "response_text": "...resposta do agente...",
      "citations": [ { "title": "...", "url": "..." } ],
      "conversation_id": "local-thread"
    }
    ```
  - Exemplo curl:
    ```bash
    curl -s -X POST \
      -H "Content-Type: application/json" \
      -d '{"user_message":"Comprei um produto com defeito, o que faço?"}' \
      http://localhost:8000/api/v1/chat | jq
    ```

### Configuração
- Defina `COHERE_API_KEY` no ambiente do serviço `api`.
- Opcional: `KB_DIR` (padrão `./kb`), diretório com arquivos `.json`.

Formato esperado dos arquivos JSON (lista ou objeto único):
```json
{
  "title": "Como ingressar com ação de alimentos",
  "content": "Passos, documentos necessários, prazos...",
  "url": "https://exemplo.gov.br/guia-alimentos",
  "jurisdiction": "BR",
  "updated_at": "2025-07-15",
  "tags": ["família", "alimentos", "processo"]
}
```

Observações:
- O agente usa RAG local por palavras-chave (simples) para selecionar trechos relevantes da KB e envia para o modelo da Cohere (Command-R+).
- Se `KB_DIR` estiver vazio, uma KB mínima de fallback é usada.
- As respostas são meramente informativas e não substituem aconselhamento jurídico profissional.

## Conversas (planejados)

Agora implementados para orquestrar threads de conversa do chat.

- Criar conversa
  - `POST /api/v1/conversations`
  - Requer convidado atual: envie `X-Guest-Id: <guest_id>`
  - Body (opcional):
    ```json
    { "title": "Atendimento consumidor" }
    ```
  - Resposta 201:
    ```json
    { "id": 1, "guest_id": "<guest>", "title": "Atendimento consumidor", "created_at": "..." }
    ```

- Enviar mensagem numa conversa (dispara resposta do agente quando `role=user`)
  - `POST /api/v1/conversations/{conversation_id}/messages`
  - Requer convidado atual: envie `X-Guest-Id: <guest_id>`
  - Body:
    ```json
    { "role": "user", "content": "Minha conta foi negativada indevidamente." }
    ```
  - Resposta 200 (retorna a mensagem gravada; se `role=user`, a resposta será a do `assistant`):
    ```json
    { "id": 10, "conversation_id": 1, "role": "assistant", "content": "...resposta...", "created_at": "..." }
    ```

- Listar conversas
  - `GET /api/v1/conversations`
  - Requer convidado atual: envie `X-Guest-Id: <guest_id>`

- Obter detalhes de uma conversa (inclui histórico)
  - `GET /api/v1/conversations/{conversation_id}`
  - Requer convidado atual: envie `X-Guest-Id: <guest_id>`

Observação: o endpoint `/api/v1/chat` continua disponível para uso stateless; para experiências com histórico, prefira as rotas de conversas.
