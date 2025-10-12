# Política de 2 Etapas (Clarify → Final)

Este backend implementa uma dinâmica de duas etapas no chatbot:

- Etapa A (início): ao receber a primeira mensagem do usuário (U0), o agente faz RAG, não responde ainda e retorna exatamente 3 perguntas de esclarecimento em um único bloco:

  ```
  <clarify>
  Q1: ...
  Q2: ...
  Q3: ...
  ```

- Etapa B (fechamento): quando o usuário responder (U1), o agente faz novo RAG com base em {U0, Q1–Q3, U1} e entrega a resposta final (sem novas perguntas).

- Se o usuário ignorar as perguntas e mudar de assunto, o agente recomeça uma nova Etapa A (heurística simples baseada em sobreposição de termos).

## Endpoints

### 1) Conversas (stateful)

`POST /api/v1/conversations/{conversation_id}/messages`

- Primeira mensagem `role=user` → retorna `<clarify>` com Q1–Q3.
- Próxima mensagem `role=user` → retorna resposta final.
- Se mudar de assunto entre as etapas, volta a `<clarify>`.

Exemplo (curl):

```bash
# Etapa A
curl -s -X POST \
  -H "X-Guest-Id: $GUEST_ID" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"Minha conta foi negativada indevidamente."}' \
  http://localhost:8000/api/v1/conversations/$CONV_ID/messages | jq

# Etapa B (responde às Q1–Q3 livres)
curl -s -X POST \
  -H "X-Guest-Id: $GUEST_ID" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"SP. Quero limpar o nome. Tenho comprovantes."}' \
  http://localhost:8000/api/v1/conversations/$CONV_ID/messages | jq
```

### 2) Chat stateless (com thread local)

`POST /api/v1/chat`

Suporta a mesma política de 2 etapas usando `conversation_id` para manter o fio local em memória (não persistente; apenas para uso rápido):

```bash
# Etapa A → retorna <clarify>
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_message":"Comprei um produto com defeito","conversation_id":"thread-123"}' \
  http://localhost:8000/api/v1/chat | jq

# Etapa B → resposta final
curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"user_message":"SP. Quero trocar. Produto durável, 20 dias de uso.","conversation_id":"thread-123"}' \
  http://localhost:8000/api/v1/chat | jq
```

### Base de conhecimento (KB)

- A KB �� carregada automaticamente a partir do primeiro diret��rio existente na ordem: `backend-fastapi/know_base`, `backend-fastapi/kb`, `./know_base`, `./kb`. Se `KB_DIR` estiver definida, tem prioridade sobre todos.
- O reposit��rio inclui `backend-fastapi/know_base` com 3 leis estruturadas e priorizadas no RAG: Lei 7.716/1989, Lei 12.288/2010 e Lei 14.532/2023. Quando presentes, elas s��o sempre consideradas nos documentos enviados ao modelo, al��m do top‑k por palavras‑chave.

Notas:
- O estado do `/chat` é temporário (processo em memória) e pode se perder em reinícios. Para produção e histórico robusto, use as rotas de conversas.
- O agente continua usando RAG local e Cohere (Command‑R+). Configure `COHERE_API_KEY` e, opcionalmente, `KB_DIR` para sua base.

