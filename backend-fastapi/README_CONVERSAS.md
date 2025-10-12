# Conversas e Mensagens — Endpoints

Guia conciso para criar conversas e enviar mensagens no backend.

### Base de conhecimento (KB)

- A KB �� carregada automaticamente a partir do primeiro diret��rio existente na ordem: `backend-fastapi/know_base`, `backend-fastapi/kb`, `./know_base`, `./kb`.
- Se `KB_DIR` estiver definida no ambiente do servi��o, ela tem prioridade sobre os caminhos acima.
- O reposit��rio inclui `backend-fastapi/know_base` com 3 leis estruturadas (Lei 7.716/1989, Lei 12.288/2010 e Lei 14.532/2023) que s��o priorizadas no RAG e sempre consideradas junto com os top‑k documentos por palavras‑chave.

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
- Comportamento (política de 2 etapas):
  - Etapa A (início): ao receber `role="user"`, o agente faz RAG, NÃO responde ainda e retorna exatamente 3 perguntas curtas de esclarecimento em um único bloco:

    ```
    <clarify>
    Q1: ...
    Q2: ...
    Q3: ...
    ```

  - Etapa B (fechamento): quando o usuário responder (novo `role="user"` em seguida), o agente faz novo RAG com base em {U0, Q1–Q3, U1} e entrega a resposta final (sem novas perguntas).

  - Se o usuário ignorar as perguntas e mudar de assunto, o agente recomeça uma nova Etapa A.

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
- Para chat sem histórico, há também `POST /api/v1/chat` (stateless) com a mesma política de 2 etapas — veja `backend-fastapi/README_TWO_STEPS.md`.

