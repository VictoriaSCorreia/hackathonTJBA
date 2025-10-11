# Conversas e Mensagens — Endpoints

Guia conciso para criar conversas e enviar mensagens no backend.

- Base URL: `http://localhost:8000/api/v1`
- Autenticação convidado: envie `X-Guest-Id: <guest_id>` ou cookie `guest_id=<guest_id>`
- Obtenha um convidado: `POST /api/v1/sessions`

## 1) Criar conversa
- `POST /conversations`
- Body: opcional (pode omitir totalmente) ou enviar `{}`; para título opcional:
  ```json
  { "title": "Atendimento consumidor" }
  ```
- Exemplos:
  - Sem body:
    ```bash
    GUEST_ID="<seu-guest-id>"
    curl -s -X POST \
      -H "X-Guest-Id: $GUEST_ID" \
      http://localhost:8000/api/v1/conversations | jq
    ```
  - Com título:
    ```bash
    curl -s -X POST \
      -H "X-Guest-Id: $GUEST_ID" \
      -H "Content-Type: application/json" \
      -d '{"title":"Atendimento consumidor"}' \
      http://localhost:8000/api/v1/conversations | jq
    ```

## 2) Enviar mensagem na conversa
- `POST /conversations/{conversation_id}/messages`
- Body:
  ```json
  { "role": "user", "content": "Minha conta foi negativada indevidamente." }
  ```
- Comportamento:
  - Quando `role="user"`, o backend chama o agente, salva a sua pergunta e a resposta, e RETORNA a mensagem do `assistant`.
  - Para `role="assistant"`, apenas grava a mensagem e retorna a própria mensagem gravada.
- Exemplo (`role=user`):
  ```bash
  CONV_ID=1
  curl -s -X POST \
    -H "X-Guest-Id: $GUEST_ID" \
    -H "Content-Type: application/json" \
    -d '{"role":"user","content":"Minha conta foi negativada indevidamente."}' \
    http://localhost:8000/api/v1/conversations/$CONV_ID/messages | jq
  ```

## 3) Listar conversas do convidado
- `GET /conversations`
- Exemplo:
  ```bash
  curl -s -H "X-Guest-Id: $GUEST_ID" \
    http://localhost:8000/api/v1/conversations | jq
  ```

## 4) Obter conversa com histórico
- `GET /conversations/{conversation_id}`
- Resposta: objeto com `conversation` e `messages` (ordenadas por criação ascendente).
- Exemplo:
  ```bash
  curl -s -H "X-Guest-Id: $GUEST_ID" \
    http://localhost:8000/api/v1/conversations/$CONV_ID | jq
  ```

## Observações
- Endpoints implementados em: `backend-fastapi/app/api/v1/routes/conversations.py`
- Serviço de persistência: `backend-fastapi/app/services/conversation_service.py`
- Modelos: `backend-fastapi/app/models/conversation.py`
- Para chat sem histórico, há também `POST /api/v1/chat` (stateless).
